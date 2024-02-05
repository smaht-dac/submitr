.. raw:: html

   <div style="width: 100%; text-align: center;">
     <iframe src="_static/logo.html" style="width: 575px; height: 220px; border: none; margin: 0; padding: 0;" />
      [SMaHT submitr logo]
     </iframe>
   </div>

.. warning::

   **THIS IS A PRE-RELEASE VERSION.** TESTING-123
   Watch for version 1.0.


========
Overview
========

------------------------------------------------
smaht-submitr: A remote file submitter for SMaHT
------------------------------------------------

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

The ``smaht-submitr`` is a command-line tool for uploading files to SMaHT.
It is implemented as Python package and distributed on `PyPi <https://pypi.org/>`_ here: `smaht-submitr <https://pypi.org/project/smaht-submitr/>`_


System Requirements
===================

* ``python`` (>= ``3.8`` and <= ``3.11``) 
* ``pip`` (>= ``22.0.0``)
* ``poetry`` (>= ``1.4.0``)
* ``smaht-portal`` (>= ``1.0.0``)


What To Do Next
===============

Advanced users who have already installed Python
can proceed to instructions for **Installing smaht-submitr**.

Less experienced users should start with instructions
for **Installing Prerequisites**,
which will introduce some basics for working with the terminal
and installing the dependencies to run this package.



.. toctree::
  :maxdepth: 1

  self
  installing_prerequisites
  installation
  credentials
  usage
  submitr
