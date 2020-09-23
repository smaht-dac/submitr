==========
SubmitCGAP
==========


A file submission tool for CGAP
-------------------------------

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

Initial support is for "metadata bundles", which are Excel files
(such as .xls or .xlsx files)
that are accompanied by other files (such as ``.fastq.gz`` files).


About Metadata Bundles
======================

.. note::

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
you should have access to the ``submit-metadata-bundle`` command.
For help about its arguments, do::

   submit-metadata-bundle --help

However, it should suffice for many cases to specify
the bundle file you want to upload and either a site or a
CGAP beanstalk environment.
For example::

   submit-metadata-bundle mymetadata.xls

This command should do everything, including upload referenced files
if they are in the same directory. (It will ask for confirmation.)

To invoke it for validation only, without submitting anything, do::

   submit-metadata-bundle mymetadata.xls --validate_only

You can resume execution with the upload part by doing::

   resume-uploads <uuid> --env <env>

or::

   resume-uploads <uuid> --server <server>

You can upload individual files separately by doing::

   upload-item-data <filename> --uuid <item-uuid> --env <env>

or::

   upload-item-data <filename> --uuid <item-uuid> --server <server>

where the ``<item-uuid>`` is the uuid for the individual item, not the metadata bundle.
