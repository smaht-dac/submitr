============
Installation
============

.. toctree::
  :maxdepth: 1

More experienced users who already have ``python`` (version ``3.8``, ``3.9``, ``3.10``, or ``3.11``) and ``pip`` installed,
and a (optional) Python virtual environment satisfactorily setup,
can proceed directly to the essential element of the actual installation
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

.. tip::
    If you just want to cut to the chase
    see the `Actual Installation <installation.html#actual-installation>`_ section at the end of this page.


System Requirements
===================

* ``python`` `3.8, 3.9, 3.10, or 3.11`
* ``pip`` `>= 20.0.0`
* ``bash``
* ``virtualenv`` `>= 16.0.0` (`optional`)

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

This step is **optional**.
If you do not create a virtual environment, ``poetry`` will make one for you.
But there are still good reasons you might want to make your own, so here
are three ways to do it:

* If you have a ``virtualenvwrapper`` installation that knows how to use your Python version (3.7, 3.8 or 3.9)::

   mkvirtualenv myenv

* If you have virtualenv but not virtualenvwrapper,
  and you have, for example, ``python3.9`` in your ``PATH``::

   virtualenv myenv -p python3.9

* If you are using ``pyenv`` to control what Python version you use, make sure you have set it
  to your preferred version and then do::

   pyenv exec python -m venv myenv


Virtual Environment Activation 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should execute all actions related to this repository
from within a virtual environment.

To activate a virtual environment::

   source myenv/bin/activate


Virtual Environment Deactivation 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's rarely necessary to deactivate a virtual environment.
One is automatically deactivated if you enter another,
and normally they have very little effect on other actions you might
take. So it's normally safe to just leave them activated.

However, if you want to deactivate an active environment, just do::

   deactivate


For Developers
==============

If you are a software developer, and you wish to install ``smaht-submitr`` locally
for development or other purposes, please see the `Advanced Usage <advanced_usage.html#installation-for-developers>`_ section.


Actual Installation
===================

Assuming ``python`` and ``pip`` is satisfactorily installed,
to actually install the ``submitr-smaht`` software package, do::

   pip install smaht-submitr
