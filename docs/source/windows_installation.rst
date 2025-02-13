====================
Windows Installation
====================

.. toctree::
  :maxdepth: 1

For **Windows** users, some testing has been done for ``smaht-submitr``,
but honesly it has not been as thorough as for MacOS and Linux.
Similarly for the **Windows** installation process;
these instructions here are provisional, not guaranteed, and are but one way of doing this;
but this should help you get started if you are not very experienced.

Installation
============

This assumes you have Adminstrator privileges, and that you do not yet have Python installed.
Open a PowerShell and execute:

.. code-block:: bash

    Set-ExecutionPolicy Bypass -Scope Process -Force; `
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

Afer this you should open a new PowerShell session to make sure the above "takes".
Then run these commands:

.. code-block:: bash

    choco install pyenv-win -y
    pyenv install 3.10.5
    pyenv global 3.10.5

Then install ``smaht-submitr`` by executing:

.. code-block:: bash

    pip install smaht-submitr
