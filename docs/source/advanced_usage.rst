===============================
Advanced Usage of smaht-submitr
===============================

Despite the title, this section describes not so much "advanced" usage, at least in terms in terms of complexity, but merely less common use cases, which some users may find relevant.

Other Files Formats
===================

As desribed in the main usage section, the primary and recommended file format for metadata submission is the Excel spreadsheet.
However we also support a couple other formats, as follows.

**JSON Files**

It is interesting to note that internally, the ``smaht-submitr`` tool translates the given Excel spreadsheet file
into JSON (JavaScript Object Notation) format, and then submits that to SMaHT for processing; i.e. JSON is really
the native format for this tool. So naturally, you can use a (single) JSON file directly rather than an Excel file to submit metadata.

The required JSON is comprised of a single object containing one or more properties, each named for a SMaHT Portal object type,
and each of those containing an array of one or more object definitions for that type. The objects must of course
conform to the schema for their corresponding types.

To see an example of this JSON, if you have a Excel spreadsheet metadata file, you can invoke ``submit-metadata-bundle``
with that file, specifying the ``--check-only`` and ``--verbose`` options;
this will output the JSON for the given Excel spreadsheet as translated by ``smaht-submitr``.

**CSV Files**

As Excel files are really just fancy CSV (comma-separated-values), it's natural that CSV files be supported as an alternative.
The file name for CSV file `must` be suffixed with ``.csv``.
Nothing much to say here specifically about this file format per se, as it should be self-explanatory to anyone familiar with these file formats,
be be sure to read the next paragraph.

Since, unlike Excel files, which support multiple tabs (each representing a different SMaHT Portal object type),
CSV files cannot represent multiple SMaHT Portal object types, and since we need to somehow specify what object
type the CSV file contains data for, the actual file name of the CSV file is required to be the SMaHT Portal
object type name (minus the ``.csv`` suffix). This file name can be either the camel-case or the snake-case
version of the type name, for example, ``CellCulture.csv`` or ``cell_culture.csv``, respectively.

This obviously implies that multiple files are required if multiple types are to be submitted,
and the next question is how to submit multiple files in a single submission.
The answer is that in this case the files need to packaged together into a
single archive file (optionally compressed - see below) using the standard ``tar`` command-line utility.

**TSV Files**

Exactly the same as CSV files, TSV (tab-separated-values) files are also supported, with the only
difference being that tabs are used rather than commas as field separators.
And, the file name for TSV file `must` be suffixed with ``.tsv`` (rather than ``.csv``).

**Compressed Files**

Any file that is submitted via ``smaht-submitr``, no matter what its format,
maybe compress using either of the standard ``gzip`` or ``zip`` command-line utilities.
