================
Account Creation
================

Information on obtaining a :toplink:`SMaHT Portal <https://data.smaht.org/>` account.

* To get setup with a SMaHT Portal account for your role, please email our `data wranglers` at `smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.
* Please provide the email address you wih to use for your account, and CC your principle investigator (PI) for validation purposes.
* This email must be the same as the one registered with the SMaHT OC.
* This email address may be any one you like (e.g. an institutional one), but it `must` be associated with a Google account (see below).
* If you wish to use a **non-Google** (e.g. an institutional) email address, please **see below** for information on linking this email to a Google account.
* Once your account request is processed, you will then be able to login to :toplink:`SMaHT Portal <https://data.smaht.org/>` using the **Sign in with Google** option, using your chosen Google or Google-linked email address, and account password.


Linking Non-Google Email to Google
----------------------------------

SMaHT Portal uses the :toplink:`OAuth <https://en.wikipedia.org/wiki/OAuth>` authentication system to support login.
This requires that you login to SMaHT Portal with a **Google** account.

But how do you do this if you prefer to use a **non-Google** (e.g. institutional) email address?
In this case you will need to associate (`link`) your non-Google email address with a Google account.
To do this go to this page and following the instructions:

* :toplink:`Google Account Creation with non-Google Email <https://accounts.google.com/SignUpWithoutGmail>`

.. note::
    It is important to `not` register this Google account with your Google (gmail) email address as your primary email.
    Rather, register with your non-Google (e.g. institutional) email address as the **primary email address** associated with
    your Google account in order for authentication to work properly!

.. tip::
   For more on this please see:
   :toplink:`SMaHT Portal Account Creation <https://data.smaht.org/docs/user-guide/account-creation>`

Obtaining Credentials
----------------------
Once you have a SMaHT Portal account, you will want to obtain credentials in order to use ``smaht-submitr``.
This is required to allow this software to communicate directly with SMaHT Portal.
Please see the next `Credentials <credentials.html>`_ section for instructions on this.
