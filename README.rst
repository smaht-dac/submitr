
.. image:: docs/source/_static/images/submitr-banner.png
    :target: https://pypi.org/project/submitr/
    :alt: SMaHT remote Metadata Submission Tool: submitr
    :align: center

|

**THIS IS A PRE-RELEASE VERSION.**

This was recently forked from SubmitCGAP and is not yet ready for normal use.

Watch for version 1.0.

------------

=======
submitr
=======


A file submission tool for SMAHT
================================

.. image:: https://github.com/smaht-dac/submitr/actions/workflows/main.yml/badge.svg
   :target: https://github.com/smaht-dac/submitr/actions
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/smaht-dac/submitr/badge.svg
    :target: https://coveralls.io/github/smaht-dac/submitr
    :alt: Coverage Percentage

.. image:: https://readthedocs.org/projects/submitr/badge/?version=latest
   :target: https://submitr.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status


Description
===========

This is a tool for uploading certain kinds of files to SMaHT.

The "R" is for Remote file submission. You can think of this tool as putting the "R" in "SMaHT". :)


Background
==========

This tool was forked from SubmitCGAP and will probably remain compatible, but by forking it, the original repository will remain stable and this new repository can experiment safely.

Because SubmitCGAP supported submission of new cases, family histories, and gene lists, that's what this begins with. But that doesn't imply that those things are present in SMaHT. The protocol is designed to require both ends to agree on the availability of a particular kind of upload for it to happen.


Installation
============

Installing this system involves these steps:

1. Create, install, and activate a virtual environment.
2. *Only if you are a developer*, install poetry and select the source repository.
   Others will not have a source repository to select,
   so should skip this step.
3. If you are an end user, do "``pip install submitr``".
   Otherwise, do "``make build``".
4. Set up a ``~/.smaht-keys.json`` credentials file.

See detailed information about these installation steps at
`Installing submitr <https://submitr.readthedocs.io/en/latest/installation.html>`_.



Testing
=======

To run unit tests, do::

   $ make test

Additional notes on testing these scripts for release can be found in
`Testing submitr <TESTING.rst>`__.


Getting Started
===============

Once you have finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle`` and the ``submit-genelist``
commands. For more information about how to format files for submission and how to
use these commands, see `Getting Started <https://submitr.readthedocs.io/en/latest/getting_started.html>`_.
