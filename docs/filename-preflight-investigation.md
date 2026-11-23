# Filename preflight investigation

## Findings

Submitr assembles workbook-referenced files from `StructuredDataSet.upload_files` and then, for each portal File item, patches its `filename` to obtain upload credentials before sending bytes to S3. Metadata submission (server ingestion) creates or updates those File items before any upload begins, so a collision found only at upload time would leave the colliding item already committed. The portal collision preflight therefore runs after validation and before the metadata is submitted, and is repeated immediately before each filename PATCH/credential request as a last guard, including on resumed uploads, where `resume-uploads` takes the submission center from the item being resumed (the IngestionSubmission or File).

Workbook file references are basenames for upload purposes. Two different source paths can therefore address the same uploaded filename. The preflight reports duplicate normalized basenames with workbook sheet and row locations. A repeated filename is allowed when the references identify the same portal item, which supports legitimate updates without treating the item as a collision with itself.

Portal filename ownership must be scoped to the submission center carried by the submission flow. A same-name File belonging to another center is out of scope; an update that resolves to the same File (matched by `uuid`, `@id`, `submitted_id`, `accession`, or `aliases`) is also allowed. Lookup failures and records that cannot be shown to belong to the submitting center retain the existing tolerant lookup behavior rather than creating a false positive.

MD5 is already used by submitr for transfer/S3 verification and for metadata-bundle provenance. It is not used for this pre-upload portal filename collision check. Filename equality is intentionally the only comparison in this stage.

## Staged implementation plan

1. **Workbook protection (this stage):** reject duplicate normalized upload basenames across uploadable workbook file rows, including relevant nested upload entries, while reporting actionable sheet/row locations and permitting repeated references to the same portal item.
2. **Portal protection (this stage):** before submitting metadata, look up same-name portal Files for every workbook upload filename, retain only records belonging to the submitting submission center, exclude the item being updated, and abort with all collisions listed. Repeat the per-file check immediately before filename PATCH/credential generation.
3. **Future checksum stage:** compare content/checksums only after the filename protections have proven stable. This stage must not infer same-content identity from MD5.
4. **Future reservation stage:** add a server-side atomic filename reservation if portal-side race prevention is required. A client lookup alone cannot close a concurrent-upload race.

Checksum comparison, same-content detection, and server-side reservation are deliberately out of scope for this launch.
