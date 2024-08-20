=============
smaht-submitr
=============

----------
Change Log
----------


1.1.1
=====
* Change to dcicutils (8.13.3.1b11) structured_data.py to NOT silently convert a
  string representing a floating point number to an integer. Per bug report here:
  https://docs.google.com/document/d/1zj-edWR1ugqhd6ZxC07Rkq6M7I_jqiR-pO598gFg0p8
* Moved utility scripts view-portal-object and update-portal-object to dcicutils 8.13.3.
* Extensible validators mechanism (see submitr/validators.py) initially for submitted_id;
  uses new smaht-portal /validators/submitted_id/{submitted_id} endpoint/API to flag
  misformatted submitted_id values; also flags duplicates. See submitr/validators directory.
* Changed to disallow fuzzy matches (prefixes) for enum types; must be exact match (case-insensitive);
  actual change in dcicutils.misc_utils.to_enum.
* Changed to report errors for malformed dates, e.g. "6/29/2024" rather than "2024-06-29";
  actual change in dcicutils.structured_data.Schema._map_function_date/time.
* Changed MEANING of (and added --submit-new synonym for) the --submit option, which now
  means that IF any submitted metadata items would result in actual UPDATES of items which
  already EXIST in the database, then an ERROR/message will be given and nothing will be done.
  - Added new a --update (and submit-update synonym for) option which
    means that items which already EXIST in the database MAY be updated.


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

