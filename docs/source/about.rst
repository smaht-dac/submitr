=====
About
=====

This :toplink:`smaht-submitr <https://pypi.org/project/smaht-submitr/>` software
and :toplink:`SMaHT Portal <https://data.smaht.org/>`
were developed by the :toplink:`Department of Biomedical Informatics <https://dbmi.hms.harvard.edu/>` (DBMI)
at :toplink:`Harvard Medical School <https://hms.harvard.edu/>`.

.. image:: https://dbmi.hms.harvard.edu/sites/default/files/hero-images/HMS_DBMI_Logo.svg
    :width: 350px
    :target: https://dbmi.hms.harvard.edu/
    :alt: HMS DBMI

.. note::
   You need a SMaHT account to use this software. For information an obtaining an account please see:
   `SMaHT Portal Account Creation <account_creation.html>`_

For further support, questions, feature requests, bug reports, or other information
regarding the file submission process or the SMaHT project,
please contact the SMaHT DAC Team at
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.
See the `Reporting Issues <#id1>`_ section below for more on this.

.. tip::
    **SMaHT** is an acronym for: :toplink:`Somatic Mosaicism across Human Tissues <https://commonfund.nih.gov/smaht>`

Python Package & Source Code
-----------------------------
* Python Package: :toplink:`https://pypi.org/project/smaht-submitr <https://pypi.org/project/smaht-submitr>`
* Source Code: :toplink:`https://github.com/smaht-dac/submitr <https://github.com/smaht-dac/submitr>`

Reporting Issues
----------------

If you experience issues with this software, please do not hesitate to report them to
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.

What to Send Us
~~~~~~~~~~~~~~~
Please include as much relevant information as you can to help us assist in the troubleshooting process, including:

* Your operating system version. For Mac OS X you can get this by clicking **About this Mac** in the Apple logo dropdown at the top left corner of your screen.
* The full text of any error message you are seeing with all associated output.
* If possible, the output of the following commands from your terminal:

.. code-block:: bash

    submit-metadata-bundle --version
    uname -a
    python --version
    pip freeze

FYI you can capture the output of multiple commands into single file on the command-line like::

    submit-metadata-bundle --version >> your_error_info.txt
    uname -a >> your_error_info.txt
    python --version >> your_error_info.txt
    pip freeze >> your_error_info.txt

You can then attach this single file to any correspondence with us and it will likely allow us to resolve issues more quickly.

.. caution::
    Please be careful **not** to send us your SMaHT Portal **Secret Access Key** value
    (see `Credentials <credentials.html#securing-access-keys>`_).
    This is **sensitive** information and, like a password, it should **never** be
    **shared** with anyone, and particularly through any insecure channels (like email).
