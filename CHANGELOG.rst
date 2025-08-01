=============
smaht-submitr
=============

----------
Change Log
----------

1.12.0
======
`PR 29 SN DSA Validator <https://github.com/smaht-dac/submitr/pull/29>`_

* Add validator for SupplementaryFile that checks that `haplotype` and `donor_specific_assembly` are present if `data_type` contains "DSA" and the `file_format` is "fa"


1.11.0
======
`PR 28 SN Add ONT unaligned reads validator <https://github.com/smaht-dac/submitr/pull/28>`_

* Adds a validator that reports if any UnalignedRead items that are from ONT sequencers are missing the `software` property, or if any linked Software items are missing ONT-specific properties
* Also checks if `derived_from` is missing for ONT fastq files


1.10.1
======
`PR 31 SN fix library prep validator <https://github.com/smaht-dac/submitr/pull/31>`_

* Add null value option of empty list to all schema get commands for library prep validator and paired reads validator


1.10.0
======
`PR 27 SN Add RIN required validator <https://github.com/smaht-dac/submitr/pull/27>`_

* Add a validator that ensures that the property rna_integrity_number has a value for Analyte items where "RNA" is in molecule and non-RNA analytes cannot have a value for `rna_integrity_number`


1.9.1
=====
`PR 30 Fix external_id validator <https://github.com/smaht-dac/submitr/pull/30>`_

* Add protectors in validators to account for empty or hidden spreadsheets


1.9.0
=====
`PR 25 SN External ID validators <https://github.com/smaht-dac/submitr/pull/25>`_

* Add a validator for Tissue that checks that the linked Donor `external_id` is contained within the `external_id` of the Tissue (e.g. SMHT001 and SMHT001-3A)
* Add a validator for TissueSample that checks that the linked Tissue` external_id` is contained within the `external_id` of the TissueSample (e.g. SMHT001-3A and SMHT001-3A-001A1)


1.8.0
=====
`PR 22: SN strand validator <https://github.com/smaht-dac/submitr/pull/22>`_

* Add validator that requires that `strand` in LibraryPreparation be filled out if the Library is linked to RNA Analyte items and 
  requires that `rna_seq_protocol` in LibraryPreparation be filled out for RNA-Seq libraries
* Both of these properties are forbidden for non-RNA libraries


1.7.2
=====
`WF resume_uploads credentials check <https://github.com/smaht-dac/submitr/pull/26>`_

* Add check to ``resume_uploads`` command for invalid credentials
* Update error message for invalid credentials


1.7.1
=====
`PR 24 SN Add life history items to unreferenced list <https://github.com/smaht-dac/submitr/pull/24>`_

- Add Demographic, Diagnosis, Exposure, FamilyHistory, MedicalTreatment, DeathCircumstances, and TissueCollection to `_TYPES_WHICH_ARE_ALLOWED_TO_BE_UNREFERENCED` in the unreferenced_validator


1.7.0
=====
`PR 23 SN paired read validator <https://github.com/smaht-dac/submitr/pull/23>`_

* Adds a validator that reports if any UnalignedRead items that are paired fastqs defined in the spreadsheet (StructuredDataSet) are paired appropriately to the same FileSet item with the R2 file paired to the R1 file
* Also checks for duplicate R1 file references in paired_with


1.6.3
=====
Update dcicutils to 8.13.3.


1.6.2
=====
Thug commit fixing build with comments for these versions.


1.6.1
=====
Thug commit changing beta dcicutils to real one (8.18.2).


1.6.0
=====
* 2025-03-04 / dmichaels
  Branch: dmichaels-20250304-correct-error-row-number-and-detect-orphans | from main (49ebe1ef101b0ec5153d382517ed33a473f4c26c) | PR-20
  - Corrected for off-by-one error for error reporting in validators.submitted_id_validator._submitted_id_validator_finish.
  - Detect "orphaned" items in spreadsheet; orphaned items are those items (rows) defined within the spreadsheet which have
    no internal (within the spreadsheet) references to it (as identified by the submitted_id for the item); but ignoring such
    items which are one of these types: AlignedReads, HistologyImage, Supplementaryfiles, TissueSample, UnalignedReads, VariantCalls
    See submitr/validators/unreferenced_validator.py. Turn this off using the --ignore-orphans option to submit-metadata-bundle.


1.5.1
=====
* 2025-02-28 / dmichaels
  Branch: dmichaels-20250228-correct-submitr-config-path | from main (779b6044ab3d84373f1514e36270c4e063d2ed80) | PR-19
  - Updated dcicutils to 8.18.1 to point to correct (master) branch for config/custom_column_mappings.js.


1.5.0
=====
* 2025-02-07 / dmichaels
  Branch: dmichaels-20250207-sheet-instance-names | from main (5de96fbc5b0c818c3dc3b5122750c13fbf43a6a3) | PR-18
  - Support for sheet "instance" names, i.e. where we can have multiple sheets referring to the same type,
    for example can have sheets named "DSA_ExternalQualityMetric" and "ExternalQualityMetric" which
    are both of the type ExternalQualityMetric. Previously the sheet name referred exclusively to
    the single portal object namea; and sheet names must be unique within a spreadsheet; so there
    was no way to have multiple sheets of the same type; with this change this will be allowed.
    This was actually to custom_excel.py; and/but then realized this, and the previous change
    WRT the qc_values pseudo-column support contained therein, needed to go into dcicutils because
    it needed to be used on the smaht-portal/ingestion side of things as well; so it is there now.
  - Considered removing "consortia" from the IngestionSubmission object creation as this is not needed and
    it causes permission problems for non-admin users; see submitr.submission._post_submission. But after
    back/forth decided instead to remove restricted_fields from consortial in smaht-portal/.../mixins.json.

1.4.0
=====
* 2025-01-15 / branch: dmichaels-custom-column-mappings-20250115 / PR-16 / dmichaels
* Added custom column mappings for simplified QCs specification in spreadsheet. 
  The bulk of this is in submitr/custom_excel.py where we use a special CustomExcel class
  for use by StructuredDataSet (in submission.py) which effectively/sorta preprocesses the
  spreadsheet according to the config file in config/custom_column_mappings.json; by default
  it pulls this config dynamically (from the master branch of) of this (public) GitHub repo.


1.3.0
=====
* Fix for C4-1187 where we were not implicitly adding consortia to submitted like for submission-centers.
  Also added setting of file_size for uploaded files.


1.2.0
=====
* Changed MEANING of (and added --submit-new synonym for) the --submit option, which now
  means that IF any submitted metadata items would result in actual UPDATES of items which
  already EXIST in the database, then an ERROR/message will be given and nothing will be done.
  - Added new a --update (and submit-update synonym for) option which
    means that items which already EXIST in the database MAY be updated.
* Fix submission_uploads.py/file_for_upload.py to not bomb out of the file upload process
  if we cannot get upload_credentials; this can happen if the file being uploaded already
  has as status of uploaded (or anything except uploading or in-review); so in this case,
  where the file status is uploaded, we will detect it, give a warning that this file is
  being skipped for upload because it has already been uploaded, and continue on.
  This uses new smaht-portal /files/{uuid}/upload_file_size endpoint; if it this
  does not yet exist though we fail gracefully, not doing this check in this case.
* Validator hook to validate (all) submitted_id values; see validators.submitted_id_validator.
* Validator hook to look for duplicate rows for certain types; see validators.duplicate_row_validator.
* Validator hook to validate submitted_id values using server-side custom validator.
* Added support for FileSet.expected_file_count pseudo column; see validators.file_set_count_validator.
* Added --nouploads option (if using resume-uploads later).
* Print Python version in command header, and Portal version.


1.1.1
=====
* Mostly changes related to additional fixes/enhancements from this doc:
  https://docs.google.com/document/d/1zj-edWR1ugqhd6ZxC07Rkq6M7I_jqiR-pO598gFg0p8
* Fixed bug (to dcicutils 8.13.3.1b11) structured_data.py to NOT silently convert
  a string representing a floating point number to an integer.
* Moved utility scripts view-portal-object and update-portal-object to dcicutils 8.13.3.
* Extensible validators hook mechanism (see submitr/validators.py) initially for submitted_id;
  uses new smaht-portal /validators/submitted_id/{submitted_id} endpoint/API to flag
  misformatted submitted_id values; also flags duplicates. See submitr/validators directory.
* Changed to disallow fuzzy matches (prefixes) for enum types; must be exact match (case-insensitive);
  actual change in dcicutils.misc_utils.to_enum.
* Changed to report errors for malformed dates, e.g. "6/29/2024" rather than "2024-06-29";
  actual change in dcicutils.structured_data.Schema._map_function_date/time.


1.1.0
=====
* Fix for local make exe (for building binaries locally).
* Make work with Python 3.12.
  - Had to update to flake8 which required low Python version to go from 3.8 to 3.8.1.
  - Had to update dcicutils for pyramid update (from 1.10.4 to 2.0.2 for imp import not found).
  - Had to update a couple tests for assert_called_with rather than called_with.
  - Had to update a couple tests for different behavior for assert_called_with.
  - Removed obsolete tests (for obsolete/unsupported scripts).


1.0.0
=====
* Using pyinstaller to create a single independent executable (per command)
  so commands can be run without having Python/pyenv/etc installed.
* Some changes related to starting work on integration tests with the portal.


0.8.3
=====

* 2024-05-14/dmichaels/PR-10
* Added rclone support; most relevant code in submitr/rclone directory. 
  A lot of refactoring of file upload related code for this (see files_for_upload.py)
* Added metadata_template.py module with goal of checking the user's metadata
  file with the latest HMS DBMI metadata template and giving a warning if the
  version appears to be out of date. Also new convenience command to export and
  download the HMS metadata template file to Excel file (get-metadata-template).
* Added option to --version to automatically (after prompting) update version to latest.
* Added ability to print upload file info for check-submissionn.
* Fixed ETA for server-side validation/submission progress bar.
* Other progress bar improvements.
* Removed shortened forms of command options to remove ambiguity (e.g. -sd / --server d).
* Added warning for use of obsolete command options.
* Improved messaging on exit when interrupting server-side validation/submission.
* Improved messaging for check-submission.
* Fix for usage of --keys (was not being used for server validation/submission).
* Minor fix for --validate-local-skip option (undefined structured_data variable).
* Fix for --validate-remote-skip option to pass validate_skip to ingester to
  skip the validation on submission which happens by default before the loadxl.
* Added --files for use with --info to submit-metadata-bundle.
* For file uploads, after asking the same yes/no question and getting the same response many
  times in a row, ask if all subsequent such questions should automatically get the same answer.
* Removed ref_lookup_strategy references for structured_data; refactored/internalized in dcicutils.


0.8.2
=====

* 2024-05-08/dmichaels/PR-8
  Pass validate_only flag to ingester on --validate-remote-skip to
  skip server-side validation on submit; previously this flag merely
  served to skip kicking off server-side validation from submitr.
  ONLY allowed (on server-side) for admin users.


0.8.2
=====

* 2024-05-08/dmichaels/PR-8
  Pass validate_only flag to ingester on --validate-remote-skip to
  skip server-side validation on submit; previously this flag merely
  served to skip kicking off server-side validatieon from submitr.

0.8.0
=====

* FYI the 'draft' branch is made from branch dmichaels-20240205 (on 2024-02-23) was
  made with the sole purpose of having a readthedocs version is the name "draft".
* Documentation updates.
* Lots of reworking of validation options (from discussion with Elizabeth).
  Require --validate or --submit; do remote/server validation silently; etc.
* Changed "Author" name/email in PyPi to SMaHT DAC / smhelp@hms-dbmi.atlassian.net;
  controlled by pyproject.toml.
* Changes to view-portal-object script (need to update this in dcicutils).
* Support for submits_for to get submission center.
* Got rid of "old style" protocol support (to simplify).


0.5.4
=====

* Test release from (non-master) branch to change "Author" name/email at pypi.


0.5.3
=====

* Version updates to dcicutils.
* Changes to itemize SMaHT submission ingestion create/update/diff situation.


0.5.2
=====

* Refactored to use dcicutils.portal_utils.Portal.
* Many minor-ish changes to submit-metadata-bundle, resume-uploads, upload-item-data.
  E.g. sanity checking file paths and uuids, providing more info/feedback to user,
  allowing accession ID or accession ID based file name, show file sizes, etc.
* Subsumed upload-item-data functionality into resume-uploads for convenience.
* Starting (readthedocs) documentation updates.


0.5.1
=====

* Thug commit to initiate publish.


0.5.0
=====

* Lotsa SMaHT ingestion related work.


0.4.0
=====

* Upgrade to Python 3.11; and 3.7 no longer supported.
* Added --details option so submit-metadata-bundle and show-upload-info
  to fetch and show detailed information from S3.
* Added sanity checks for submitted file.


0.3.4
=====

* Documentation refactor for ReadTheDocs to use an iframe for the logo.


0.3.3
=====

* Make the heading for "Basic Setup" to be "Installing Prerequisites",
  since that naming is more standard.
* Rename the "Getting Started" option to more standard "Using submitr",
  since getting started is ambiguous between installation and usage.
* Add an "Implementation of submitr" heading on the implementation part
  to make it clear to end users they don't need to look at this.
* Reorganize to make experimental ``rclone`` support *not* be the first thing
  that you see in this doc,
  since non-experimental stuff needs to be first.
* Make ``rclone`` section not pretend to tell you about ``awscli``
  in the heading, since the actual text barely mentions ``awscli``.
* Light editing on the opening of the section about ``rclone`` to make
  the motivational part clearer.


0.3.2
=====

* Fix auto-publish on pushing a tag.
* Disabled ``scripts/publish`` since we're using functionality from ``dcicutils.scripts`` now.
* Adjusted headings to present with better indentation and better recursive header presentation.


0.3.1
=====

* Auto-submit to readthedocs on any non-beta version tag push (v* except v*b*).
* Fix a bug in readthedocs submission where we were using branches=master and getting an error saying
  ``{"detail":"Parameter \"ref\" is required"}``. ChatGPT thinks this is because we wanted a curl
  parameter of ``-d "ref=master"`` rather than ``-d "branches=master"`` like we had.
* Remove spurious "Module Contents" headings in three places.
  We do not put code in ``__init__.py`` so these sections would always be empty (and confusing).


0.3.0
=====

* Add a pretty logo
* Warn about not yet being still experimental.
* Better badges.


0.2.1
=====

* Some commands will now default the app to 'smaht' better.
* In general, a lot of rewriting of 'cgap' references to
  be either SMaHT or to reference a centrally defined default.


0.2.0
=====

* Fix a bug in the project-association in Sphinx config file.
* Add a warning about preliminary nature in README.rst
* Enable auto-publish to readthedocs on checkin to master.
* Enable auto-publish to pypi on tag.

0.1.1
=====

* Additional tweaks mostly related to readthedocs.


0.1.0
=====

* Initial changes to give submitr a bit of a different look that SubmitCGAP.

0.0.0
=====

* Forked from SubmitCGAP 4.1.0.

