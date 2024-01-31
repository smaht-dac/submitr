=============================
Credentials for smaht-submitr
=============================

Credentials can be placed in the file ``~/.smaht-keys.json`` which typically looks something like this::

   {
       "data": {
           "key": "your-portal-key",
           "secret": "your-portal-secret",
           "server": "https://data.smaht.org"
       },
       "staging": {
           "key": "your-portal-key",
           "secret": "your-portal-secret",
           "server": "https://staging.smaht.org"
       }
   }

Create or modify a file using the text editor of your choice (``vim`` or ``TextEdit`` or whatever),
for example, using ``TextEdit`` you can do it like can open or create this file from a MacOS Terminal window with:

.. code-block::

    $ open -a TextEdit ~/.smaht-keys.json

The environment names (e.g. ``data``) there are of your own choosing; this name will be used
as the ``--env`` argument to the various `smaht-submitr` commands, e.g. ``submit-metadata-bundle`` and ``resume-uploads``.
If you're not sure which ``server`` you should be submitting to, reach out to your contact on the SMaHT DAC Team.

The ``key`` and ``secret`` values are obtained from the `Access Keys` sections of the SMaHT Portal `My Profile` page.

This file should **not** be readable by others than yourself.
Set its permissions accordingly by using ``chmod 600``,
which sets the file to be readable and writable only by yourself,
and to give no one else (but the system superuser) any permissions at all::

   $ ls -l ~/.smaht-keys.json
   -rw-r--r--  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json

   $ chmod 600 ~/.smaht-keys.json

   $ ls -l ~/.smaht-keys.json
   -rw-------  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json

