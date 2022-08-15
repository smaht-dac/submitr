==================
Testing SubmitCGAP
==================

This document describes various ways to test this repository.

Unit Testing
============

The repository has unit testing. To invoke it, do::

   $ make test

This is just syntactic sugar for::

   $ pytest -vv

Suggested Interactive Tests
===========================

There are various commands in ``submit_cgap/scripts``
that you might want to execute at a
command shell. You may need to make small adjustments
to these examples to make them work for you.

As an example, some of these tests are offered with a
``-s http://localhost:8000`` argument (where ``-s`` is shorthand
for ``--server``) to talk to the localhost, since the default is to talk to the
production server. You might need to rewrite to use a different
server, or else to specify an example,
as in ``-e fourfront-cgapdev``.

Testing the Validate-Only Feature
---------------------------------

Use the ``-v`` or ``-validate-only`` option to validate but not submit a posting::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -v -s http://localhost:8000

There is also a test file that contains errors so that you can see what errors would look like::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test_with_errors.xlsx -v -s http://localhost:8000

In either case, you will be queried about whether to do the operation::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -v -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test.xlsx to http://localhost:8000 (for validation only)? [yes/no]: no
   Aborting submission.

Only if you answer yes will it proceed, though it will still require that you have credentials set up correctly::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -v -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test.xlsx to http://localhost:8000 (for validation only)? [yes/no]: yes
   CGAPPermissionError: Your credentials were rejected by http://localhost:8000. Either this is not the right server, or you need to obtain up-to-date access keys.

Getting correct credentials is a matter of having your ``~/.cgap-keys.json`` file
in good order. See `Setting Up Credentials <INSTALLATION.rst#Setting Up Credentials>`__.
If credentials are set up properly, you can do::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -v -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test.xlsx to http://localhost:8000 (for validation only)? [yes/no]: yes
   The server http://localhost:8000 recognizes you as Kent Pitman <kent_pitman@hms.harvard.edu>.
   Using institution: /institutions/hms-dbmi/
   Using project: /projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/
   22:26:11 Bundle uploaded, assigned uuid 353fa353-fec2-4e4d-a4ba-0cbe60aa550d for tracking. Awaiting processing...
   22:26:27 Final status: success
   ----- Validation Output -----
   file_fastq items: 4 validated; 0 errors
   file_processed items: 0 validated; 0 errors
   sample items: 3 validated; 0 errors
   individual items: 3 validated; 0 errors
   family items: 1 validated; 0 errors
   sample_processing items: 1 validated; 0 errors
   report items: 1 validated; 0 errors
   case items: 3 validated; 0 errors
   All items validated.

Of course, there could be an error in the file,
in which case you'd see something more like::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test_with_errors.xlsx -v -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test_with_errors.xlsx to http://localhost:8000 (for validation only)? [yes/no]: yes
   The server http://localhost:8000 recognizes you as Kent Pitman <kent_pitman@hms.harvard.edu>.
   Using institution: /institutions/hms-dbmi/
   Using project: /projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/
   22:29:58 Bundle uploaded, assigned uuid efbec0ae-34d3-4f08-87d9-72bfcb3bc8d3 for tracking. Awaiting processing...
   22:30:13 Final status: failure
   ----- Validation Output (prior to failure) -----
   Row 0 - Proband for this analysis could not be found. This row cannot be processed.
   Row 1 - Proband for this analysis could not be found. This row cannot be processed.
   Row 2 - Proband for this analysis could not be found. This row cannot be processed.
   file_fastq items: 0 validated; 0 errors
   file_processed items: 0 validated; 0 errors
   sample items: 0 validated; 0 errors
   individual items: 0 validated; 0 errors
   family items: 0 validated; 0 errors
   sample_processing items: 0 validated; 0 errors
   report items: 0 validated; 0 errors
   case items: 0 validated; 0 errors
   Errors found in items. Please fix spreadsheet before submitting.

Testing Metadata Bundle Submissions
-----------------------------------

When everything is all fixed up and you're ready to do the posting,
it's time to try it one more time::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test.xlsx to http://localhost:8000? [yes/no]: yes
   The server http://localhost:8000 recognizes you as Kent Pitman <kent_pitman@hms.harvard.edu>.
   Using institution: /institutions/hms-dbmi/
   Using project: /projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/
   01:27:54 Bundle uploaded, assigned uuid c5bdbeee-49f1-4fa7-9e64-bc93f2cb151f for tracking. Awaiting processing...
   01:28:09 Final status: success
   ----- Validation Output -----
   file_fastq items: 4 validated; 0 errors
   file_processed items: 0 validated; 0 errors
   sample items: 3 validated; 0 errors
   individual items: 3 validated; 0 errors
   family items: 1 validated; 0 errors
   sample_processing items: 1 validated; 0 errors
   report items: 1 validated; 0 errors
   case items: 3 validated; 0 errors
   All items validated.
   ----- Post Output -----
   Success - sample 3464467 posted
   Success - sample 3464468 posted
   Success - sample 3464469 posted
   Success - individual 456 posted
   Success - individual 789 posted
   Success - individual 123 posted
   Success - family 333 posted
   file_fastq: 4 items posted successfully; 0 items not posted
   sample: 3 items posted successfully; 0 items not posted
   individual: 3 items posted successfully; 0 items not posted
   family: 1 items posted successfully; 0 items not posted
   sample_processing: 1 items posted successfully; 0 items not posted
   report: 1 items posted successfully; 0 items not posted
   case: 3 items posted successfully; 0 items not posted
   file_fastq: 4 items patched successfully; 0 items not patched
   sample: 3 items patched successfully; 0 items not patched
   individual: 3 items patched successfully; 0 items not patched
   family: 1 items patched successfully; 0 items not patched
   sample_processing: 1 items patched successfully; 0 items not patched
   report: 1 items patched successfully; 0 items not patched
   case: 3 items patched successfully; 0 items not patched
   ----- Upload Info -----
   {'uuid': '7f09e053-0cee-42ac-aa47-f725adb183d5', 'filename': 'f1_R1.fastq.gz'}
   {'uuid': '776f1767-cb43-48d1-84dc-90955ce0930a', 'filename': 'f1_R2.fastq.gz'}
   {'uuid': '7c039d90-4072-419b-ae12-7031ea9d4274', 'filename': 'f2_R1.fastq.gz'}
   {'uuid': '4afcf1c7-ebfe-4e96-b272-69f358e43ca0', 'filename': 'f2_R2.fastq.gz'}
   Upload 4 files? [yes/no]: yes
   Uploading submit_cgap/tests/data/f1_R1.fastq.gz to item 7f09e053-0cee-42ac-aa47-f725adb183d5 ...
   Going to upload submit_cgap/tests/data/f1_R1.fastq.gz to s3://encoded-4dn-files/7f09e053-0cee-42ac-aa47-f725adb183d5/GAPFIYYBY24O.fastq.gz.
   Uploaded in 1.46 seconds
   Upload of submit_cgap/tests/data/f1_R1.fastq.gz to item 7f09e053-0cee-42ac-aa47-f725adb183d5 was successful.
   Uploading submit_cgap/tests/data/f1_R2.fastq.gz to item 776f1767-cb43-48d1-84dc-90955ce0930a ...
   Going to upload submit_cgap/tests/data/f1_R2.fastq.gz to s3://encoded-4dn-files/776f1767-cb43-48d1-84dc-90955ce0930a/GAPFIXJRIVGO.fastq.gz.
   Uploaded in 1.78 seconds
   Upload of submit_cgap/tests/data/f1_R2.fastq.gz to item 776f1767-cb43-48d1-84dc-90955ce0930a was successful.
   Uploading submit_cgap/tests/data/f2_R1.fastq.gz to item 7c039d90-4072-419b-ae12-7031ea9d4274 ...
   Going to upload submit_cgap/tests/data/f2_R1.fastq.gz to s3://encoded-4dn-files/7c039d90-4072-419b-ae12-7031ea9d4274/GAPFINORP5F5.fastq.gz.
   Uploaded in 0.74 seconds
   Upload of submit_cgap/tests/data/f2_R1.fastq.gz to item 7c039d90-4072-419b-ae12-7031ea9d4274 was successful.
   Uploading submit_cgap/tests/data/f2_R2.fastq.gz to item 4afcf1c7-ebfe-4e96-b272-69f358e43ca0 ...
   Going to upload submit_cgap/tests/data/f2_R2.fastq.gz to s3://encoded-4dn-files/4afcf1c7-ebfe-4e96-b272-69f358e43ca0/GAPFIMK89CF6.fastq.gz.
   Uploaded in 0.72 seconds
   Upload of submit_cgap/tests/data/f2_R2.fastq.gz to item 4afcf1c7-ebfe-4e96-b272-69f358e43ca0 was successful.

Note that you have some queries you'll have to answer in the middle of this.

Testing resume-uploads
----------------------

If for some reason you had answered no to "Upload 4 files?" you could
resume this operation later by using the GUID that was mentioned toward
the beginning of the output where it says::

   01:27:54 Bundle uploaded, assigned uuid c5bdbeee-49f1-4fa7-9e64-bc93f2cb151f for tracking. Awaiting processing...

This guid is the tracking ID for this submission. You can do::

   $ resume-uploads c5bdbeee-49f1-4fa7-9e64-bc93f2cb151f --bundle_filename submit_cgap/tests/data/cgap_submit_test.xlsx -s http://localhost:8000
   Upload 4 files? [yes/no]: yes
   Uploading submit_cgap/tests/data/f1_R1.fastq.gz to item 7f09e053-0cee-42ac-aa47-f725adb183d5 ...
   Going to upload submit_cgap/tests/data/f1_R1.fastq.gz to s3://encoded-4dn-files/7f09e053-0cee-42ac-aa47-f725adb183d5/GAPFIYYBY24O.fastq.gz.
   Uploaded in 0.86 seconds
   Upload of submit_cgap/tests/data/f1_R1.fastq.gz to item 7f09e053-0cee-42ac-aa47-f725adb183d5 was successful.
   Uploading submit_cgap/tests/data/f1_R2.fastq.gz to item 776f1767-cb43-48d1-84dc-90955ce0930a ...
   Going to upload submit_cgap/tests/data/f1_R2.fastq.gz to s3://encoded-4dn-files/776f1767-cb43-48d1-84dc-90955ce0930a/GAPFIXJRIVGO.fastq.gz.
   Uploaded in 0.76 seconds
   Upload of submit_cgap/tests/data/f1_R2.fastq.gz to item 776f1767-cb43-48d1-84dc-90955ce0930a was successful.
   Uploading submit_cgap/tests/data/f2_R1.fastq.gz to item 7c039d90-4072-419b-ae12-7031ea9d4274 ...
   Going to upload submit_cgap/tests/data/f2_R1.fastq.gz to s3://encoded-4dn-files/7c039d90-4072-419b-ae12-7031ea9d4274/GAPFINORP5F5.fastq.gz.
   Uploaded in 0.70 seconds
   Upload of submit_cgap/tests/data/f2_R1.fastq.gz to item 7c039d90-4072-419b-ae12-7031ea9d4274 was successful.
   Uploading submit_cgap/tests/data/f2_R2.fastq.gz to item 4afcf1c7-ebfe-4e96-b272-69f358e43ca0 ...
   Going to upload submit_cgap/tests/data/f2_R2.fastq.gz to s3://encoded-4dn-files/4afcf1c7-ebfe-4e96-b272-69f358e43ca0/GAPFIMK89CF6.fastq.gz.
   Uploaded in 0.72 seconds
   Upload of submit_cgap/tests/data/f2_R2.fastq.gz to item 4afcf1c7-ebfe-4e96-b272-69f358e43ca0 was successful.


Testing show-upload-info
------------------------

If you answer no to the post queries, you'll need to come back to that later and try
again.  To do that, you'll need to either use ``resume-uploads`` (as described above)
or else use ``upload-item-data`` to upload individual files. However, to do that you
will need the guid associated with each file.

That information was in the original successful submission, as here:

   {'uuid': '7f09e053-0cee-42ac-aa47-f725adb183d5', 'filename': 'f1_R1.fastq.gz'}
   {'uuid': '776f1767-cb43-48d1-84dc-90955ce0930a', 'filename': 'f1_R2.fastq.gz'}
   {'uuid': '7c039d90-4072-419b-ae12-7031ea9d4274', 'filename': 'f2_R1.fastq.gz'}
   {'uuid': '4afcf1c7-ebfe-4e96-b272-69f358e43ca0', 'filename': 'f2_R2.fastq.gz'}

But you can also recover it if you have the tracking guid, for example::

   $ show-upload-info c5bdbeee-49f1-4fa7-9e64-bc93f2cb151f -s http://localhost:8000
   ----- Upload Info -----
   {'uuid': '7f09e053-0cee-42ac-aa47-f725adb183d5', 'filename': 'f1_R1.fastq.gz'}
   {'uuid': '776f1767-cb43-48d1-84dc-90955ce0930a', 'filename': 'f1_R2.fastq.gz'}
   {'uuid': '7c039d90-4072-419b-ae12-7031ea9d4274', 'filename': 'f2_R1.fastq.gz'}
   {'uuid': '4afcf1c7-ebfe-4e96-b272-69f358e43ca0', 'filename': 'f2_R2.fastq.gz'}

You could also obtain the information from the ``['additional_data']['upload_info']`` part of::

   http://localhost:8000/ingestion-submissions/c5bdbeee-49f1-4fa7-9e64-bc93f2cb151f/?format=json

If you later resubmit the same metadata bundle, it will try to patch, not post::

   $ submit-metadata-bundle submit_cgap/tests/data/cgap_submit_test.xlsx -s http://localhost:8000
   Submit submit_cgap/tests/data/cgap_submit_test.xlsx to http://localhost:8000? [yes/no]: yes
   The server http://localhost:8000 recognizes you as Kent Pitman <kent_pitman@hms.harvard.edu>.
   Using institution: /institutions/hms-dbmi/
   Using project: /projects/12a92962-8265-4fc0-b2f8-cf14f05db58b/
   02:02:10 Bundle uploaded, assigned uuid 2ac0b2ed-3de9-4e34-b702-930bbdfb3ade for tracking. Awaiting processing...
   02:02:25 Final status: success
   ----- Validation Output -----
   sample 3464467 - Item already in database, no changes needed
   sample 3464468 - Item already in database, no changes needed
   sample 3464469 - Item already in database, no changes needed
   individual 456 - Item already in database, no changes needed
   individual 789 - Item already in database, no changes needed
   individual 123 - Item already in database, no changes needed
   family for 456 - Item already in database, no changes needed
   file_fastq items: 4 validated; 0 errors
   file_processed items: 0 validated; 0 errors
   sample items: 3 validated; 0 errors
   individual items: 3 validated; 0 errors
   family items: 1 validated; 0 errors
   sample_processing items: 1 validated; 0 errors
   report items: 1 validated; 0 errors
   case items: 3 validated; 0 errors
   All items validated.
   ----- Post Output -----
   file_fastq: 4 items patched successfully; 0 items not patched
   ----- Upload Info -----
   {'uuid': '7f09e053-0cee-42ac-aa47-f725adb183d5', 'filename': 'f1_R1.fastq.gz'}
   {'uuid': '776f1767-cb43-48d1-84dc-90955ce0930a', 'filename': 'f1_R2.fastq.gz'}
   {'uuid': '7c039d90-4072-419b-ae12-7031ea9d4274', 'filename': 'f2_R1.fastq.gz'}
   {'uuid': '4afcf1c7-ebfe-4e96-b272-69f358e43ca0', 'filename': 'f2_R2.fastq.gz'}
   Upload 4 files? [yes/no]: no
   No uploads attempted.


Test Files
----------

Note that these commands make use of
various test files in ``submit_cgap/tests/data``.

You can create your own test ``.fastq`` files
by using the ``make-sample-fastq-file`` command.

Getting Help
------------

These scripts should respond to a ``--help`` argument so that
you can learn about their purpose and argument syntax.
