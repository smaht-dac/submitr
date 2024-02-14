==========================
Installation Prerequisites
==========================

The SMaHT ingestion submission tool, ``smaht-submitr``,
is a Python based command-line tool and requires a ``python`` installation with version `3.8, 3.9, 3.10, or 3.11`.
This document is intended for users who are not very familiar with the command-line or Python.
The intent is to provide detailed instructions for setting up your local environment for using ``smaht-submitr``.

.. note::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these instructions should be generally applicable (with some modifications),
    and such users, who are presumed to be a bit more advanced, should have no great difficulty.
    For **Windows**, little to no testing has been done; Windows specific instructions may be available in the future.

Navigating this Document
========================

Each section in this document is meant to sequentially guide you through the initial setup
process for installing dependencies necessary to run ``smaht-submitr``, while simultaneously
getting you setup with some best practices for managing the submissions in your local system.

One important note of clarification is that when you see code blocks that begin with ``\$``,
this means the commands are meant to be run directly in the (command-line) ``Terminal`` application
(without the ``\$``). Blocks that do not begin with ``\$`` are intended to be dropped
directly into files.


Unix Command Cheatsheet
-----------------------

Using Unix commands to interact with your system directly requires using the (command-line) ``Terminal`` application.
To open the ``Terminal`` application, if not present in your home dock, open ``Finder``, navigate to
Applications folder and then to the Utilities sub-folder. Inside the Utilities folder near the bottom should
be the ``Terminal`` application, which you should add to your home dock by clicking and dragging for
future convenience.

Before continuing, once you've opened the `Terminal` ensure in the top it says `bash` and not
`zsh`. Newer Mac OS X versions package with `zsh` by default, but we want to use `bash`. If you see `zsh`,
once in the terminal run the following command, close and re-open terminal and you will be using the
expected `bash` shell

.. code-block:: bash

    $ chsh -s /bin/bash

Using this repository and interacting with file submissions assumes some knowledge of the Unix
file-system and familiarity with ``bash``. What follows is a list of the essential commands you should
know for working with ``smaht-submitr``. Whenever in doubt, you can enter "man <cmd>" into the terminal to
pull up documentation on the command. You can also do such search into your favorite search engine to
locate the manual pages. Generally you need to know how to look around the file system and create
directories and files.

* `pwd` will "print working directory" i.e: the current location in the Unix file system where the terminal is "located".
  Whenever you start a new terminal session, odds are you will be sent to your home directory.
  The `~` character is a global alias for the current active users home directory.
* `ls` will list all files and directories in the current directory.


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


* `cd` will change directory. Use `ls` first to see which directories are available, then use `cd` to change back to them. The special identifier `..` indicates the directory above the current one, so use `cd ..` to exit.
* `cat <filename>` will output the contents of a file to the terminal.
* `mkdir <directory_name>` will create a new directory.
* `touch <filename>` will create a new empty file.


Installing XCode Developer Tools
--------------------------------

Some new machines come with very few parts of the developer toolchain that may prevent
you from doing even basic installation of packages. Thankfully, for Mac OS X, packages
all of the developer tools cleanly into an easily installable package it calls the XCode Developer
Tools. You can install these with:

.. code-block:: bash

    $ xcode-select --install

This install may take some significant time, but once complete you should have tools
necessary for installing Python and other related package for use with ``smaht-submitr``.


Installing Python and Pyenv
---------------------------

Most systems come with versions of Python installed by default, but oftentimes they are not the
newest versions, and for our software we prefer to be running newer supported versions of Python
for security reasons. We also recommend using `pyenv` for managing virtual environments. This allows
you to isolate Python package installations from one another, so you do not install another package
with conflicting dependencies that may causes issues. Doing so ensures that you have an isolated
installation location that will not interfere with other things you may have installed into your
system Python.

Begin by installing pyenv using the automatic installer.

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

The previous XCode Developer Tools installation should give you dependencies necessary
to install newer Python versions.

.. code-block:: bash

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
