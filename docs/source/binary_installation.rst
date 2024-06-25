===================
Binary Installation
===================

.. toctree::
  :maxdepth: 1

If you would like to avoid installing Python, the ``smaht-submitr`` tool can be installed as a single
self-contained executable file, as described below.

System Requirements
===================
These systems are supported  by the ``smaht-submitr`` binary.

* MacOS x86-64 architecture (Intel Silicon)
* MacOS arm64 architecture (Apple Silicon, i.e. M1, M2, or M3)
* Linux x86-64 architecture (RedHat/Centos or Debian/Ubuntu derivatives)
* Linux arm64 architecture (RedHat/Centos or Debian/Ubuntu derivatives)
* Note that Windows is not (currently) supported.

Installation
============

To install the ``smaht-submitr`` binary executable, simply run this command from the command-line:

.. code-block:: bash

    curl https://raw.githubusercontent.com/smaht-dac/submitr/master/install.sh | /bin/bash

This will download an executable file called ``submitr``.
You can/should move this to a directory which is in you ``PATH``.
For example:

.. code-block:: bash

    mkdir ~/bin
    mv submitr ~/bin
    export PATH=$PATH:~/bin  # Add this line to end of your ~/.bashrc file.

Usage
=====

The usage of this binary executable is exactly the same as with the normal Python-based installation
except that all commands need to be prefixed with ``submitr``. For example:

.. code-block:: bash

    submitr submit-metadata-bundle # your arguments ...
    submitr resume-uploads  # your arguments ...
