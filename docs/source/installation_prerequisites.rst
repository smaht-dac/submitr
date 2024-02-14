==========================
Installation Prerequisites
==========================

The SMaHT submission tool, ``smaht-submitr``,
is a Python based command-line tool and requires a Python installation (version `3.8, 3.9, 3.10, or 3.11`).
These instructions, intended for users who are not very familiar with the command-line or Python,
will help you install Python and setup your local environment for using ``smaht-submitr``.

.. warning::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these instructions should be generally applicable (with some modifications),
    and such users, who are presumed to be a bit more advanced, should have no great difficulty.
    For **Windows** users, little to no testing has been done; Windows specific instructions may be available in the future.

Navigating this Document
========================

Each section in this document is meant to sequentially guide you through the initial setup
process for installing dependencies necessary to run ``smaht-submitr``, while simultaneously
getting you setup with some best practices for managing the submissions on your local system.


The Command-Line
----------------

The ``smaht-submitr`` package provides a number of `command-line` tools (commands) which must
be run from the command-line using a system `terminal` application.

On Mac OS X, to open the ``Terminal`` application, if not already present in your home Dock, open ``Finder``, navigate to
the ``Applications`` folder and then to the ``Utilities`` sub-folder. Inside this folder
should be the ``Terminal`` application, which you can double-click on to bring it up;
for future convenience you can add it to your home dock by clicking and dragging it to your Dock.

Before continuing, once you've opened the ``Terminal`` ensure in the top it says ``bash`` and not
``zsh``. Newer Mac OS X versions package with ``zsh`` by default, but we want to use ``bash``. If you see ``zsh``,
once in the terminal run the following command, close and re-open terminal and you will be using the
expected ``bash`` shell

.. code-block:: bash

    $ chsh -s /bin/bash

For Linux, it is inherently a more command-line oriented operating system,
and as Linux users are typically a bit more advanced than normal,
specific instructions will be omitted, though much of what is here is applicate to Linux as well.

UNIX Command Cheatsheet
-----------------------

Using this repository and interacting with file submissions assumes some knowledge of the UNIX
file-system and familiarity with ``bash``. What follows is a list of the essential commands you should
know for working with ``smaht-submitr``. For help for a UNIX command, you can always
enter ``man <command-name>`` in the terminal to pull up documentation on the named command.
You can also do use your favorite Web search engine to locate the manual pages.
Generally speaking, you just need to know how to look around the file system and create
directories and files.

* ``pwd``: This will print the full path of your current directory; i.e. the current location within the UNIX file system where your terminal is "located". Whenever you start a new terminal session, odds are you will be in your home directory. The ``~`` (tilde) character is a global alias for your home directory.
* ``ls``: This will list all files and directories in the current directory.
* ``ls -l``: Same as above but includes more detailed info, including file size (in bytes), for example `1311` for `some_file_name` in the below example.


.. code-block:: bash

    $ pwd
    /Users/your_username
    $ ls
    some_file_name
    another_file_name
    some_directory_name/
    $ ls -l
    -rw-r--r--  1 your_username  your_usergroup    1311 Feb  7 14:04 some_file_name
    -rw-r--r--  1 your_username  your_usergroup    4038 Feb 14 14:04 another_file_name
    drw-r--r--  1 your_username  your_usergroup     128 Jan  5 14:04 some_directory_name/


* ``cd``: This will change your current directory. The special identifier ``..`` indicates the parent directory (above the current one).
* ``cat some_file_name``: This will output the contents of a file to the terminal.
* ``mkdir some_directory_name``: This will create a new directory.
* ``touch some_file_name``: This will create a new empty file; **be careful** as if ``some_file_name`` already exists it will be truncated.


Installing Python and Pyenv
---------------------------

Most systems come with a version of Python installed by default, but oftentimes it is an
older version; and for our software we prefer to be running newer supported versions of Python
for security and other reasons.

We also recommend using ``pyenv`` for managing virtual environments. This allows
you to isolate Python package installations from one another, so you do not install another package
with conflicting dependencies that may causes issues. Doing so ensures that you have an isolated
installation location that will not interfere with other things you may have installed into your
system Python.

Begin by installing ``pyenv`` using the automatic installer.

.. code-block:: bash

    $ curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

You will now need to add some commands to your `~/.bashrc` file, which is a script that is executed
when your user logs in. You can open this file with TextEdit from the terminal with:

.. code-block:: bash

    $ open -a TextEdit ~/.bashrc

If you prefer a different text editor, such as VSCode, you can replace `TextEdit` with the name of that
application, but we recommend `TextEdit` for users who are not familiar with other editors.

Once open, add the following to your `~/.bashrc` file. It may have no contents - if it does not exist
you can copy the below as is and drop it into the file. Doing so ensures that you can use
your `~/.bashrc` file as a macro for making `pyenv` and associated commands available to you easily.
When doing this ensure that you copy the block from below as sometimes the quotation marks
get clobbered into an incorrect form that will throw errors when you run it.

.. code-block:: bash

    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

Once done you can force the changes to take effect by running `source ~/.bashrc`. Once done you should
be able to run `pyenv`.

.. code-block:: bash

    $ source ~/.bashrc
    $ pyenv  # verify installation, should output some help information

To install a newer/specific version Python, do::

    $ pyenv install 3.11.6

This command will install Python version 3.11.6 through `pyenv`. If it is not successful feel free
to copy the error output and send it to the SMaHT DAC Team. Once the installation has completed, we will
create and activate a virtual environment for using ``smaht-submitr``.

.. code-block:: bash

    $ pyenv virtualenv 3.11.6 smaht-submitr-3.11
    $ pyenv activate smaht-submitr-3.11
    $ pyenv local smaht-submitr-3.11

This creates a virtual environment called ``smaht-submitr-3.11`` using Python version 3.11.6. We add ``-3.11`` at
the end just to indicate it is a Python 3.11 environment. Feel free to name your virtual environment whatever
name is most convenient for you. When in doubt you can run ``pyenv versions`` to see a list of
virtual environments you have created. The ``pyenv local`` command ensures that whenever you ``cd`` into
your ``smaht-submitr`` directory you automatically enter the associated virtual environment. If successful, at
this point you can transition to the installation docs section
Installing smaht-submitr in a Virtual Environment.
