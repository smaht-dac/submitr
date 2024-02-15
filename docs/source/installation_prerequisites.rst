==========================
Installation Prerequisites
==========================

The SMaHT submission tool, ``smaht-submitr``,
is a Python based command-line tool and requires a Python installation (version `3.8, 3.9, 3.10, or 3.11`).
These instructions, intended for users who are not very familiar with the command-line or Python,
will help you install Python and setup your local environment for using ``smaht-submitr``.

.. note::
    These instructions are targeted specifically for **Mac OS X** users.
    For **Linux** users, these should be generally applicable (with some modifications);
    presumed to be a bit more advanced, such users should have little difficulty.
    For **Windows** users, very little testing has been done; not recommended; but more experienced users should be able to work through it.

Each section in this document is meant to sequentially guide you through the initial setup
process for installing the tools necessary to effectively run ``smaht-submitr``.

The UNIX Command-Line
---------------------

The ``smaht-submitr`` package provides a number of `command-line` tools (commands) which must
be run from the command-line using a system `terminal` application.

On Mac OS X (which is built on UNIX), to open the ``Terminal`` application, open ``Finder``,
navigate to the ``Applications`` folder and then to the ``Utilities`` sub-folder.
Inside this folder should be the ``Terminal`` application, which you can double-click on to bring it up;
for future convenience you can add it to your home Dock (if not already there) by clicking and dragging it to your Dock.

Before continuing, once you've opened the ``Terminal`` ensure that in the top title bar it shows ``bash`` (and not ``zsh`` or whatever).
Newer Mac OS X versions package with ``zsh`` by default, but we want to use ``bash``.
If you see ``zsh``, once in the terminal run the following command,
close and re-open terminal and you will be using the expected ``bash`` shell::

    chsh -s /bin/bash

For Linux, it is inherently a more command-line oriented operating system,
and as Linux users are typically a bit more advanced than normal,
specific instructions will be omitted, though much of what is here is applicable to Linux as well.

UNIX Command Cheatsheet
-----------------------

Using ``smaht-submitr`` assumes some knowledge of the UNIX file system and
familiarity with the UNIX shell (``bash``).
What follows is a list of the essential commands you should
know for working with ``smaht-submitr``. For help with a UNIX command, you can always
enter ``man <command-name>`` in the terminal to pull up documentation on the named command.
You can also do use your favorite Web search engine to locate the manual pages.
Generally speaking, you just need to know how to look around the file system and create
directories and files.

* ``pwd``: This will print the full path of your current directory; i.e. the current location within the UNIX file system where your terminal is "located". Whenever you start a new terminal session, odds are you will be in your home directory. The ``~`` (tilde) character is a global alias for your home directory.
* ``ls``: This will list all files and directories in the current directory.
* ``ls -l``: Same as above but with more info, including file size (in bytes), for example `1311` for `some_file_name` in the example below.


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

Installing Homebrew
-------------------

For Mac OS X, a very common and convenient tool for the management of (mostly development related)
software installation is `Homebrew <https://brew.sh/>`_  or ``brew`` (as the command is named).
We will assume this Homebrew method of installation for the remainder of this document.

To install Homebrew, from the command-line, do::

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Just to make sure it installed properly try the command ``brew --version`` and it should output something like ``Homebrew 4.2.8``. Use ``brew help`` to see all available ``brew`` commands.

.. tip::
   Another common alternative to using Homebrew on Mac OS X is to use `XCode <https://developer.apple.com/xcode/>`_.
   If you want to go this route instead please see (for example) `Installing Python on Mac OS X via XCode <https://docs.python-guide.org/starting/install3/osx/>`_ (external link). In brief to get started with this use the command ``xcode-select --install``.
   Note however that this installs a `lot` of software, and it may be a lengthy process (at least in terms of time).

Installing Python
-----------------

Most systems come with a version of Python installed by default, but oftentimes it is an
older version; and for our software we prefer to be running newer supported versions of Python
for security and other reasons.

So, with ``brew`` installed (per the `previous section <installation_prerequisites.html#installing-homebrew>`_) we can now readily install Python like this::

    brew install python

Confusingly, this may (or may not) install Python as ``python3`` rather than ``python``.
If ``python`` does not work (e.g. `command not found`), then ``python3`` should work.
Hopefully, any confusion will dissipate once we get ``pyenv`` installed (next),
which is one goal here, so that we can gain more convenient control of which version of Python is installed/active.

Installing Pyenv
----------------

We highly recommend using ``pyenv`` for managing virtual Python environments.
This allows you to isolate Python package and library installations from one another,
so you do not install packages which have conflicting dependencies with another package,
as this may cause problems.

With ``pyenv`` you can create any number of (named) isolated installation environments,
each with its own version of Python, and each `guaranteed` not interfere with one another.
Using ``brew``, you can install ``pyenv`` like this::

    brew install pyenv pyenv-virtualenv

.. note::

    FYI there are (of course) other ways to install ``pyenv``, for example with
    ``curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash``

Configuring Pyenv
~~~~~~~~~~~~~~~~~
Before using ``pyenv`` you will first need to add some settings to your ``~/.bashrc`` file,
which is a script that is executed whenever your login (or launch a new terminal).
You can edit this file (for example) with ``TextEdit`` (or ``vim`` or whatever you're familiar with) from the terminal with::

    open -a TextEdit ~/.bashrc

Add the following (verbatim) to your ``~/.bashrc`` file (at the end of the file is fine)::

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

Once you've saved those changes,
you can force these changes to take effect immediately (without closing and opening a new terminal)
by running ``source ~/.bashrc``. Once this is done you should be able to run ``pyenv`` properly;
for example, to list your virtual environments, do::

    pyenv virtualenvs

You probably won't see anything listed from that as you have not defined any virtual environments yet.

Using Pyenv
~~~~~~~~~~~
Now (finally), to use ``pyenv`` to install a newer/specific version Python,
for example version 3.11.6 (a recommended version), do::

    pyenv install 3.11.6

You can list the versions of Python which are installed using ``pyenv versions``.
And now, to create (and activate) a Python virtual environment named (for example) ``smaht-submitr-3.11``, do::

    pyenv virtualenv 3.11.6 smaht-submitr-3.11
    pyenv activate smaht-submitr-3.11

This creates a virtual Python environment called ``smaht-submitr-3.11`` which uses Python version 3.11.6,
and then (the second command there) actives that virtual environment for your current terminal session.
Your can name your virtual environment (i.e. ``smaht-submitr-3.11`` in this example) whatever of you like.
You can list the virtual environment you have created using ``pyenv virtualenvs``.
(You can deactivate a virtual environment using ``pyenv deactivate``).

.. caution::
   You will need to explicitly active the desired virtual environment for each new terminal session,
   i.e. using ``pyenv activate smaht-submitr-3.11`` for example.

Assuming the above example, if you now do ``python --version`` you should `definitely` see something like ``Python 3.11.6``;
if you do not, then something may be wrong (see the `About <about.html#reporting-issues>`_ page to see about
contacting us for additional help).

.. note::

   There are of course other features provided by ``pyenv`` (e.g. setting up to use a particular Python version
   whenever you're in a particular directory). For more information, this page provides a pretty good tutorial:
   `Managing Multiple Python Versions With Pyenv <https://realpython.com/intro-to-pyenv/>`_.
