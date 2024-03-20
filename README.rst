
.. image:: https://staging.smaht.org/static/img/docs/submitr_logo.png
    :target: https://pypi.org/project/smaht-submitr/
    :alt: SMaHT remote Metadata Submission Tool: submitr
    :align: left


|


------------

==============
smaht-submitr
==============


A file submission tool for SMaHT
================================

.. image:: https://github.com/smaht-dac/submitr/actions/workflows/main.yml/badge.svg
   :target: https://github.com/smaht-dac/submitr/actions
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/smaht-dac/submitr/badge.svg
    :target: https://coveralls.io/github/smaht-dac/submitr
    :alt: Coverage Percentage

.. image:: https://readthedocs.org/projects/submitr/badge/?version=draft
   :target: https://submitr.readthedocs.io/en/draft/?badge=draft
   :alt: Documentation Status


Description
===========

This is a tool for uploading certain kinds of files to SMaHT.
The "R" is for Remote file submission. You can think of this tool as putting the "R" in "SMaHT". :)

Please see our detailed documentation here: `SMaHT Submitr <https://submitr.readthedocs.io/en/draft/>`_


Background
==========

This tool was forked from SubmitCGAP and will probably remain compatible, but by forking it, the original repository will remain stable and this new repository can experiment safely.

Because SubmitCGAP supported submission of new cases, family histories, and gene lists, that's what this begins with. But that doesn't imply that those things are present in SMaHT. The protocol is designed to require both ends to agree on the availability of a particular kind of upload for it to happen.


Installation
============

Installing this system involves these steps:

1. Install Python and optionally a virtual environment manager of your choice (e.g. ``pyenv``)..
2. Install this package with: ``pip install smaht-submitr``
3. Setup your SMaHT Portal credentials file: ``~/.smaht-keys.json``. See `SMaHT Submitr Credentials <https://submitr.readthedocs.io/en/draft/installation.html>`_ for more in this.

See detailed information about installation see: `Installing SMaHT Submitr <https://submitr.readthedocs.io/en/draft/installation.html>`_.


Getting Started
===============

Once you have finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle``, ``resume-uploads``, and ``check-submissions``
commands. For more information about how to format files for submission and how to
use these commands, see `Getting Started with SMaHT Submitr <https://submitr.readthedocs.io/en/draft/usage.html>`_.
