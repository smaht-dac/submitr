.. raw:: html

   <div style="width: 100%; text-align: left; margin-left:-10px">
     <iframe src="_static/logo.html" style="width: 555px; height: 155px; border: none; margin: 0; padding: 0;" />
      [SMaHT submitr logo]
     </iframe>
   </div>

-----------------------------

========
Overview
========

**smaht-submitr**: A metadata and file submission tool for :toplink:`SMaHT Portal <https://data.smaht.org/>`.

.. note::
   You need a SMaHT account to use this software. For information on obtaining an account please see the
   `SMaHT Portal Account Creation <account_creation.html>`_ page. See the `About <about.html>`_ page 
   for more general information about this tool and the SMaHT project.

.. .. image:: https://github.com/smaht-dac/submitr/actions/workflows/main.yml/badge.svg
..     :target: https://github.com/smaht-dac/submitr/actions
..     :alt: Build Status

.. .. image:: https://coveralls.io/repos/github/smaht-dac/submitr/badge.svg
..     :target: https://coveralls.io/github/smaht-dac/submitr
..     :alt: Coverage Percentage

.. .. image:: https://readthedocs.org/projects/submitr/badge/?version=latest
..     :target: https://submitr.readthedocs.io/en/latest/?badge=latest
..     :alt: Documentation Status


Description
===========

The :boldcode:`smaht-submitr` software is a command-line tool for importing and uploading
metadata and files into the :toplink:`SMaHT Portal <https://data.smaht.org/>`.
It is implemented as Python package and distributed on :toplink:`PyPi <https://pypi.org/>`
here: :toplink:`smaht-submitr <https://pypi.org/project/smaht-submitr/>`.
This document explains how to get up and running with the use of this tool.

.. raw:: html

    For more information about this software and the SMaHT project see: <strong><a href="about.html">About</a></strong>
    <br /> <br />

.. tip::
    This documentation covers the `mechanics` of using ``smaht-submitr``.
    It does not at this time cover the `semantics` of the metadata;
    though there is an `Object Model <object_model.html>`_ reference.
    For more information on this aspect of submission please see: **TBD**


System Requirements
===================

* ``python`` `3.9, 3.10, or 3.11`

.. note::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these should be generally applicable (with some modifications);
    presumed to be a bit more advanced, such users should have little difficulty.
    For **Windows** users, very little testing has been done; not recommended; but more experienced users should be able to work through it.


What To Do Next
===============

More experienced users who already have Python installed
to their satisfaction can proceed to instructions for `Installation <installation.html>`_.

Less experienced users should start with instructions
for `Installation Prerequisites <installation_prerequisites.html>`_,
which will introduce some basics for working with the terminal
and installing the dependencies for this tool:

* `Installation Prerequisites <installation_prerequisites.html>`_

.. toctree::
  :maxdepth: 1
  :caption: General  ℹ️

  self
  about

.. toctree::
  :caption: Setup  ⚙️
  :maxdepth: 1

  installation
  account_creation
  credentials

.. toctree::
  :caption: Documentation  📄
  :maxdepth: 1

  usage
  uploading_files
  advanced_usage

.. toctree::
  :caption: Reference 🔍
  :maxdepth: 1

  consortia
  submission_centers
  file_formats
  object_model
