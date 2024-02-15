==============
Advanced Usage
==============

Despite the title, this section describes not so much "advanced" usage, at least in terms of complexity, but merely less common use cases, which some users may find relevant.

Though the following `does` assume some basic understanding of JSON, CSV and TSV files,
and the ``tar``, ``gzip``, and ``zip`` command-line utilities.

Other Files Formats
===================

As described in the main `Usage <usage.html#formatting-files-for-submission>`_ section,
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

.. tip::
    To see an example of this JSON, if you have a Excel spreadsheet metadata file, you can invoke ``submit-metadata-bundle``
    with that file with both the ``--validate-local-only`` and ``--verbose`` options;
    this will output the JSON for the spreadsheet as translated by ``smaht-submitr``.

CSV Files
---------

As Excel files are really just fancy `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ (comma-separated-values),
it's natural that CSV files be supported as an alternative.
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
and the next question is how to submit multiple files in a single submission, which is answered next.

Archive Files
~~~~~~~~~~~~~

To submit multiple (CSV) files in a single submission, they need to be packaged together into a
single `archive` file (optionally compressed - `see below <advanced_usage.html#compressed-files>`_) using the standard ``tar`` command-line utility.
The name of this TAR file `must` be suffixed with ``.tar``; other than that there are
no requirements for the name of this file. For example::

    tar cf your_tar_file.tar cell_culture.csv unaligned_reads.csv

Or alternatively, rather than ``tar``, the standard ``zip`` command-line utility can also be used.
The name of this ZIP file `must` be suffixed with ``.zip``; other than that there are
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

.. tip::
    You can alternatively use the single suffix ``.tgz``, rather than double suffixed ``.tar.gz``, for such compressed (``gzip``-ed) TAR files.

More on Validation
==================

As described in the main `Usage <usage.html#validation>`_ section, validation can be performed on the given metadata file
before it is actually ingestion into SMaHT Portal. This can be done most simply and comprehensively
by using the ``--validate`` option. And in fact, this is the default behavior if you, as a submitter,
are `not` an `admin` user.

But under the hood there are more finer grained modes of validation
which may be useful for troubleshooting or other peculiar situations, as described next.

Client-Side vs. Server-Side Validation
--------------------------------------

Validation is supported both on the `client-side`, meaning `before` the data is submitted to
SMaHT Portal for ingestion; and on the `server-side`, meaning `after` the data is submitted
to SMaHT Portal for ingestion.

That is, client-side validation is performed `locally` within the ``submit-metadata-bundle`` command-line process itself;
and server-side validation is performed `remotely` within the SMaHT server ingestion process itself.

These two modes of validation largely cover the same ground,
however there are `some` aspects of validation which 
can `only` be done on the server-side and so this may pick up problems (e.g. various identifier format checking) which
are not possible to detect on the client-side; and conversely, the client-side validation
is the only place where issues regarding the presence (or absence) of any referenced
files (intended for upload) can be detected.

For this reason, the default ``--validate`` mode of validation is the most comprehensive,
as it performs `both` client-side and server-side validation.
But alternatively, you can invoke either one of these validations individually and exclusively as follows.

Validation Only
~~~~~~~~~~~~~~~

If you want to perform `only` the client-side validation (for whatever reason),
there is a ``--validate-local-only`` option which will cause `only` local client-side validation to be done;
no remote server-side validation will be done in this case.

If you want to perform `only` the server-side validation (for whatever reason),
there is a ``--validate-only`` option which will cause `only` remote server-side validation to be done;
no local client-side validation will be done in this case.

.. note::
    In `both` of these cases (``--validate-local-only`` and ``--validate-only``) the actual ingestion process itself
    will `not` proceed; i.e. these `only` perform (either client-side or server-side) validation and output the results.

Also of minor note is that if there are server-side validation errors, you will not be able
to continue with the submission process; i.e. there is no way to get your data ingested into SMaHT Portal,
unless/until you correct the problems (or unless you use the ``--validate-local``).
But if there are client-side validation errors,
you `may` (after prompting) continue processing, in spite of there
being local client-side validation errors (this of course is not recommended).

.. note::
    Even in the absence of `any` validation (which is actually not even a readily available option),
    if there are problems with the submitted data, it will `not` be ingested into SMaHT Portal;
    i.e. no need to worry that corrupt data might sneak into the system; the system guards against this.
    However, without making use of the ``--validate`` options it `is` possible that `some` of your objects
    will be ingested properly, and other, problematic ones, will `not` be ingested at all.

Viewing Portal Objects
======================

Also included in the ``smaht-submitr`` package is a command-line utility called ``view-portal-object``,
which some users might sometimes find convenient, for troubleshooting or sanity checking purposes.
Given a UUID or a path to an object within SMaHT Portal, it simply prints to the output the object in JSON format
for example::

    view-portal-object --env data dca16310-5127-4347-bd58-10f8fb5516b2
    view-portal-object --env data /SubmissionCenter/smaht_dac

If you want to display the data in `YAML <https://en.wikipedia.org/wiki/YAML>`_ format rather than JSON
use the ``--yaml`` option. And if you want to automatically copy the (JSON) data to the clipboard use the ``--copy`` option.

Viewing Portal Schemas
----------------------

Using the same ``view-portal-object`` utility described above you can also view SMaHT Portal object schemas,
by using the ``--schema`` option and passing the name of a SMaHT Portal object type,
for example::

    view-portal-object --env data --schema CellLine

Or you can output the type names of  `all` schema types present within SMaHT Portal using the special ``schemas`` identifier,
for example::

    view-portal-object --env data schemas

And if you also pass the ``--verbose`` option to the above, it will also print the `identifying` and `required` properties for each listed schema type name.

.. tip::
    There is nothing really that the ``view-portal-object`` command does that you cannot also do by interacting with SMaHT Portal directly 
    via your browser, but some command-line savvy users may find this interface more agreeable under some circumstances.

Installation for Developers
===========================

If you are a software developer, and you want to install ``smaht-submitr`` locally
for development or other purposes,
and assuming you have Python and a (optional) Python virtual environment satisfactorily setup,
you can do so like this::

   git clone https://github.com/smaht-dac/submitr.git
   cd submitr
   make build

Note that ``poetry`` is the substrate that the build scripts rely on.
You won't be calling it directly, rather ``make build`` will call it.

Internal Documentation
----------------------

Internal documentation for ``smaht-submitr`` can be found here:

.. toctree::
  :maxdepth: 1

  submitr
