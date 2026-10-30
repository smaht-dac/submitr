VCF file preflight
==================

Submitr preflights local VCF files during the normal file review, before the
upload confirmation. Only files of the two portal VCF file formats, ``vcf``
(``.vcf``) and ``vcf_gz`` (``.vcf.gz``), are checked, with a streaming,
standard-library-only validator. A file's declared ``file_format`` (e.g. in
the submission spreadsheet) identifies it when present; otherwise its file name
does. Other file formats, including other ``VariantCalls`` file formats, are not
VCF preflighted.

A file declared as ``vcf`` or ``vcf_gz`` whose name does not end in that
format's extension, a ``.vcf`` file that is gzip/BGZF-compressed, or a
``.vcf.gz`` file that is not, is reported as a file format mismatch and kept
out of the upload; its content is not preflighted.

Structural failures are non-overridable and keep the file out of the upload:

* gzip or BGZF decompression errors, truncation, and the configured
  decompressed-byte limit;
* a missing or malformed ``##fileformat`` or ``#CHROM`` header; and
* malformed record field counts or the supported record-shape checks. An
  ``ALT`` of ``.`` is accepted as the no-alternate-allele case; otherwise
  ``ALT`` must list bases, symbolic alleles, or ``*`` (breakend replacement
  strings are not supported).

The preflight also reports narrowly scoped header compatibility advisories.
Metadata-like lines with one ``#`` instead of ``##``, INFO attributes written
with ``key: value`` instead of ``key=value``, and continuation lines without a
key are accepted but require explicit submitter confirmation before upload.
Line-ending and unknown-minor-version advisories use the same confirmation
path. Normal review output aggregates repeated advisories into actionable
counts; ``--verbose`` includes the affected line details. Review-only/
``--validate`` output does not select a file for upload and states when that
file would require confirmation. Structural errors are reported separately,
take precedence, and cannot be overridden by confirmation. No reference genome
is consulted and the validator does not attempt downstream VCF semantic or
annotation validation.
