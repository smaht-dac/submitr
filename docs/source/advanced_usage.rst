==============
Advanced Usage
==============

Despite the title, this section describes not so much "advanced" usage, at least in terms of complexity, but merely less common use cases, which some users may find relevant.

Though the following `does` assume some basic understanding of JSON, CSV and TSV files,
and the ``tar``, ``gzip``, and ``zip`` command-line utilities.

Other Files Formats
===================

As described in the main `Usage <usage.html>`_ section,
the primary and recommended file format for metadata submission is the Excel spreadsheet.
However we also support a couple other formats, as follows.

JSON Files
----------

It is significant to note that internally, the ``smaht-submitr`` tool translates the given Excel spreadsheet file
into `JSON <https://en.wikipedia.org/wiki/JSON>`_ (JavaScript Object Notation) format, and then submits that to SMaHT for processing; i.e. JSON is really
the native format for this tool. So naturally, you can use a (single) JSON file directly rather than an Excel file to submit metadata.
The file name for a JSON file `must` be suffixed with ``.json``.

The required JSON is comprised of a single object containing one or more properties, each named for a SMaHT Portal object type,
and each of those containing an array of one or more object definitions for that type. The objects must of course
conform to the schema for their corresponding types.

To see an example of this JSON, if you have a Excel spreadsheet metadata file, you can invoke ``submit-metadata-bundle``
with that file, specifying the ``--check-only`` and ``--verbose`` options;
this will output the JSON for the given Excel spreadsheet as translated by ``smaht-submitr``.

CSV Files
---------

As Excel files are really just fancy `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ (comma-separated-values), it's natural that CSV files be supported as an alternative.
Nothing much to say here specifically about this file format per se, as it should be self-explanatory to anyone familiar with these file formats;
but be sure to read the next paragraph.
The file name for a CSV file `must` be suffixed with ``.csv``.

Since, unlike Excel files, which support multiple tabs (each representing a different SMaHT Portal object type),
CSV files cannot represent multiple SMaHT Portal object types, and since we need to somehow specify what object
type the CSV file contains data for, the actual file name of the CSV file is required to be the SMaHT Portal
object type name (minus the ``.csv`` suffix). This file name can be either the `camel-case <https://en.wikipedia.org/wiki/Camel_case>`_
or `snake-case <https://en.wikipedia.org/wiki/Snake_case>`_
version of the type name, for example, ``CellCulture.csv`` or ``cell_culture.csv``, respectively.

This obviously implies that multiple files are required if multiple types are to be submitted,
and the next question is how to submit multiple files in a single submission.

The answer is that in this case the files need to packaged together into a
single archive file (optionally compressed - see below) using the standard ``tar`` command-line utility.
The name of this TAR file `must` be suffixed with ``.tar``, other than that there are
no requirements for the name of this file. For example::

    tar cf your_tar_file.tar cell_culture.csv unaligned_reads.csv

Or alternatively, rather than ``tar``, the standard ``zip`` command-line utility can also be used.
The name of this ZIP file `must` be suffixed with ``.zip``, other than that there are
no requirements for the name of this file. For example::

    zip your_zip_file.zip cell_culture.csv unaligned_reads.csv

TSV Files
---------

Exactly analogous to CSV files, `TSV <https://en.wikipedia.org/wiki/Tab-separated_values>`_ (tab-separated-values) files are also supported;
the only difference being that tabs are used rather than commas as field separators.
And, the file name for a TSV file `must` be suffixed with ``.tsv`` (rather than ``.csv``).

Compressed Files
----------------

Any file that is submitted via ``smaht-submitr``, no matter what its format,
may be compressed using either of the standard ``gzip`` command-line utility.
Such file names `must` be suffixed with ``.gz``. For example::

    gzip your_tar_file.tar

This will automatically compress this file into ``your_tar_file.tar.gz``.
Incidentally, for such a ``.tar.gz`` file you both ``tar`` and ``gzip`` it in a single step like this::

    tar czf your_tar_file.tar.gz cell_culture.csv unaligned_reads.csv

And you can also alternatively use the single suffix ``.tgz`` (rather than ``.tar.gz``) for such compressed TAR files.

Viewing Portal Objects
======================

Also included in the ``smaht-submitr`` package is a command-line utility called ``view-portal-object``,
which some users might sometimes find convenient, for troubleshooting or sanity checking purposes.
Given a UUID or a path to an object within SMaHT Portal, it simply prints to the output the object in JSON format
for example::

    view-portal-object --env data dca16310-5127-4347-bd58-10f8fb5516b2
    view-portal-object --env data /SubmissionCenter/smaht_dac

Note there is nothing really that this command does that you cannot also do by interacting SMaHT Portal directly 
via your browser, but some command-line savvy users may find this interface more agreeable under some circumstances.

Viewing Portal Schemas
----------------------

Using the same ``view-portal-object`` utility described above you can also view SMaHT Portal object schemas,
by using the ``--schema`` option and passing the name of a SMaHT Portal object type,
for example::

    view-portal-object --env data --schema CellLine

Or you can output all schema types present within SMaHT Portal using the special ``schemas`` identifier,
for example::

    view-portal-object --env data schemas

And if you also pass the ``-verbose`` option to the above, it will also print the `identifying` and `required` properties for each listed schema type name.
