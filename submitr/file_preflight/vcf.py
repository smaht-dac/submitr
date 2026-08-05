"""A bounded, pure-Python structural preflight for VCF files.

This module intentionally covers only stream integrity, required VCF header
shape, and record shape.  It does not inspect a reference genome or attempt
the broader semantic checks that belong in downstream QC.
"""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass, field
import gzip
import math
import os
from pathlib import Path
import re
import zlib
from typing import BinaryIO, Iterable, List, Optional, Tuple, Union


DEFAULT_MAX_ERRORS = 25
DEFAULT_MAX_LINE_BYTES = 16 * 1024 * 1024
DEFAULT_MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024
_MANDATORY_COLUMNS = ("#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO")
_IUPAC_BASES = frozenset("ACGTRYSWKMBDHVN")
_META_KEY_RE = re.compile(r"^##([A-Za-z][A-Za-z0-9_.-]*)\s*=\s*(.*)$")
_FILEFORMAT_RE = re.compile(r"^##fileformat=VCFv4\.(\d+)$")
_POS_RE = re.compile(r"^[1-9][0-9]*$")
_FILTER_TOKEN_RE = re.compile(r"^[^;\s]+$")
_SYMBOLIC_ALLELE_RE = re.compile(r"^<[A-Za-z][A-Za-z0-9_.:-]*>$")


@dataclass(frozen=True)
class VcfFinding:
    """One actionable structural error or advisory warning."""

    stage: str
    message: str
    line_number: Optional[int] = None
    severity: str = "error"

    @property
    def is_error(self) -> bool:
        return self.severity == "error"

    def __str__(self) -> str:
        location = f"line {self.line_number}: " if self.line_number is not None else ""
        return f"{self.stage}: {location}{self.message}"


@dataclass
class VcfPreflightResult:
    """The bounded result returned by :func:`validate_vcf`."""

    structural_findings: List[VcfFinding] = field(default_factory=list)
    advisory_findings: List[VcfFinding] = field(default_factory=list)
    version: Optional[str] = None
    records_checked: int = 0
    source_name: Optional[str] = None
    errors_truncated: bool = False

    @property
    def ok(self) -> bool:
        """Whether the file passed the non-overridable structural checks."""

        return not self.structural_findings

    @property
    def requires_confirmation(self) -> bool:
        """Whether advisory findings require an explicit upload confirmation."""

        return self.ok and bool(self.advisory_findings)

    @property
    def warnings(self) -> List[VcfFinding]:
        """Alias useful to callers that call advisory findings warnings."""

        return self.advisory_findings


class _FindingCollector:

    def __init__(self, result: VcfPreflightResult, max_errors: int) -> None:
        self.result = result
        self.max_errors = max_errors

    @property
    def stop(self) -> bool:
        return len(self.result.structural_findings) >= self.max_errors

    def error(self, stage: str, message: str, line_number: Optional[int] = None) -> None:
        if len(self.result.structural_findings) < self.max_errors:
            self.result.structural_findings.append(
                VcfFinding(stage=stage, message=message, line_number=line_number)
            )
            if len(self.result.structural_findings) == self.max_errors:
                self.result.errors_truncated = True
        else:
            self.result.errors_truncated = True

    def advisory(self, stage: str, message: str, line_number: Optional[int] = None) -> None:
        if len(self.result.advisory_findings) < self.max_errors:
            self.result.advisory_findings.append(
                VcfFinding(stage=stage, message=message, line_number=line_number, severity="warning")
            )


class _ByteLimitExceeded(Exception):

    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"decompressed input exceeded {limit} bytes")


class _LineTooLong(Exception):

    def __init__(self, line_number: int, limit: int) -> None:
        self.line_number = line_number
        self.limit = limit
        super().__init__(f"line exceeds the {limit}-byte preflight limit")


class _CountingReader:
    """Read fixed-size chunks while enforcing a decompressed-byte ceiling."""

    def __init__(self, source: BinaryIO, max_bytes: Optional[int]) -> None:
        self.source = source
        self.max_bytes = max_bytes
        self.bytes_read = 0

    def read(self, size: int = _READ_CHUNK_BYTES) -> bytes:
        data = self.source.read(size)
        if not isinstance(data, bytes):
            raise TypeError("VCF input stream must return bytes")
        self.bytes_read += len(data)
        if self.max_bytes is not None and self.bytes_read > self.max_bytes:
            raise _ByteLimitExceeded(self.max_bytes)
        return data


def _iter_binary_lines(source: _CountingReader, max_line_bytes: int) -> Iterable[Tuple[int, bytes, bytes]]:
    """Yield ``(line number, content, terminator)`` without universal-newline loss."""

    line = bytearray()
    line_number = 1
    pending_cr = False

    def emit(terminator: bytes) -> Tuple[int, bytes, bytes]:
        nonlocal line_number
        emitted = (line_number, bytes(line), terminator)
        line.clear()
        line_number += 1
        return emitted

    while True:
        chunk = source.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        for byte in chunk:
            if pending_cr:
                if byte == 10:
                    yield emit(b"\r\n")
                    pending_cr = False
                    continue
                yield emit(b"\r")
                pending_cr = False
            if byte == 10:
                yield emit(b"\n")
            elif byte == 13:
                pending_cr = True
            else:
                line.append(byte)
                if len(line) > max_line_bytes:
                    raise _LineTooLong(line_number, max_line_bytes)

    if pending_cr:
        yield emit(b"\r")
    elif line:
        yield emit(b"")


def is_vcf_filename(filename: Union[str, os.PathLike]) -> bool:
    """Return whether a filename identifies a VCF or compressed VCF."""

    return str(filename).lower().endswith((".vcf", ".vcf.gz"))


def _looks_like_gzip(path_or_stream: Union[str, os.PathLike, BinaryIO]) -> bool:
    if isinstance(path_or_stream, (str, os.PathLike)):
        path = Path(path_or_stream)
        if path.name.lower().endswith(".gz"):
            return True
        try:
            with path.open("rb") as source:
                return source.read(2) == b"\x1f\x8b"
        except OSError:
            return False
    try:
        position = path_or_stream.tell()
        magic = path_or_stream.read(2)
        path_or_stream.seek(position)
        return magic == b"\x1f\x8b"
    except (AttributeError, OSError, TypeError):
        return False


def validate_vcf(path_or_stream: Union[str, os.PathLike, BinaryIO],
                 *,
                 filename: Optional[str] = None,
                 compressed: Optional[bool] = None,
                 max_errors: int = DEFAULT_MAX_ERRORS,
                 max_line_bytes: int = DEFAULT_MAX_LINE_BYTES,
                 max_uncompressed_bytes: Optional[int] = DEFAULT_MAX_UNCOMPRESSED_BYTES) -> VcfPreflightResult:
    """Validate a VCF path or binary stream using only the Python standard library.

    Structural findings make ``result.ok`` false and are never overrideable by
    the upload review.  Advisory findings leave ``result.ok`` true but make
    ``result.requires_confirmation`` true.
    """

    if max_errors < 1:
        raise ValueError("max_errors must be at least 1")
    if max_line_bytes < 1:
        raise ValueError("max_line_bytes must be at least 1")
    if max_uncompressed_bytes is not None and max_uncompressed_bytes < 1:
        raise ValueError("max_uncompressed_bytes must be at least 1 or None")

    source_name = filename or str(getattr(path_or_stream, "name", "<stream>"))
    compressed = _looks_like_gzip(path_or_stream) if compressed is None else compressed
    result = VcfPreflightResult(source_name=source_name)
    collector = _FindingCollector(result, max_errors=max_errors)

    try:
        with ExitStack() as stack:
            if isinstance(path_or_stream, (str, os.PathLike)):
                raw_source = stack.enter_context(open(path_or_stream, "rb"))
            else:
                raw_source = path_or_stream
            if compressed:
                source = stack.enter_context(gzip.GzipFile(fileobj=raw_source, mode="rb"))
            else:
                source = raw_source
            _validate_stream(
                _CountingReader(source, max_uncompressed_bytes),
                result=result,
                collector=collector,
                max_line_bytes=max_line_bytes,
            )
    except _ByteLimitExceeded as error:
        collector.error(
            "compression" if compressed else "input",
            f"decompressed input exceeds the configured {error.limit}-byte limit; "
            "the file cannot be preflighted safely",
        )
    except _LineTooLong as error:
        collector.error("record", str(error), error.line_number)
    except (gzip.BadGzipFile, EOFError, zlib.error, OSError) as error:
        detail = str(error) or "compressed stream ended unexpectedly"
        collector.error(
            "compression" if compressed else "input",
            f"cannot read the file stream ({detail}); check for truncation or corruption",
        )
    return result


def _validate_stream(source: _CountingReader,
                     *,
                     result: VcfPreflightResult,
                     collector: _FindingCollector,
                     max_line_bytes: int) -> None:
    first_nonempty_seen = False
    fileformat_seen = False
    column_header_seen = False
    column_header_line: Optional[int] = None
    expected_fields = 0
    warned_non_lf = False

    for line_number, raw_line, terminator in _iter_binary_lines(source, max_line_bytes):
        if terminator and terminator != b"\n" and not warned_non_lf:
            collector.advisory(
                "header",
                "non-LF line terminators are accepted but may not be compatible with downstream VCF tools",
                line_number,
            )
            warned_non_lf = True

        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError as error:
            collector.error(
                "record" if column_header_seen else "header",
                f"line is not valid UTF-8 ({error.reason}); save the VCF as UTF-8 text",
                line_number,
            )
            if collector.stop:
                break
            continue

        if not line:
            continue
        if not first_nonempty_seen:
            first_nonempty_seen = True
            fileformat_match = _FILEFORMAT_RE.fullmatch(line)
            if not fileformat_match:
                collector.error(
                    "header",
                    "first non-empty line must be ##fileformat=VCFv4.<n>",
                    line_number,
                )
            else:
                fileformat_seen = True
                result.version = f"VCFv4.{fileformat_match.group(1)}"
                if fileformat_match.group(1) not in {"0", "1", "2", "3"}:
                    collector.advisory(
                        "header",
                        f"VCF version {result.version} is not one of the commonly supported 4.x versions; "
                        "continuing with structural checks",
                        line_number,
                    )
            continue

        if not column_header_seen:
            if line == "#CHROM" or line.startswith("#CHROM"):
                header_fields = line.split("\t")
                if len(header_fields) < len(_MANDATORY_COLUMNS) or tuple(header_fields[:8]) != _MANDATORY_COLUMNS:
                    collector.error(
                        "header",
                        "#CHROM header must be tab-delimited and begin with "
                        "#CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO in that order",
                        line_number,
                    )
                    continue
                if len(header_fields) == 8:
                    expected_fields = 8
                elif header_fields[8] != "FORMAT" or len(header_fields) < 10:
                    collector.error(
                        "header",
                        "FORMAT must be followed by at least one sample column",
                        line_number,
                    )
                    continue
                else:
                    expected_fields = len(header_fields)
                column_header_seen = True
                column_header_line = line_number
                continue

            if line.startswith("#") and not line.startswith("##"):
                collector.advisory(
                    "header",
                    "metadata-like header line uses one #; bcftools-compatible metadata lines use ##",
                    line_number,
                )
                continue
            if line.startswith("##"):
                _validate_meta_line(line, line_number, collector, fileformat_seen)
                if collector.stop:
                    break
                continue
            collector.error(
                "header",
                "expected a ## metadata line or the tab-delimited #CHROM column header",
                line_number,
            )
            if collector.stop:
                break
            continue

        if line.startswith("#"):
            collector.error("record", "unexpected header/comment line after the #CHROM header", line_number)
        elif line:
            format_keys_for_record = _format_keys_for_record(line, expected_fields)
            reasons = _record_shape_errors(line, expected_fields, format_keys_for_record)
            if reasons:
                collector.error("record", "; ".join(reasons), line_number)
            else:
                result.records_checked += 1
        if collector.stop:
            break

    if not first_nonempty_seen:
        collector.error("header", "file is empty; a VCF must contain a fileformat and #CHROM header")
    elif not fileformat_seen:
        collector.error("header", "missing required first-line ##fileformat=VCFv4.<n> metadata")
    if not column_header_seen:
        collector.error(
            "header",
            "missing required tab-delimited #CHROM column header",
            column_header_line,
        )


def _validate_meta_line(line: str,
                        line_number: int,
                        collector: _FindingCollector,
                        fileformat_seen: bool) -> None:
    match = _META_KEY_RE.fullmatch(line)
    if not match:
        key_value_match = re.match(r"^##\s*[A-Za-z][A-Za-z0-9_.-]*\s*:", line)
        if key_value_match:
            collector.advisory(
                "header",
                "metadata uses key:value notation; bcftools-compatible metadata uses key=value",
                line_number,
            )
        else:
            collector.advisory(
                "header",
                "header continuation line has no key=value declaration; add a metadata key",
                line_number,
            )
        return

    key, value = match.groups()
    if key == "fileformat" and fileformat_seen:
        collector.error("header", "##fileformat appears more than once", line_number)
        return
    if not value.strip():
        collector.error("header", f"##{key} metadata has an empty value", line_number)
        return
    if value.lstrip().startswith("<") and not value.rstrip().endswith(">"):
        collector.error("header", f"##{key} structured metadata is missing its closing >", line_number)
        return

    if key.upper() == "INFO" and value.lstrip().startswith("<"):
        inner = value.strip()[1:-1] if value.rstrip().endswith(">") else value.strip()[1:]
        if attribute_name := _first_colon_attribute(inner):
            collector.advisory(
                "header",
                f"INFO attribute {attribute_name} uses key:value notation; use key=value",
                line_number,
            )


def _first_colon_attribute(value: str) -> Optional[str]:
    """Find a colon separator outside quoted INFO attribute values."""

    attribute_start = 0
    in_quotes = False
    escaped = False
    for index, character in enumerate(value + ","):
        if escaped:
            escaped = False
        elif character == "\\" and in_quotes:
            escaped = True
        elif character == '"':
            in_quotes = not in_quotes
        elif character == "," and not in_quotes:
            attribute = value[attribute_start:index]
            match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_.-]*)\s*:", attribute)
            if match:
                return match.group(1)
            attribute_start = index + 1
    return None


def _format_keys_for_record(line: str, expected_fields: int) -> List[str]:
    fields = line.split("\t")
    if len(fields) <= 8 or len(fields) < expected_fields:
        return []
    if fields[8] in {"", "."}:
        return []
    return fields[8].split(":")


def _record_shape_errors(line: str, expected_fields: int, format_keys: List[str]) -> List[str]:
    fields = line.split("\t")
    reasons: List[str] = []
    if len(fields) != expected_fields:
        reasons.append(f"record has {len(fields)} tab-delimited fields; expected {expected_fields}")
        return reasons

    if not _POS_RE.fullmatch(fields[1]):
        reasons.append("POS must be a positive integer")
    if fields[5] != ".":
        try:
            quality = float(fields[5])
            if not math.isfinite(quality) or quality < 0:
                raise ValueError
        except ValueError:
            reasons.append("QUAL must be . or a non-negative number")
    if fields[6] != ".":
        filter_tokens = fields[6].split(";")
        if not filter_tokens or any(not _FILTER_TOKEN_RE.fullmatch(token) for token in filter_tokens):
            reasons.append("FILTER must be . or a non-empty semicolon-delimited token list")
    if not _valid_allele(fields[3], allow_star=False):
        reasons.append("REF must contain IUPAC bases or a symbolic allele")
    alt_alleles = fields[4].split(",")
    if not alt_alleles or any(not _valid_allele(allele, allow_star=True) for allele in alt_alleles):
        reasons.append("ALT must contain IUPAC bases, symbolic alleles, or * separated by commas")

    if expected_fields > 8:
        if not format_keys or any(not key for key in format_keys):
            reasons.append("FORMAT must contain non-empty colon-delimited keys")
        elif any(len(sample.split(":")) > len(format_keys) for sample in fields[9:]):
            reasons.append("sample FORMAT values contain more fields than the declared FORMAT keys")
    return reasons


def _valid_allele(allele: str, *, allow_star: bool) -> bool:
    if not allele:
        return False
    if allow_star and allele == "*":
        return True
    if _SYMBOLIC_ALLELE_RE.fullmatch(allele):
        return True
    return all(base in _IUPAC_BASES for base in allele.upper())
