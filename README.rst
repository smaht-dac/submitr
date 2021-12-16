==========
SubmitCGAP
==========


A file submission tool for CGAP
===============================

.. image:: https://travis-ci.org/dbmi-bgm/SubmitCGAP.svg
   :target: https://travis-ci.org/dbmi-bgm/SubmitCGAP
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/dbmi-bgm/SubmitCGAP/badge.svg
   :target: https://coveralls.io/github/dbmi-bgm/SubmitCGAP
   :alt: Coverage

.. image:: https://readthedocs.org/projects/submitcgap/badge/?version=latest
   :target: https://submitcgap.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Description
===========

This is a tool for uploading certain kinds of files to CGAP.

Current support is for "metadata bundles" and "gene lists".
"Metadata bundles" are Excel files (``.xlsx``) accompanied by other files
(such as ``.fastq.gz`` files).
"Gene lists" are either Excel files (``.xlsx``) or plain text (``.txt``) files.


About Metadata Bundles
======================
"Metadata bundles" are Excel files (``.xlsx``) accompanied by other files
(such as ``.fastq.gz`` files).

**Note:**
The format of the Excel files that are used as
"metadata bundles" is not yet documented.
For now you should begin by obtaining a template file from
your contact on the CGAP Team and then customize that as appropriate.

Installation
============

Installing this system involves these steps:

1. Create, install, and activate a virtual environment.
2. Install poetry
3. *Only if you are a developer*, select the source repository.
   Others will not have a source repository to select,
   so should skip this step.
4. If you are an end user, do "``pip install submit_cgap``".
   Otherwise, do "``make build``".
5. Set up a ``~/.cgap-keys.json`` credentials file.

For detailed information about these installation steps, see
`Installing SubmitCGAP <INSTALLATION.rst>`__.


Testing
=======

To run unit tests, do::

   $ make test

Additional notes on testing these scripts for release can be found in
`Testing SubmitCGAP <TESTING.rst>`__.


Getting Started
===============

Once you have finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle`` and the ``submit-genelist``
commands.

Formatting Files for Submission
-------------------------------

There are 3 types of submissions: accessioning (new cases) and family history (pedigrees)
both use the ``submit-metadata-bundle`` command, and gene lists use the ``submit-genelist``
command.

For details on what file formats are accepted and how the information should be structured,
see our submission help pages at `the main CGAP server <https://cgap.hms.harvard.edu/help/submission>`_
or at <your-cgap-server>/help/submission .

Metadata Bundles
----------------

There are two types of submissions that fall under "metadata bundles" - namely,
accessioning (new cases) and family history (pedigrees). The default is accessioning,
if no ingestion_type is specified. If you would like to submit a family history,
make sure the cases are submitted first.

Accessioning
^^^^^^^^^^^^

For help about arguments, do::

   submit-metadata-bundle --help

However, it should suffice for many cases to specify
the bundle file you want to upload and either a site or a
CGAP beanstalk environment.
For example::

   submit-metadata-bundle mymetadata.xlsx --server <server_url>

This command should do everything, including upload referenced files
if they are in the same directory. (It will ask for confirmation.) If you belong to
multiple projects and/or institutions, you can also add the ``--project <project>``
and ``--institution <institution>`` options; if you belong to only one project/institution
in CGAP, the system will automatically detect them.

To invoke it for validation only, without submitting anything, do::

   submit-metadata-bundle mymetadata.xlsx --validate_only --server <server_url>

To specify a different directory for the files, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder --server <server_url>

The above command will only look in the directory specified (and not any subdirectories)
for the files to upload. To look in the directory and all subdirectories, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder --subfolders --server <server_url>

You can resume execution with the upload part by doing::

   resume-uploads <uuid> --env <env>

or::

   resume-uploads <uuid> --server <server_url>

You can upload individual files separately by doing::

   upload-item-data <filename> --uuid <item-uuid> --env <env>

or::

   upload-item-data <filename> --uuid <item-uuid> --server <server_url>

where the ``<item-uuid>`` is the uuid for the individual item, not the metadata bundle.

Normally, for the three commands above, you are asked to verify the files you would like
to upload. If you would like to skip these prompts so the commands can be run by a
scheduler or in the background, you can pass the ``--no_query`` or ``-nq`` argument, such
as::

    submit-metadata-bundle mymetadata.xlsx --no_query

Family History
^^^^^^^^^^^^^^

If, after submitting a case, you would also like to submit a family history for the case,
you use the same command as described above but add the --ingestion_type flag::

    submit-metadata-bundle mypedigree.xlsx --ingestion_type family_history --server <server_url>

Gene Lists
----------

The ``submit-genelist`` command shares similar features with ``submit-metadata-bundle``.
For help about arguments, do::

   submit-genelist --help

and to submit a gene list for validation only, do::

   submit-genelist --validate-only

For most situations, simply specify the gene list you want to upload, e.g.::

   submit-genelist mygenelist.xlsx --server <server_url>
