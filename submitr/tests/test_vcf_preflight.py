import gzip
from pathlib import Path
import struct
import zlib
from unittest import mock

import pytest

from submitr.file_for_upload import FileForUpload, FilesForUpload
from submitr.file_preflight import validate_vcf


VCF_FIXTURE_DIR = Path(__file__).parent / "data" / "vcf"


def _fixture(name):
    return VCF_FIXTURE_DIR / name


def _bgzf(data):
    """Make a small BGZF stream from bytes using the public block layout."""

    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(data) + compressor.flush()
    block_size = 18 + len(compressed) + 8
    header = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff"
    extra = b"\x06\x00BC\x02\x00" + struct.pack("<H", block_size - 1)
    trailer = struct.pack("<II", zlib.crc32(data) & 0xffffffff, len(data))
    eof = bytes.fromhex("1f8b08040000000000ff0600424302001b000300000000000000000000")
    return header + extra + compressed + trailer + eof


@pytest.mark.parametrize("fixture", ["valid_plain.vcf", "valid_samples.vcf", "captain_valid_header.vcf"])
def test_valid_vcf_fixtures_pass(fixture):
    result = validate_vcf(_fixture(fixture))

    assert result.ok is True
    assert result.requires_confirmation is False
    assert not result.structural_findings
    assert not result.advisory_findings
    assert result.records_checked > 0


def test_valid_gzip_and_bgzf_streams_pass(tmp_path):
    content = _fixture("valid_plain.vcf").read_bytes()
    gzip_path = tmp_path / "valid.vcf.gz"
    with gzip.open(gzip_path, "wb") as compressed:
        compressed.write(content)
    bgzf_path = tmp_path / "valid-bgzf.vcf.gz"
    bgzf_path.write_bytes(_bgzf(content))

    assert validate_vcf(gzip_path).ok is True
    assert validate_vcf(bgzf_path).ok is True


@pytest.mark.parametrize("corruptor", [lambda data: data[:-5], lambda data: data[:-1] + bytes([data[-1] ^ 1])])
def test_compressed_corruption_blocks_upload(tmp_path, corruptor):
    content = _fixture("valid_plain.vcf").read_bytes()
    valid_path = tmp_path / "valid.vcf.gz"
    with gzip.open(valid_path, "wb") as compressed:
        compressed.write(content)
    corrupt_path = tmp_path / "corrupt.vcf.gz"
    corrupt_path.write_bytes(corruptor(valid_path.read_bytes()))

    result = validate_vcf(corrupt_path)

    assert result.ok is False
    assert any(finding.stage == "compression" for finding in result.structural_findings)


def test_non_gzip_named_vcf_gz_blocks_upload(tmp_path):
    path = tmp_path / "download.vcf.gz"
    path.write_bytes(b"<html>download failed</html>\n")

    result = validate_vcf(path)

    assert result.ok is False
    assert result.structural_findings[0].stage == "compression"
    assert "gzip" in str(result.structural_findings[0]).lower()


@pytest.mark.parametrize("fixture", ["missing_column_header.vcf", "malformed_record.vcf"])
def test_required_schema_and_record_shape_are_structural(fixture):
    result = validate_vcf(_fixture(fixture))

    assert result.ok is False
    assert result.structural_findings
    assert all(finding.severity == "error" for finding in result.structural_findings)


def test_invalid_utf8_is_reported_with_record_line_context(tmp_path):
    path = tmp_path / "invalid-utf8.vcf"
    path.write_bytes(_fixture("valid_plain.vcf").read_bytes().replace(b"chr3", b"chr\xff"))

    result = validate_vcf(path)

    assert result.ok is False
    assert any(finding.line_number == 7 and "UTF-8" in finding.message for finding in result.structural_findings)


def test_sample_format_values_cannot_exceed_declared_keys(tmp_path):
    path = tmp_path / "too-many-sample-values.vcf"
    path.write_bytes(_fixture("valid_samples.vcf").read_bytes().replace(b"0/1:8", b"0/1:8:extra"))

    result = validate_vcf(path)

    assert result.ok is False
    assert "more fields" in str(result.structural_findings[0])


def test_crlf_is_accepted_with_an_advisory(tmp_path):
    path = tmp_path / "windows.vcf"
    path.write_bytes(_fixture("valid_plain.vcf").read_bytes().replace(b"\n", b"\r\n"))

    result = validate_vcf(path)

    assert result.ok is True
    assert result.requires_confirmation is True
    assert any("line terminators" in finding.message for finding in result.advisory_findings)


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("advisory_one_hash.vcf", "one #"),
        ("advisory_info_colon.vcf", "key:value"),
        ("advisory_continuation.vcf", "no key"),
    ],
)
def test_captain_header_advisories_are_non_blocking(fixture, message):
    result = validate_vcf(_fixture(fixture))

    assert result.ok is True
    assert result.requires_confirmation is True
    assert any(message in finding.message for finding in result.advisory_findings)


def test_captain_combined_header_fixture_has_all_three_advisories():
    result = validate_vcf(_fixture("captain_advisory_headers.vcf"))

    assert result.ok is True
    assert len(result.advisory_findings) == 3
    assert result.requires_confirmation is True


def test_colons_inside_quoted_info_descriptions_are_not_advisories(tmp_path):
    path = tmp_path / "quoted-info.vcf"
    content = _fixture("valid_plain.vcf").read_bytes().replace(
        b'Description="Read depth"', b'Description="depth: before,depth: after"'
    )
    path.write_bytes(content)

    result = validate_vcf(path)

    assert result.ok is True
    assert not result.advisory_findings


def test_record_errors_are_bounded(tmp_path):
    content = _fixture("malformed_record.vcf").read_bytes()
    path = tmp_path / "many-errors.vcf"
    header = content.split(b"#CHROM", 1)[0] + b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    bad_record = b"chr1\tbad\t.\tA\tC\t.\tPASS\n"
    path.write_bytes(header + bad_record * 40)

    result = validate_vcf(path, max_errors=3)

    assert len(result.structural_findings) == 3
    assert result.errors_truncated is True


def test_decompressed_byte_limit_is_structural(tmp_path):
    path = tmp_path / "limited.vcf"
    path.write_bytes(_fixture("valid_plain.vcf").read_bytes())

    result = validate_vcf(path, max_uncompressed_bytes=10)

    assert result.ok is False
    assert result.structural_findings[0].stage == "input"
    assert "limit" in result.structural_findings[0].message


@pytest.mark.parametrize("answer", [True, False])
def test_review_requires_confirmation_for_advisory_headers(tmp_path, answer):
    source = _fixture("captain_advisory_headers.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no", return_value=answer) as confirm:
        reviewed = FilesForUpload.review([file_for_upload], printf=output.append)

    assert reviewed is answer
    assert file_for_upload.ignore is (not answer)
    assert confirm.call_count == 1
    assert any("compatibility findings" in line for line in output)


def test_review_hard_blocks_structural_vcf_without_prompt(tmp_path):
    source = _fixture("malformed_record.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no") as confirm:
        reviewed = FilesForUpload.review([file_for_upload], printf=output.append)

    assert reviewed is False
    assert file_for_upload.ignore is True
    confirm.assert_not_called()
    assert any("Upload is blocked" in line for line in output)


def test_variant_calls_type_runs_preflight_even_without_vcf_suffix(tmp_path):
    path = tmp_path / "calls.data"
    path.write_bytes(_fixture("valid_plain.vcf").read_bytes())
    file_for_upload = FileForUpload(
        {"file": path.name, "type": "VariantCalls"},
        main_search_directory=tmp_path,
    )

    assert file_for_upload.review(printf=lambda message: None) is True


def test_vcf_file_format_runs_preflight_even_without_vcf_suffix(tmp_path):
    path = tmp_path / "calls.data"
    path.write_bytes(_fixture("valid_plain.vcf").read_bytes())
    file_for_upload = FileForUpload(
        {"file": path.name, "file_format": "vcf"},
        main_search_directory=tmp_path,
    )

    assert file_for_upload.review(printf=lambda message: None) is True
