============
Installation
============

.. toctree::
  :maxdepth: 1

More experienced users who already have ``python`` (version ``3.8``, ``3.9``, ``3.10``, or ``3.11``) installed,
and a (optional) Python virtual environment setup to their satisfaction,
may proceed directly to the essential element of the actual installation
of the ``smaht-submitr`` installation, which is simply::

    pip install smaht-submitr

Less experienced users may want to start with the following,
which will introduce some basics for installing and working
with Python (including dependencies) on the terminal command-line:

.. toctree::
  :maxdepth: 1

  installation_prerequisites

You can then proceed with the rest of these instructions
to setup a virtual Python environment.

System Requirements
===================

* ``python`` `3.8, 3.9, 3.10, or 3.11`
* ``bash``

.. warning::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these instructions should be generally applicable (with some modifications),
    and such users, who are presumed to be a bit more advanced, should have no great difficulty.
    For **Windows** users, little to no testing has been done; Windows specific instructions may be available in the future.

.. note::
   The command-line shell for all of these instructions is assumed ``bash`` (i.e. not ``zsh`` or ``csh`` et cetera).
   To invoke the ``bash`` shell from the command-line simply run ``bash``.

Virtual Environment Setup
=========================

This step is **optional** though recommended.
See the `Installation Prerequisites <installation_prerequisites.html>`_ section for
installing the ``pyenv`` command required to do this.
Assuming you have ``pyenv`` installed (per that section),
to create a virtual Python environment with version 3.11.6 of Python, do::

    pyenv install 3.11.6
    pyenv virtualenv 3.11.6 smaht-submitr-3.11

That name ``smaht-submitr-3.11`` can actually be any name that you choose.
To activate this virtual environment, do::

    pyenv activate smaht-submitr-3.11

Now you can proceed to actually install ``smaht-submitr``, next.

Actual Installation
===================

Assuming ``python`` is satisfactorily installed,
to install the ``submitr-smaht`` software package, do::

   pip install smaht-submitr

(Note that the ``pip`` command is automatically installed with ``python``).

For Developers
==============

If you are a software developer, and you wish to install ``smaht-submitr`` locally
for development or other purposes, please see the `Advanced Usage <advanced_usage.html#installation-for-developers>`_ section.
