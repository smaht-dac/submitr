=====================
Installing SubmitCGAP
=====================


System Requirements
===================

* Python 3.6 or 3.7
* ``pip`` (version 20 or higher)
* ``virtualenv`` (version 16 or higher)


Setting Up a Virtual Environment (OPTIONAL)
===========================================

This action is optional.
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


Installing in a Virtual Environment
==========================================

Installation for Developers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are a developer, you'll be installing with Poetry.
Once you have created a virtual environment, or have decided to just let Poetry handle that,
install with poetry, make sure your current directory is the source repository and do::

   poetry install


Installation for End Users (non-Developers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're an end user,
once you have created and activated the virtual environment,
just do::

   pip install submit_cgap


Setting Up Credentials
======================

Credentials can be placed in the file ``~/.cgap-keys.json``. The file format is::

   {"envname1": {"key": ..., "secret": ..., "server": ...}, "envname2": ..., ...}

   The envname to use for production is "fourfront-cgap".
   The envname to use for local debugging is "fourfront-cgaplocal".
   So a typical file might look like:

   {
       "fourfront-cgap": {
           "key": "some_key",
           "secret": "some_secret",
           "server": "https://cgap.hms.harvard.edu"
       },
       "fourfront-local": {
           "key": "some_other_key",
           "secret": "some_other_secret",
           "server": "http://localhost:8000"
       },
       "fourfront-cgapdev": {
           "key": "some_third_key",
           "secret": "some_third_secret",
           "server": "http://fourfront-cgapdev.9wzadzju3p.us-east-1.elasticbeanstalk.com/"
       }
   }

This file should _not_ be readable by others than yourself.
Set its permissions accordingly by using ``chmod 600``,
which sets the file to be readable and writable only by yourself,
and to give no one else (but the system superuser) any permissions at all::

   $ ls -dal ~/.cgap-keys.json
   -rw-r--r--  1 jqcgapuser  staff  297 Sep  4 13:14 /Users/jqcgapuser/.cgap-keys.json

   $ chmod 600 ~/.cgap-keys.json

   $ ls -dal ~/.cgap-keys.json
   -rw-------  1 jqcgapuser  staff  297 Sep  4 13:14 /Users/jqcgapuser/.cgap-keys.json


