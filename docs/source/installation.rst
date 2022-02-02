=====================
Installing SubmitCGAP
=====================


Setting Up a Virtual Environment (OPTIONAL)
===========================================

This is optional.
If you use Poetry and do not create a virtual environment, Poetry will make one for you.
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

**End Users:** Submit-CGAP can be installed with a simple pip install::

   pip install submit-cgap

**Developers:** Once you have created a virtual environment, or have decided to just let Poetry handle that,
install with poetry::

   poetry install


Setting Up Credentials
======================

Credentials can be placed in a file named ``~/.cgap-keys.json``. The file format is::

   {"envname1": {"key": ..., "secret": ..., "server": ...}, "envname2": ..., ...}

For most CGAP environments, the envname to use is the part of the url preceding
``.hms.harvard.edu``, such as ``cgap-mgb`` or ``cgap-devtest``.
For end users, reach out to your contact on the CGAP team or at
`cgap-support@hms-dbmi.atlassian.net <mailto:cgap-support@hms-dbmi.atlassian.net>`_
if you're not sure which server you need to submit to.
A typical file might look like below for end users (replace the example environment
and server with your own envname and server)::

    {
        "cgap-main": {
            "key": "some_key",
            "secret": "some_secret",
            "server": "https://cgap-main.hms.harvard.edu"
        }
    }

For developers, the suggested envname to use for local debugging (for developers) is "fourfront-cgaplocal".
You will probably have several keys in your credential file. An example keyfile is shown below.

   {
       "cgap-main": {
           "key": "some_key",
           "secret": "some_secret",
           "server": "https://cgap-main.hms.harvard.edu"
       },
       "fourfront-cgaplocal": {
           "key": "some_other_key",
           "secret": "some_other_secret",
           "server": "http://localhost:8000"
       },
       "cgap-testing": {
           "key": "some_third_key",
           "secret": "some_third_secret",
           "server": "https://cgap-testing.hms.harvard.edu"
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
