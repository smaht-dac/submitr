==========
SubmitCGAP
==========

----------
Change Log
----------


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
