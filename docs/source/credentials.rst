===========
Credentials
===========

In order to use the SMaHT submission tool (``smaht-submitr``)
you are required to obtain and setup an access and secret key (i.e. `credentials`)
using your SMaHT Portal account. This is what allows ``smaht-submitr`` to "talk to" SMaHT Portal on your behalf.

These SMaHT Portal credentials must stored in a specific format in a special file on your local system.
Please follow these steps below to get your access keys and configure your local system for ``smath-submitr`` usage.

.. note::
   You need a SMaHT account to use this software. For information an obtaining an account please see:
   `SMaHT Portal Account Creation <account_creation.html>`_

Obtaining Access Keys
---------------------

#. Log in to :toplink:`SMaHT Portal <https://data.smaht.org>` with your username (email) and password. (See `Account Creation <account_creation.html>`_ for getting an account).
#. Once logged in, go to your **Profile** page by clicking **Account** on the upper right corner of the page.
#. On your profile page, click the green **Add Access Key** button, and copy the **Access Key ID** and **Secret Access Key** values from the pop-up page.
#. Store these values the file ``~/.smaht-keys.json`` on your local machine. See the next section for details of this file and its format.

.. note::
   Once the pop-up page with your Access Key ID and Secret Access Key disappears, you will `not` be able to retrieve the Secret Access Key value ever again.
   `However`, if you forget or lose your Secret Access Key you can delete the key and add a new one from your Profile page at any time.

Storing Access Keys
-------------------

Once you've obtained access and secret keys (per the previous) section,
they should be stored as :toplink:`JSON <https://en.wikipedia.org/wiki/JSON>`
in a `keys file` on your local machine called ``~/.smaht-keys.json``.
(Note that the ``~`` there refers to your local home directory).
To use a different file see the `Some Tips <#id1>`_ section below.

The format of this file requires a single JSON object,
where each property is an **environment name** (of your choosing), and where its value is
an object containing ``key``, ``secret``, and ``server`` values, represening your Access Key ID,
Secret Access Key, and the target SMaHT server URL. For example:

.. code-block::
   :linenos:


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
in the above with your actual **Access Key ID** and **Secret Access Key** values
obtained from the SMaHT Portal **Add Access Key** step described above.
If you're unsure what ``server`` you should be submitting to,
please reach out to your contact on the SMaHT DAC Team at
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.

To create or modify and edit this file, use a text editor of your choice (``vim`` or ``TextEdit`` or whatever).
For example, using ``TextEdit``, from a MacOS Terminal window, like this::

    open -a TextEdit ~/.smaht-keys.json

As stated above, the environment name, e.g. ``data`` in the above example,
is of your own choosing.
And it is **important** to note that this name needs to be used as an argument to the  ``--env`` option
for the various ``smaht-submitr`` commands, for example::

    submit-metadata-bundle --env data your_metadata_file.xlsx


Some Tips
~~~~~~~~~
You can actually use `any` file rather than ``~/.smaht-keys.json`` to store your credentials;
its name `must` but suffixed with ``.json``.
If you do this, you'll need to use the ``--keys`` option, with the path to your file as an argument,
when using the ``smaht-submitr`` commands.
If you want to `avoid` having to specify the ``--keys`` option,
can use an environment variable to set your file, like this::

    export SMAHT_KEYS=/path-to-your-keys-file.json

If you only have `one` single environment defined in your keys file
then the ``--env`` argument will `not` be necessary when using the ``smaht-submit`` commands.

If you have `more` than one environment defined in your keys file,
and you want to avoid having to specify the ``--env`` option for the ``smaht-submitr`` commands, you can
can use an environment variable to set your preferred environment name, like this::

    export SMAHT_ENV=data

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

.. caution::
    Please be careful with your **Secret Access Key** value.
    This is **sensitive** information and, like a password, it should **never** be
    **shared** with anyone, and particularly through any insecure channels (like email or Slack or whatever).

.. note::
    If you `do` accidentally expose your **Secret Access Key**, we would ask you to please
    delete it and create a new one (and don't forget to update your keys file when you do this).

Screenshots
-----------
Some screenshots illustrating the SMaHT Portal credentials (Access Key ID and Secret Access Key) creation process.
First, go to your **Profile** and click **Add Access Key**.

.. image:: _static/images/credentials_access_key_before.png
    :target: _static/images/credentials_access_key_before.png
    :alt: Portal Access Key Creation (Before)

After clicking **Add Access Key**, save the **Access Key ID** and **Secret Access Key** to your keys file.

.. image:: _static/images/credentials_access_key_created.png
    :target: _static/images/credentials_access_key_created.png
    :alt: Portal Access Key Creation

After dismissing the above by clicking the **X** you will see your **Access Key ID** (but **not** the **Secret Access Key**).
Note that you can delete it and create a new one at any time.

.. image:: _static/images/credentials_access_key_after.png
    :target: _static/images/credentials_access_key_after.png
    :alt: Portal Access Key Creation (After)
