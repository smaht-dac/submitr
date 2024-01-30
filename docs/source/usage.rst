===================
Using smaht-submitr
===================

Once you have finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle`` command.
There are 2 types of submissions: accessioning (new cases) and family history (pedigrees)
which both use the ``submit-metadata-bundle`` command.

Formatting Files for Submission
===============================

For more details on what file formats are accepted and how the information should be structured,
see our submission help pages at the
`SMaHT Portal <https://data.smaht.org/>`_.

But briefly, most commonly, the file format recommended is an Excel spreadsheet file (e.g. ``your_metadata_file.xlsx``),
comprised of one or more sheets, where each sheet name is the name of a SMaHT Portal entity or `object` defined within the system.

Each sheet may contain any number of rows, each representing an instance of the object.
Each sheet must have as its first row, a special `header` row, which enumerates the names of the object properties as the column names.

Note that the first row which is entirely empty marks the end of the input, and any subsequenct rows will be entirely ignored.

And similarly, the first column in the header column which is empty marks the end of the header,
and any subsequent columns will be entirely ignored.

Submission
==========

The type of submission supported is called a "metadata bundles", or `accessioning`.
And the name of the command-line tool to initiate a submission is ``submit-metadata-bundle``.
A brief tour of this command, its arguments, and function is given below.
To get help about the command, do::

   submit-metadata-bundle --help

For many cases it will suffice simply to specify the metadata bundle file you want to upload,
and the SMaHT environment name (such as ``data`` or ``staging``) from your ``~/.smaht-keys.json`` keys file).
For example::

   submit-metadata-bundle your_metadata_file.xlsx --env data

You can omit the ``--env`` option entirely if your ``~/.smaht-keys.json`` file has only one entry.
This command should do everything, including upload referenced files (it will prompt first for confirmation);
by default these referenced files should be in the same directory is the main file; or you can
specify an alternate directory where these reside using the ``--directory`` option.

If you belong to
multiple consortia and/or submission centers, you can also add the ``--consortium <consortium>``
and ``--submission-center <submission-center>`` options; if you belong to only one of either,
the command will automatically detect (based on your user profile) and use those.

To specify a different directory for the files, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --directory /path/to/folder

The above commands will only look for the files to upload only in the directory specified (and not any sub-directories within).
To look within subdirectories, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --directory /path/to/folder --subfolders

To invoke the submission for validation only, without having SMaHT actually ingest anything into its data store, do::

   submit-metadata-bundle mymetadata.xlsx --env <environment-name> --validate-only

To invoke the submission for with `local` sanity checking, where "local" means before actually submitting to SMaHT, do::

   submit-metadata-bundle mymetadata.xlsx --env <environment-name> --check

And to invoke the submission for with `only` local sanity checking, without actually submitting to SMaHT at all, do::

   submit-metadata-bundle mymetadata.xlsx --env <environment-name> --check-only

These ``--check`` and ``--check-only`` options can be very useful and their use is encouraged,
ensure that everything is in order before sending the submission off to SMaHT for processing.
This is actually the default behavior unless your user profile indicates that you are an `admin` user.
To be more specific, these check the following:


You can resume execution with the upload part by doing::

   resume-uploads <uuid> --env <environment-name>

or::

   resume-uploads <uuid> --env <environment-name>

You can upload individual files separately by doing::

   upload-item-data <filename> --uuid <item-uuid> --env <env>

or::

   upload-item-data <filename> --uuid <item-uuid> --server <server_url>

where the ``<item-uuid>`` is the uuid for the individual item, not the metadata bundle.

Normally, for the three commands above, you are asked to verify the files you would like
to upload. If you would like to skip these prompts so the commands can be run by a
scheduler or in the background, you can pass the ``--no_query`` or ``-nq`` argument, such
as::

    submit-metadata-bundle mymetadata.xlsx --no_query
