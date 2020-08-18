===========
submit-cgap
===========

File submission for CGAP
------------------------


.. Note::

 Badges go here. Later.


Description
===========

This is a tool for uploading files to CGAP.


System Requirements
===================

* Python 3.6
* Pip (Any should work)
* Virtualenv (>=15.0.0)

Setting Up a Virtual Environment (OPTIONAL)
===========================================

This is optional.
If you do not create a virtual environment, Poetry will make one for you.
But there are still good reasons you might want to make your own, so here
are three ways to do it:

* If you have virtualenvwrapper that knows to use Python 3.6::

   mkvirtualenv myenv

* If you have virtualenv but not virtualenvwrapper,
  and you have python3.6 in your ``PATH``::

   virtualenv myenv -p python3.6

* If you are using ``pyenv`` to control what environment you use::

   pyenv exec python -m venv myenv


Activating a Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should execute all actions related to this repository
from within a virtual environment.

To activate a virtual environment::

   source myenv/bin/activate


Deactivating a Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's rarely necessary to deactivate a virtual environment.
One is automatically deactivated if you enter another,
and normally they have very little effect on other actions you might
take. So it's normally safe to just leave them activated.

However, if you want to deactivate an active environment, just do::

   deactivate

Installing Poetry in a Virtual Environment
==========================================

Once you have created a virtual environment, or have decided to just let Poetry handle that,
install with poetry::

   poetry install


Getting Started
===============

Once Poetry is installed, you should have access to the
``submit-metadata-bundle`` command.
For help about its arguments, do::

   submit-metadata-bundle --help

However, it should suffice for many cases to specify
the bundle file you want to upload and either a site or a
CGAP beanstalk environment.
For example::

   submit-metadata-bundle mymetadata.xls

This command will do everything except upload files.
To upload each of those, you will also need to do::

   upload-bundle-data <filename>

(In the future, the ``submit-metadata-bundle`` command might
do this as well.)
