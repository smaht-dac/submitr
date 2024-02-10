============
Installation
============

.. toctree::
  :maxdepth: 1

More experienced users who already have ``python`` (version ``3.8``, ``3.9``, ``3.10``, or ``3.11``) and ``pip`` installed,
and a (optional) virtual Python environment satisfactorily setup,
can proceed directly to the actual essential
element of the ``smaht-submitr`` installation, which is simply this::

    pip install smaht-submitr

Less experienced users may want to start with instructions
for `Installation Prerequisites <installation_prerequisites.html>`_,
which will introduce some basics for working with Python on the terminal
command-line, and installing dependencies to run this tool,
before continuing on with these instructions.

If you do not yet and would like have
a virtual Python environment setup,
proceed with the rest of these instructions;
otherwise you may want to cut to the chase and
see the `Actual Installation <installation.html#actual-installation>`_ section below.


System Requirements
===================

* ``python`` `3.8, 3.9, 3.10, or 3.11`
* ``pip`` `>= 20.0.0`
* ``poetry`` `>= 1.4.0` (`optional`)
* ``virtualenv`` `>= 16.0.0` (`optional`)


Virtual Environment Setup ( `Optional` )
----------------------------------------

This action is optional.
If you do not create a virtual environment, Poetry will make one for you.
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


Installation for Developers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are a developer, you'll be installing via ``poetry``.
Once you have created a virtual environment, or have decided to just let ``poetry`` handle that,
go ahead with the installation. To do that, make sure your current directory is the source repository and do::

   git clone https://github.com/smaht-dac/submitr.git
   cd submitr
   make build


Note that ``poetry`` is the substrate that our build scripts rely on.
You won't be calling it directly, but ``make build`` will call it.


Actual Installation
===================

To actually install the ``submitr-smaht`` software package::

   pip install smaht-submitr
