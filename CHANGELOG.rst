==========
SubmitCGAP
==========

----------
Change Log
----------

2.0.1
=====

* Update documentation with some small fixes
* Add new basic setup documentation 


2.0.0
=====

* Drop support for Python 3.6 (C4-898)

* Use ``ignored``, ``local_attrs``, and ``override_environ``
  from ``dcicutils.misc_utils`` rather than ``dcicutils.qa_utils``. (C4-895)

* Add debugging instrumentation for failed access to credentials.


1.5.0
=====

* Support upload of extra files
* Update test submission FASTQ files to match update submission requirements


1.4.2
=====

* Further adustments to repair problems created by 1.4.1 (C4-818).


1.4.1
=====

* Fix SubmitCGAP file upload to work correctly under Microsoft/Windows 10 (C4-816).


1.4.0
=====

* Suppress stack traceback on unexpected errors.
* Allow suppression behavior to be overridden by setting environment variable ``DEBUG_CGAP=TRUE``.
* Add an instructive herald before unexpected errors, suggesting that a bug report might need to be filed.


1.3.0
=====

* Supports Python 3.9


1.2.0
=====

* Supports Python 3.8


1.1.3
=====

* Fixed name of keyfile in installation documentation and added/modified some of
  the wording and examples.


1.1.2
=====

* Documentation reorganized; some documentation specific to submitting
  family histories added.


1.1.1
=====

* Implements an optimization of the submission protocol so that if
  the ``upload_credentials`` contain an entry for ``s3_encrypt_key_id``,
  that value is used without the health page having to be consulted.


1.1.0
=====

* Support for proper handling of ``s3_encrypt_key_id`` where one is available
  (e.g., as shown in health page).


1.0.0
=====

**PR 15: Update to require dcicutils 3.1.0 (C4-736)**

* Fixes `SubmitCGAP still uses old dcicutils (C4-736) <https://hms-dbmi.atlassian.net/browse/C4-736>`_
  This change requires python 3.6.1 (instead of 3.6.0) and dcicutils 3.1.0 or greater (instead of 2.4.0).

  This is technically an incompatible change, though no one is calling into this
  library programmatically so there is probably not code to be changed.

* Bumps the major version to version 1.0.0 in part because of the technical change in dependencies
  and in part to celebrate that SubmitCGAP is being used for production work now.


0.10.0
======

**PR 14: Fix server regexp for cgap-msa (C4-710)**

* Allow orchestrated server names to pass syntax checking test.


0.9.0
=====

**PR 13: SubmitCGAP --no_query and --subfolders arguments**

* Add ``--no_query`` argument to ``resume_uploads``, ``submit_metadata_bundle``,
  and ``upload_item_data`` scripts as well as corresponding functions in
  ``submission``.
* Add ``--subfolders`` argument to ``resume_uploads`` and ``submit_metadata_bundle``
  scripts and corresponding functions.
* Change ``local_attrs`` import in base.py to reflect changes in ``dcicutils`` to allow
  commands to be run following install of ``submit_cgap`` without need to install
  ``pytest``.
* Update ``pyproject.toml`` and ``poetry.lock`` to require new version of ``dcicutils``.


0.8.0
=====

**PR 12: SubmitCGAP submit-genelist**

* Add ``submit-genelist`` command for uploading gene lists

0.7.3
=====

**PR 10: Fix scripts/publish (C4-512)**

* Fix the ``scripts/publish`` script to work on GitHub Actions (GA)
  by allowing a ``--noconfirm`` argument.


0.7.1, 0.7.2
============

These versions had flaws. The intended changes were released as version 0.7.3.

0.7.0
=====

**PR 9: SubmitCGAP --ingestion_type argument (C4-506)**

* Add ``--ingestion_type`` argument to ``submit-metadata-bundle``.


0.6.0
=====

**PR 8: SubmitCGAP file upload bug**

* Add ``--upload_folder`` argument to the ``resume-uploads``
  and ``submit-metadata-bundle`` scripts.
* Fix bug `SubmitCGAP file upload bug (C4-383) <https://hms-dbmi.atlassian.net/browse/C4-383>`_.
* Add ``make retest`` to re-run test cases that have failed.


0.5.0
=====

**PR 7: Accommodate new permissions protocol.**

* Implement support for submission with new permissions system.


0.4.3
=====

**PR 6: Convert build to GA**

* Converts build from Travis to Github Actions.


0.4.2
=====

**PR 5: Implement CGAP_KEYS_FILE**

* Fix environment variable ``CGAP_KEYS_FILE`` to allow override of what file contains the user's keys.  This is intended only for internal use, not for end users, which is why it's not an argument to the relevant commands.


0.4.1
=====

**PR 4: Fix defaulting of institution in submit-metadata-bundle.**

* Fix defaulting of the ``--institution`` and ``--project``
  command line arguments to the ``submit-metadata-bundle`` shell script.

* Add this ``CHANGELOG.rst``.


0.4.0
=====

**PR 3: Miscellaneous Refinements**

* Various unrelated things in response to alpha testing by Sarah Reiff.

  * Make an explicit dependency on awscli so if someone doesn't have that
    globally loaded, it gets loaded by Poetry.

  * **[Incompatible change]** Simplify the name of the key file to ``~/.cgap-keys.json``
    rather than ``~/.cgap-keydicts.json`` to avoid Python-specific
    terminology that users may not care about.

    .. warning::

        This is an **incompatible change**. However, we're still in major version 0,
        and such changes are allowed there. It only requires renaming your
        keys file.)

  * Make it possible to use an alternate keyfile, but only by
    setting an environment variable, ``CGAP_KEY_FILE``, so that ordinary users
    aren't doing this, as they should need to.

  * Special handling of talking to a server that doesn't have the necessary
    support. Hopefully not a problem going forward, but just in case.

  * Add a show-upload-info script (``scripts/show_upload_info.py``).

  * Rearrange documentation to have installation covered in its own file.

  * Extend documentation related to testing, especially interactively.

  * Delete ``proto_submit.py.txt``, which was part of initial scaffolding
    for this repo and is no longer useful.


0.3.0
=====

**PR 2: Provision RTD**

* Provisions readthedocs for Submit CGAP

0.2.0
=====

**PR 1: File uploads**

* Invocation of a /submit_for_ingestion server endpoint to send a metadata bundle
  for processing.

* Implement waiting (polling /IngestionSubmission pages) to see when processing
  is done.

* Upon successful processing remotely,
  manage upload of files implicated by the processing.


0.1.0
=====

* First stab at repository.
