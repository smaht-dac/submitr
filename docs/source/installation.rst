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

Less experienced users may want to start with these `prerequisites <installation_prerequisites.html>`_,
which will introduce some basics for installing and working
with Python on the terminal command-line:

.. toctree::
  :maxdepth: 1

  installation_prerequisites

The rest of these instructions will guide you through the setup of a (optional)
virtual Python environment, and then the actual installation of ``smaht-submitr``.

.. tip::
   You need an SMaHT account to use this software. For information an obtaining an account please see:
   `SMaHT Portal Account Creation <account_creation.html>`_

System Requirements
===================

* ``python`` `3.8, 3.9, 3.10, or 3.11`
* ``bash``

.. note::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these should be generally applicable (with some modifications);
    presumed to be a bit more advanced, such users should have little difficulty.
    For **Windows** users, very little testing has been done; not recommended; but more experienced users should be able to work through it.

.. note::
   The command-line shell for all of these instructions is assumed ``bash`` (i.e. not ``zsh`` or ``csh`` et cetera).
   To invoke the ``bash`` shell from the command-line simply run ``bash``.

Virtual Environment Setup
=========================

This step is **optional** though recommended.
See the `Installation Prerequisites <installation_prerequisites.html#installing-pyenv>`_ section for
installing the ``pyenv`` command required to do this.

Assuming you have ``pyenv`` installed (per that `section <installation_prerequisites.html#installing-pyenv>`_),
to install a Python version (3.11.8),
create a virtual Python environment using this Python version,
and active this virtual environment, do::

    pyenv install 3.11.8
    pyenv virtualenv 3.11.8 smaht-submitr-3.11
    pyenv activate smaht-submitr-3.11

That name ``smaht-submitr-3.11`` can be any name that you choose.
Now you can proceed to the actual installation of ``smaht-submitr``, next.

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
