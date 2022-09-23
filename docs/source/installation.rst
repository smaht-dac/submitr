=====================
Installing SubmitCGAP
=====================


Setting Up a Virtual Environment (OPTIONAL)
===========================================

This is optional. See also the basic setup instructions for doing this setup with `pyenv`
If you use Poetry and do not create a virtual environment, Poetry will make one for you.
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

Installing SubmitCGAP in a Virtual Environment
==============================================

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

The easiest way to modify this file is with TextEdit, which you can open from the Terminal with:

.. code-block::

    $ open -a TextEdit ~/.cgap-keys.json

For developers, the suggested envname to use for local debugging (for developers) is "fourfront-cgaplocal".
You will probably have several keys in your credential file. An example keyfile is shown below
(note that the CGAP servers used are just example urls)::

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


Generating Credentials
======================

Access keys for using SubmitCGAP are generated from the Web UI. Upon logging in, there is a user profile
in the top right corner - select it and from the drop down navigate to profile. Once on your user profile
there is an Access Keys box where you can add an access key. Click the green "Add Access Key" button and
a pop up will show up with the ID and Secret. Copy these into your `~/.cgap-keys.json` file and SubmitCGAP
will automatically detect and use them. You will need to reset the credential every 90 days as after that
time the key will expire.
