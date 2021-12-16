=====================
Installing SubmitCGAP
=====================


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


Setting Up Credentials
======================

Credentials can be placed in the file ``~/.cgap-keydicts.json``. The file format is::

   {"envname1": {"key": ..., "secret": ..., "server": ...}, "envname2": ..., ...}

   The envname to use for the main CGAP server is "fourfront-cgap".
   The envname to use for local debugging is "fourfront-cgaplocal".
   Reach out to your contact on the CGAP team if you're not sure which server you
   need to submit to.
   So a typical file might look like below (if you are not a developer, you will probably
   only have one key rather than several):

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

   $ ls -dal ~/.cgap-keydicts.json
   -rw-r--r--  1 jqcgapuser  staff  297 Sep  4 13:14 /Users/jqcgapuser/.cgap-keydicts.json

   $ chmod 600 ~/.cgap-keydicts.json

   $ ls -dal ~/.cgap-keydicts.json
   -rw-------  1 jqcgapuser  staff  297 Sep  4 13:14 /Users/jqcgapuser/.cgap-keydicts.json
