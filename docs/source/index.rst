.. image:: /_static/images/submitr-banner.png
    :target: https://pypi.org/project/submitr/
    :alt: SMaHT remote Metadata Submission Tool: submitr
    :align: center

|

.. warning::

   **THIS IS A PRE-RELEASE VERSION.**

   This was recently forked from SubmitCGAP and is not yet ready for normal use.

   Watch for version 1.0.


========
Overview
========

----------------------------------------
submitr: remote file submitter for SMaHT
----------------------------------------

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

This is a tool for uploading files to SMaHT.


System Requirements
===================

* Python 3.7, 3.8 or 3.9
* Pip (>=20.0.0)
* Virtualenv (>=16.0.0)


What To Do Next
===============

Advanced users who have already installed Python
can proceed to instructions for **Installing submitr**.

Less experienced users should start with instructions
for **Installing Prerequisites**,
which will introduce some basics for working with the terminal
and installing the dependencies to run this package.

Although at some point **submitr** might offer the ability to
use **rclone** invisibly, for now it uses **awscli** only.
But we do now experimentally offer some instructions for
**Using rclone instead** at the end of this documentation
in case that's an option you want to pursue.


.. toctree::
  :maxdepth: 4

  self
  installing_prerequisites
  installation
  usage
  submitr
  rclone_instead
