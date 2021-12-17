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

Current support is for submission of new cases, family histories, and gene lists.


Installation
============

Installing this system involves these steps:

1. Create, install, and activate a virtual environment.
2. *Only if you are a developer*, install poetry and select the source repository.
   Others will not have a source repository to select,
   so should skip this step.
3. If you are an end user, do "``pip install submit_cgap``".
   Otherwise, do "``make build``".
4. Set up a ``~/.cgap-keys.json`` credentials file.

For detailed information about these installation steps, see
`Installing SubmitCGAP <https://submitcgap.readthedocs.io/en/latest/installation.html>`_.


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
commands. For more information about how to format files for submission and how to
use these commands, see `Getting Started <https://submitcgap.readthedocs.io/en/latest/getting_started.html>`_.
