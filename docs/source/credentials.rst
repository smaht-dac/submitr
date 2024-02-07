=============================
Credentials for smaht-submitr
=============================

If you have been designated as a submitter for the project,
and plan to use spreadsheet-based submission system (``smaht-submitr``)
to view, upload, create, or update data from/to the SMaHT data portal,
you are required to obtain and setup an access and secret key from the SMaHT data portal.
These must stored in a specific format and file on your local system.
Please follow these steps below to get your access keys and configure your local system for ``smath-submitr`` usage.

Obtaining SMaHT Portal Access Keys
----------------------------------

#. Log in to the SMaHT `website <https://data.smaht.org>`_ with your username (email) and password.
#. Once logged in, go to your **Profile** page by clicking **Account** on the upper right corner of the page.
#. On your profile page, click the green **Add Access Key** button, and copy the **Access Key ID** and **Secret Access Key** values from the popup page. Note that *once the pop-up page disappears you will not be able to see the secret access key value*. However if you forget/lose your secret key you can always delete and add new access keys from your profile page at any time.
#. Store these values the file ``~/.smaht-keys.json`` on your local machine; see the next section for details.

Storing SMaHT Portal Access Keys
--------------------------------

Once you've obtained access and secret keys (per the previous) section,
they should be stored in a file on your local machine called ``~/.smaht-keys.json``.
(Note that the ``~`` there refers to your local home directory).
The format of this file should look like this:

.. code-block::

   {
       "data": {
           "key": "<your-access-key-id>",
           "secret": "<your-secret-access-key>",
           "server": "https://data.smaht.org"
       },
       "staging": {
           "key": "<your-access-key-id>",
           "secret": "<your-secret-access-key>",
           "server": "https://staging.smaht.org"
       }
   }

To create or modify and edit this file, use a text editor of your choice (``vim`` or ``TextEdit`` or whatever).
For example, using ``TextEdit``, from a MacOS Terminal window, like this:

.. code-block::

    $ open -a TextEdit ~/.smaht-keys.json

The environment name, e.g. ``data`` in the above example, is of your own choosing; this name will be used
as the ``--env`` argument to the various `smaht-submitr` commands, e.g. ``submit-metadata-bundle`` and ``resume-uploads``.
Though if you only have one environment defined in this file then this (``-env`` argument) will not be necessary.

N.B. If you are not sure what ``server`` you should be submitting to, reach out to your contact on the SMaHT DAC Team.

Securing SMaHT Portal Access Keys
---------------------------------

For extra security, this file should **not** be readable by others; only yourself.
Set its permissions accordingly by using ``chmod 600``,
which sets the file to be readable and writable only by yourself,
and gives no one else (but the system superuser) any permissions at all::

   $ ls -l ~/.smaht-keys.json
   -rw-r--r--  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json

   $ chmod 600 ~/.smaht-keys.json

   $ ls -l ~/.smaht-keys.json
   -rw-------  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json
