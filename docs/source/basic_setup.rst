===========
Basic Setup
===========

SubmitCGAP is a Python based tool and requires a Python installation with version >=3.7.
This document is intended for users who are not very familiar with the command line or Python.
The intent is to provide detailed instructions for setting up your local environment for using SubmitCGAP.
These instructions are intended to work with Mac OS X. Linux users are presumed advanced and Windows instructions are not available at this time but will be provided in the future.

-----------------------
Unix Command Cheatsheet
-----------------------

Using this repository and interacting with file submissions assumes some knowledge of the Unix
filesystem and familiarity with bash. What follows is a list of the essential commands you should
know for working with SubmitCGAP. Whenever in doubt, you can enter "man <cmd>" into the terminal to
pull up documentation on the command. You can also do such search into your favorite search engine to
locate the manual pages. Generally you need to know how to look around the file system and create
directories and files.

* `pwd` will "print working directory" ie: the current location in the Unix file system where the terminal is "located". Whenever you start a new terminal session, odds are you will be sent to your home directory. The `~` character is a global alias for the current active users home directory.
* `ls` will list all files and directories in the current directory


.. code-block:: bash

    $ pwd
    /Users/<your_username>
    $ ls
    directory1
    file1
    file2
    $ ls ~  # this is an alias for your home directory, usually /Users/<your_username>
    directory1
    file1
    file2


* `cd` will change directory. Use `ls` first to see which directories are available, then use `cd` to change back to them. The special identifier `..` indicates the directory above the current one, so use `cd ..` to exit
* `cat <filename>` will output the contents of a file to the terminal
* `mkdir <directory_name>` will create a new directory
* `touch <filename>` will create a new empty file


Getting Started
---------------

To get started we will create an empty file to hold the submission credentials and a directory
for storing the submission Excel files and associated raw sequencing files. At this time, the sequencing
files need to be on your local machine to be submitted to CGAP. Do this by using the `touch` and `mkdir`
commands described above. Use the exact command below for creating the credential file, but you can
create the directory for the submission files anywhere, just note the location (you can check with `pwd`).


.. code-block:: bash

    $ touch ~/.cgap-keys.json
    $ mkdir Documents/submit_cgap


Installing Python and Pyenv
---------------------------

Most systems come with versions of Python installed by default, but oftentimes they are not the
newest versions, and for our software we prefer to be running newer supported versions of Python
for security reasons. We also recommend using `pyenv` for managing virtual environments. This allows
you to isolate Python package installations from one another, so you do not install another package
with conflicting dependencies that may causes issues.

Begin by installing pyenv using the automatic installer.

.. code-block:: bash

    curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

Then add the following to your `~/.bashrc` file. It may have no contents - if it does not exist you can
copy the below as is and drop it into the file. Doing so ensures that you can use your `~/.bashrc` file
as a macro for making `pyenv` and associated commands available to you easily.

.. code-block:: bash

    export PYENV_ROOT=“$HOME/.pyenv”
    command -v pyenv >/dev/null || export PATH=“$PYENV_ROOT/bin:$PATH”
    eval “$(pyenv init -)”
    eval “$(pyenv virtualenv-init -)”

Once done you can force the changes to take effect by running `source ~/.bashrc`. Once done you should
be able to run `pyenv`. In order to install newer Python versions, you will need to install Xcode
Developer Tools.

.. code-block:: bash

    xcode-select --install

This will take some significant time, but when it has completed you will have the toolchain necessary
for installing newer Python versions to your machine and can proceed with the below.

.. code-block:: bash

    pyenv install 3.8.13

This command will install Python version 3.8.13 through `pyenv`. If it is not successful feel free
to copy the error output and send it to the CGAP team. Once the installation has completed, we will
create and activate a virtual environment for using SubmitCGAP.

.. code-block:: bash

    pyenv virtualenv 3.8.13 submit_cgap38
    pyenv activate submit_cgap38

This creates a virtual environment called `submit_cgap38` using Python version 3.8.13. We add `38` at
the end to indicate it is a 3.8 environment. If successful, at this point you can transition to the
installation docs section Installing SubmitCGAP in a Virtual Environment.