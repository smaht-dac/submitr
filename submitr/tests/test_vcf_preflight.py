import gzip
from pathlib import Path
import struct
import zlib
from unittest import mock

import pytest

from dcicutils.structured_data import StructuredDataSet

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


@pytest.mark.parametrize("encoding", ["plain", "gzip", "bgzf"])
def test_header_only_vcf_passes_all_stream_encodings(tmp_path, encoding):
    content = _fixture("header_only.vcf").read_bytes()
    path = tmp_path / f"header-only-{encoding}.vcf"
    if encoding == "plain":
        path.write_bytes(content)
    elif encoding == "gzip":
        path = path.with_suffix(".vcf.gz")
        with gzip.open(path, "wb") as compressed:
            compressed.write(content)
    else:
        path = path.with_suffix(".vcf.gz")
        path.write_bytes(_bgzf(content))

    result = validate_vcf(path)

    assert result.ok is True
    assert result.records_checked == 0
    assert not result.structural_findings


def test_empty_plain_payload_is_structural(tmp_path):
    path = tmp_path / "empty.vcf"
    path.write_bytes(b"")

    result = validate_vcf(path)

    assert result.ok is False
    assert any("file is empty" in finding.message for finding in result.structural_findings)


def test_truncated_empty_gzip_payload_is_structural(tmp_path):
    path = tmp_path / "truncated-empty.vcf.gz"
    with gzip.open(path, "wb") as compressed:
        compressed.write(b"")
    path.write_bytes(path.read_bytes()[:-1])

    result = validate_vcf(path)

    assert result.ok is False
    assert any(finding.stage == "compression" for finding in result.structural_findings)


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


def test_combined_advisory_and_structural_findings_remain_blocking():
    result = validate_vcf(_fixture("combined_advisory_malformed.vcf"))

    assert result.ok is False
    assert result.requires_confirmation is False
    assert len(result.advisory_findings) == 3
    assert sum(result.advisory_counts.values()) == 3
    assert result.structural_findings


def test_default_review_aggregates_many_header_advisories(tmp_path):
    source = _fixture("many_advisory_headers.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no", return_value=True) as confirm:
        reviewed = FilesForUpload.review([file_for_upload], printf=output.append)

    assert reviewed is True
    assert confirm.call_count == 1
    assert any("30 advisory findings detected" in line for line in output)
    assert any("30 metadata-like header lines use one #" in line for line in output)
    assert not any("line 2:" in line for line in output)


def test_verbose_review_includes_advisory_line_details(tmp_path):
    source = _fixture("captain_advisory_headers.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no", return_value=True):
        reviewed = FilesForUpload.review(
            [file_for_upload], verbose=True, printf=output.append
        )

    assert reviewed is True
    assert any("line 2:" in line and "one #" in line for line in output)
    assert any("line 3:" in line and "key:value" in line for line in output)
    assert any("line 4:" in line and "no key" in line for line in output)


def test_combined_review_surfaces_advisories_without_confirmation(tmp_path):
    source = _fixture("combined_advisory_malformed.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no") as confirm:
        reviewed = FilesForUpload.review([file_for_upload], printf=output.append)

    assert reviewed is False
    assert file_for_upload.ignore is True
    confirm.assert_not_called()
    assert any("Structural errors block upload" in line for line in output)
    assert any("Header compatibility findings were also detected (3 total)" in line for line in output)
    assert any("confirmation was not requested" in line for line in output)
    assert any("Upload is blocked" in line for line in output)


def test_review_only_advisory_output_explains_confirmation_requirement(tmp_path):
    source = _fixture("captain_advisory_headers.vcf")
    path = tmp_path / source.name
    path.write_bytes(source.read_bytes())
    file_for_upload = FileForUpload(path.name, main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.yes_or_no") as confirm:
        reviewed = FilesForUpload.review(
            [file_for_upload], review_only=True, printf=output.append
        )

    assert reviewed is False
    assert file_for_upload.ignore is True
    confirm.assert_not_called()
    assert any("Review-only mode" in line for line in output)
    assert any("would require explicit confirmation before upload" in line for line in output)


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


def _encoded(content, encoding):
    if encoding == "gzip":
        return gzip.compress(content)
    if encoding == "bgzf":
        return _bgzf(content)
    return content


@pytest.mark.parametrize("encoding", ["plain", "gzip", "bgzf"])
def test_missing_alt_dot_is_accepted_in_all_stream_encodings(tmp_path, encoding):
    path = tmp_path / "alt-missing.vcf"
    path.write_bytes(_encoded(_fixture("alt_missing.vcf").read_bytes(), encoding))

    result = validate_vcf(path, compressed=encoding != "plain")

    assert result.ok is True
    assert result.records_checked == 2


@pytest.mark.parametrize(
    ("ref", "alt"),
    [("A", "A,."), ("A", ".,A"), ("A", ".,."), ("A", ".."), ("A", ".A"), ("A", "A."), ("A", ""),
     ("A", "G]17:198982]"), (".", "C"), (".", ".")],
)
def test_dot_is_only_valid_as_the_entire_alt_field(tmp_path, ref, alt):
    path = tmp_path / "bad-dot.vcf"
    path.write_bytes(
        b"##fileformat=VCFv4.3\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        + f"chr1\t10\t.\t{ref}\t{alt}\t.\tPASS\t.\n".encode()
    )

    result = validate_vcf(path)

    assert result.ok is False
    assert result.records_checked == 0
    assert result.structural_findings[0].stage == "record"


@pytest.mark.parametrize(("name", "encoding"), [("alt-missing.vcf", "plain"), ("alt-missing.vcf.gz", "bgzf")])
def test_review_accepts_missing_alt_dot(tmp_path, name, encoding):
    (tmp_path / name).write_bytes(_encoded(_fixture("alt_missing.vcf").read_bytes(), encoding))
    file_for_upload = FileForUpload(name, main_search_directory=tmp_path)

    with mock.patch("submitr.file_for_upload.yes_or_no") as confirm:
        assert FilesForUpload.review([file_for_upload], printf=lambda message: None) is True

    assert file_for_upload.ignore is False
    confirm.assert_not_called()


# Files are VCF preflighted only as one of the two portal VCF formats, vcf (.vcf) and
# vcf_gz (.vcf.gz), identified by the declared file_format if any, else by file name.
VCF_FORMAT = "fcc2647d-301b-4888-8d9d-83ea4270309c"
VCF_GZ_FORMAT = {"@id": "/file-formats/vcf_gz/", "display_title": "vcf_gz",
                 "uuid": "1b8f525f-aecb-4211-9ae5-a2c998b05599"}


@pytest.mark.parametrize(
    ("name", "metadata", "encoding", "compressed"),
    [
        ("calls.vcf", {}, "plain", False),
        ("calls.vcf.gz", {}, "gzip", True),
        ("calls.vcf", {"file_format": "vcf"}, "plain", False),
        ("calls.vcf", {"file_format": "/FileFormat/vcf"}, "plain", False),
        ("calls.vcf", {"file_format": VCF_FORMAT}, "plain", False),
        ("calls.vcf", {"file_format": "/file-formats/vcf/", "type": "VariantCalls"}, "plain", False),
        ("calls.vcf.gz", {"file_format": "vcf_gz"}, "bgzf", True),
        ("CALLS.VCF.GZ", {"file_format": VCF_GZ_FORMAT, "type": "OutputFile"}, "gzip", True),
    ],
)
def test_portal_vcf_formats_run_preflight(tmp_path, name, metadata, encoding, compressed):
    (tmp_path / name).write_bytes(_encoded(_fixture("valid_plain.vcf").read_bytes(), encoding))
    file_for_upload = FileForUpload(dict(metadata, file=name), main_search_directory=tmp_path)

    with mock.patch("submitr.file_for_upload.validate_vcf", wraps=validate_vcf) as preflight:
        assert file_for_upload.review(printf=lambda message: None) is True

    assert preflight.call_args.kwargs["compressed"] is compressed


@pytest.mark.parametrize(
    ("name", "metadata", "content"),
    [
        ("calls.txt", {"type": "VariantCalls"}, b"not a vcf\n"),
        ("calls.bin", {"file_format": "variantcalls"}, b"\x00\x01"),
        ("calls.gvcf", {"file_format": "gvcf"}, b"not checked\n"),
        ("calls.gvcf.gz", {}, b"\x1f\x8bnot checked"),
        ("calls.vcf.gz.tbi", {}, b"not checked"),
        ("reads.fastq", {"type": "UnalignedReads"}, b"@r\nA\n+\nI\n"),
    ],
)
def test_other_formats_are_not_vcf_preflighted(tmp_path, name, metadata, content):
    (tmp_path / name).write_bytes(content)
    file_for_upload = FileForUpload(dict(metadata, file=name), main_search_directory=tmp_path)

    with mock.patch("submitr.file_for_upload.validate_vcf") as preflight:
        assert file_for_upload.review(printf=lambda message: None) is True

    preflight.assert_not_called()


@pytest.mark.parametrize(
    ("name", "metadata", "encoding", "message"),
    [
        ("calls.vcf.gz", {"file_format": "vcf"}, "gzip", "file_format vcf requires a file name ending in .vcf"),
        ("calls.vcf", {"file_format": VCF_GZ_FORMAT}, "plain",
         "file_format vcf_gz requires a file name ending in .vcf.gz"),
        ("calls.txt", {"file_format": "vcf", "type": "VariantCalls"}, "plain",
         "file_format vcf requires a file name ending in .vcf"),
        ("calls.vcf", {"file_format": "gvcf", "type": "OutputFile"}, "plain",
         "A .vcf file name requires file_format vcf, but the declared file_format is gvcf"),
        ("calls.vcf", {"file_format": "vcfgz"}, "plain",
         "A .vcf file name requires file_format vcf, but the declared file_format is vcfgz"),
        ("calls.vcf.gz", {"file_format": {"display_title": "fastq_gz"}}, "gzip",
         "A .vcf.gz file name requires file_format vcf_gz, but the declared file_format is fastq_gz"),
        ("calls.vcf", {}, "gzip", "A .vcf file must not be gzip/BGZF-compressed"),
        ("calls.vcf", {"file_format": "vcf"}, "bgzf", "A .vcf file must not be gzip/BGZF-compressed"),
        ("calls.vcf.gz", {}, "plain", "A .vcf.gz file must be gzip/BGZF-compressed"),
        ("calls.vcf.gz", {"file_format": "vcf_gz"}, "plain", "A .vcf.gz file must be gzip/BGZF-compressed"),
    ],
)
def test_vcf_format_mismatch_blocks_without_content_preflight(tmp_path, name, metadata, encoding, message):
    (tmp_path / name).write_bytes(_encoded(_fixture("valid_plain.vcf").read_bytes(), encoding))
    file_for_upload = FileForUpload(dict(metadata, file=name), main_search_directory=tmp_path)
    output = []

    with mock.patch("submitr.file_for_upload.validate_vcf") as preflight, \
            mock.patch("submitr.file_for_upload.yes_or_no") as confirm:
        reviewed = FilesForUpload.review([file_for_upload], printf=output.append)

    assert reviewed is False
    assert file_for_upload.ignore is True
    preflight.assert_not_called()
    confirm.assert_not_called()
    assert any("VCF file format mismatch" in line for line in output)
    assert any(message in line for line in output)
    assert any("Upload is blocked" in line for line in output)


def test_structured_data_upload_files_carry_declared_file_format(tmp_path):
    (tmp_path / "calls.vcf").write_bytes(_fixture("valid_plain.vcf").read_bytes())
    (tmp_path / "other.vcf").write_bytes(_fixture("valid_plain.vcf").read_bytes())
    structured_data = mock.MagicMock(spec=StructuredDataSet)
    structured_data.upload_files = [{"type": "VariantCalls", "file": "calls.vcf"},
                                    {"type": "VariantCalls", "file": "other.vcf"}]
    structured_data.data = {"VariantCalls": [{"filename": "other.vcf", "file_format": "vcf"},
                                             {"filename": "calls.vcf", "file_format": "vcf_gz"}]}
    output = []

    files_for_upload = FilesForUpload.assemble(structured_data, main_search_directory=tmp_path)
    with mock.patch("submitr.file_for_upload.validate_vcf", wraps=validate_vcf) as preflight:
        reviewed = FilesForUpload.review(files_for_upload, review_only=True, printf=output.append)

    assert [file.file_format for file in files_for_upload] == ["vcf_gz", "vcf"]
    assert reviewed is False
    assert [file.ignore for file in files_for_upload] == [True, False]
    assert preflight.call_count == 1
    assert any("file_format vcf_gz requires a file name ending in .vcf.gz" in line for line in output)
