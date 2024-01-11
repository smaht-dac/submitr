==================
Installing submitr
==================


System Requirements
===================

* Python 3.8, 3.9, 3.10, or 3.11
* ``pip`` (>=20.0.0)
* ``virtualenv`` (>=16.0.0)
* ``poetry`` (>=1.4.0)


Setting Up a Virtual Environment (OPTIONAL)
===========================================

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
go ahead with the installation. To do that, make sure your current directory is the source repository and do::

   make build


.. tip::

   Poetry is the substrate that our build scripts rely on.
   You won't be calling it directly, but ``make build`` will call it.


Installation for End Users (non-Developers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're an end user,
once you have created and activated the virtual environment,
just do::

   pip install submitr


Setting Up Credentials
======================

Credentials can be placed in the file ``~/.smaht-keys.json`` which looks like this::

   {
       "smaht-staging": {
           "key": "your-portal-key",
           "secret": "your-portal-secret",
           "server": "https://data.smaht.org"
       },
       "smaht-data": {
           "key": "your-portal-key",
           "secret": "your-portal-secret",
           "server": "https://data.smaht.org"
       },
       "smaht-local": {
           "key": "your-local-portal-key",
           "secret": "your-local-portal-secret",
           "server": "http://localhost:8000"
       }
   }

The easiest way to create or modify a file like this is with TextEdit, which you can open from a MacOS Terminal window with:

The environment names there are of your own choosing; this name will be used
as the ``--env`` argument to the various `submitr` commands, e.g. ``submit-metadata-bundle`` and ``resume-uploads``.
If you're not sure which server you should be submitting to, reach out to your contact on the SMaHT DAC Team.

The ``key`` and ``secret`` values are obtained from the `Access Keys` sections of the SMaHT Portal `My Profile` page.

A typical key file might look like the below. If you are not a developer, you will probably
only have one key rather than several, and almost certainly none of the URLs will be on ``localhost``::

.. code-block::

    $ open -a TextEdit ~/.cgap-keys.json

This file should _not_ be readable by others than yourself.
Set its permissions accordingly by using ``chmod 600``,
which sets the file to be readable and writable only by yourself,
and to give no one else (but the system superuser) any permissions at all::

   $ ls -dal ~/.smaht-keys.json
   -rw-r--r--  1 smahtuser  staff  297 Sep  4 13:14 /Users/smahtuser/.smaht-keys.json

   $ chmod 600 ~/.smaht-keys.json

   $ ls -dal ~/.smaht-keys.json
   -rw-------  1 smahtuser  staff  297 Sep  4 13:14 /Users/smahtuser/.smaht-keys.json

