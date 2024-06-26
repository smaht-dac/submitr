=====
About
=====

This :toplink:`smaht-submitr <https://pypi.org/project/smaht-submitr/>` software
and :toplink:`SMaHT Portal <https://data.smaht.org/about/>`
were developed by the :toplink:`Department of Biomedical Informatics <https://dbmi.hms.harvard.edu/>` (DBMI)
at :toplink:`Harvard Medical School <https://hms.harvard.edu/>`.

.. image:: https://www.iscb.org/images/stories/ismb2020/bazaar/logo.HarvardMedical-BiomedicalInformatics.png
    :width: 450px
    :target: https://dbmi.hms.harvard.edu/
    :alt: HMS DBMI

.. note::
   You need a SMaHT account to use this software. For information an obtaining an account please see:
   `SMaHT Portal Account Creation <account_creation.html>`_

For further support, questions, feature requests, bug reports, or other information
regarding the metadata and file submission process, or the SMaHT project in general,
please contact the SMaHT DAC Team at
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_.
See the `Reporting Issues <#id1>`_ section below for more on getting help from us regarding bugs or other usage problems.

.. tip::
    **SMaHT** is an acronym for: :toplink:`Somatic Mosaicism across Human Tissues <https://commonfund.nih.gov/smaht>`

Python Package & Source Code
-----------------------------
* Python Package: :toplink:`https://pypi.org/project/smaht-submitr <https://pypi.org/project/smaht-submitr>`
* Source Code: :toplink:`https://github.com/smaht-dac/submitr <https://github.com/smaht-dac/submitr>`

Reporting Issues
----------------

If you're experiencing issues using this software, would like to report bugs, or have suggestions on
how to improve this process, please do not hesitate to report these to us at:
`smhelp@hms-dbmi.atlassian.net <mailto:smhelp@hms-dbmi.atlassian.net>`_

What to Send Us
~~~~~~~~~~~~~~~
If applicable, please include as much relevant information as you can to help us assist you in any troubleshooting process, including:

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

See Also
--------

.. raw:: html

    <ul>
        <li><a target="_blank" href="https://data.smaht.org/about">About SMaHT<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org">SMaHT Portal<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/docs">SMaHT Portal Documentation<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://www.smaht.org/">SMaHT Network<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/about/consortium/data">SMaHT Data Overview<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/about/join/policy">SMaHT Membership Policy<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/about/consortium/awardees">SMaHT Consortium Members Map<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href=" https://dbmi.hms.harvard.edu/">HMS Department of Biomedical Informatics<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
    </ul>

Technical
~~~~~~~~~

.. raw:: html

    <ul>
        <li><a target="_blank" href="https://docs.google.com/spreadsheets/d/1sEXIA3JvCd35_PFHLj2BC-ZyImin4T-TtoruUe6dKT4/edit#gid=1645623888">SMaHT Metadata Submission Template <span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://docs.google.com/spreadsheets/d/1b5W-8iBEvWfnJQFkcrO9_rG-K7oJEIJlaLr6ZH5qjjA/edit#gid=1589547329">SMaHT Metadata Submission Example <span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/search/?type=Consortium">SMaHT Consortia<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="https://data.smaht.org/search/?type=SubmissionCenter">SMaHT Submission Centers<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
        <li><a target="_blank" href="object_model.html">SMaHT Object Model<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a></li>
    </ul>
