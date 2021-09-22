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

Once ``poetry`` has finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle`` and the ``submit-genelist``
commands.

Metadata Bundles
----------------

For help about arguments, do::

   submit-metadata-bundle --help

However, it should suffice for many cases to specify
the bundle file you want to upload and either a site or a
CGAP beanstalk environment.
For example::

   submit-metadata-bundle mymetadata.xlsx

This command should do everything, including upload referenced files
if they are in the same directory. (It will ask for confirmation.)

To invoke it for validation only, without submitting anything, do::

   submit-metadata-bundle mymetadata.xlsx --validate_only

To specify a different directory for the files, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder

The above command will only look in the directory specified (and not any subdirectories)
for the files to upload. To look in the directory and all subdirectories, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder --subfolders

You can resume execution with the upload part by doing::

   resume-uploads <uuid> --env <env>

or::

   resume-uploads <uuid> --server <server>

You can upload individual files separately by doing::

   upload-item-data <filename> --uuid <item-uuid> --env <env>

or::

   upload-item-data <filename> --uuid <item-uuid> --server <server>

where the ``<item-uuid>`` is the uuid for the individual item, not the metadata bundle.

Normally, for the three commands above, you are asked to verify the files you would like
to upload. If you would like to skip these prompts so the commands can be run by a
scheduler or in the background, you can pass the ``--no_query`` or ``-nq`` argument, such
as::
    
    submit-metadata-bundle mymetadata.xlsx --no_query

Gene Lists
----------

The ``submit-genelist`` command shares similar features with ``submit-metadata-bundle``.
For help about arguments, do::

   submit-genelist --help

and to submit a gene list for validation only, do::

   submit-genelist --validate-only

For most situations, simply specify the gene list you want to upload, e.g.::

   submit-genelist mygenelist.xlsx
