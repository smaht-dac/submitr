===========
Credentials
===========

If you have been designated as a submitter for the SMaHT project,
and plan to use spreadsheet-based submission system (i.e. ``smaht-submitr``)
to view, upload, create, or update data from/to SMaHT Portal,
you are required to obtain and setup an access and secret key (i.e. `credentials`)
from SMaHT Portal.

These SMaHT Portal credentials must stored in a specific format in a special file on your local system.
Please follow these steps below to get your access keys and configure your local system for ``smath-submitr`` usage.

Obtaining Access Keys
---------------------

#. Log in to `SMaHT Portal <https://data.smaht.org>`_ with your username (email) and password.
#. Once logged in, go to your **Profile** page by clicking **Account** on the upper right corner of the page.
#. On your profile page, click the green **Add Access Key** button, and copy the **Access Key ID** and **Secret Access Key** values from the pop-up page.
#. Store these values the file ``~/.smaht-keys.json`` on your local machine. See the next section for details of this file and its format.

.. note::
   Once the pop-up page with your Access Key ID and Secret Access Key disappears, you will `not` be able to retrieve the Secret Access Key value ever again.
   However, if you forget or lose your Secret Access Key you can delete the key and add a new one from your Profile page at any time.

Storing Access Keys
-------------------

Once you've obtained access and secret keys (per the previous) section,
they should be stored in a file on your local machine called ``~/.smaht-keys.json``.
(Note that the ``~`` there refers to your local home directory).

.. tip::
   You can actually use any file rather than ``~/.smaht-keys.json`` to store your credentials.
   If you do, you will need to use the ``--keys`` options with the path to your alternate file as an argument,
   when using the ``smaht-submitr`` commands.

The format of this file requires a single `JSON <https://en.wikipedia.org/wiki/JSON>`_
object, where each property is an `environment` name (of your choosing), and where its value is
an object containing a ``key``, ``secret``, and ``server`` values, represening your Access Key ID,
Secret Access Key, and the target SMaHT server URL. For example:

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

Obviously you would replace ``<your-access-key-id>`` and ``<your-secret-access-key>``
with your actual Access Key ID and Secret Access Key values obtained from SMaHT Portal **Add Access Key** step described above.

To create or modify and edit this file, use a text editor of your choice (``vim`` or ``TextEdit`` or whatever).
For example, using ``TextEdit``, from a MacOS Terminal window, like this:

.. code-block::

    $ open -a TextEdit ~/.smaht-keys.json

As stated above, the environment name, e.g. ``data`` in the above example,
is of your own choosing; this name should be used as the ``--env`` argument
to the various `smaht-submitr` commands, e.g. ``submit-metadata-bundle`` and ``resume-uploads``.

.. tip::
    If you only have `one` single environment defined in this ``~/.smaht-keys.json`` file
    then the ``--env`` argument will not be necessary when using the ``smaht-submit`` commands.

N.B. If you are not sure what ``server`` you should be submitting to,
please reach out to your contact on the SMaHT DAC Team at
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.

Securing Access Keys
--------------------

For extra security, it is wise to make this file unreadable by others than yourself.
Set its permissions accordingly by using ``chmod 600`` command,
which sets the file to be readable and writable only by you,
and gives no one else (but the system superuser) any permissions at all::

   $ ls -l ~/.smaht-keys.json
   -rw-r--r--  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json

   $ chmod 600 ~/.smaht-keys.json

   $ ls -l ~/.smaht-keys.json
   -rw-------  1 youruser  staff  137 Jan 31 08:55 /Users/youruser/.smaht-keys.json
