VCF file preflight
==================

Submitr preflights local VCF files during the normal file review, before the
upload confirmation. Files named ``.vcf`` or ``.vcf.gz`` and files identified
as ``VariantCalls`` are checked with a streaming, standard-library-only
validator.

Structural failures are non-overridable and keep the file out of the upload:

* gzip or BGZF decompression errors, truncation, and the configured
  decompressed-byte limit;
* a missing or malformed ``##fileformat`` or ``#CHROM`` header; and
* malformed record field counts or the supported record-shape checks.

The preflight also reports narrowly scoped header compatibility advisories.
Metadata-like lines with one ``#`` instead of ``##``, INFO attributes written
with ``key: value`` instead of ``key=value``, and continuation lines without a
key are accepted but require explicit submitter confirmation before upload.
Line-ending and unknown-minor-version advisories use the same confirmation
path. No reference genome is consulted and the validator does not attempt
downstream VCF semantic or annotation validation.
