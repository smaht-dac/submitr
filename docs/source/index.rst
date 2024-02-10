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

**smaht-submitr**: A metadata and file submission tool for `SMaHT Portal <https://data.smaht.org/>`_.

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

The ``smaht-submitr`` software is a command-line tool for importing and uploading metadata and files into the `SMaHT Portal <https://data.smaht.org/>`_.
It is implemented as Python package and distributed on `PyPi <https://pypi.org/>`_ here: `smaht-submitr <https://pypi.org/project/smaht-submitr/>`_.


System Requirements
===================

* ``python`` `3.8, 3.9, 3.10, or 3.11`
* ``pip`` `>= 20.0.0`
* ``poetry`` `>= 1.4.0` (`optional`)


What To Do Next
===============

More advanced users who already have `Python` installed
can proceed to instructions for `Installation <installation.html>`_.

Less experienced users should start with instructions
for `Installion Prerequisites <installing_prerequisites.html>`_,
which will introduce some basics for working with the terminal
and installing the dependencies to run this tool.



.. toctree::
  :maxdepth: 1

  self
  installation
  credentials
  usage
  uploading_files
  advanced_usage
  submitr
