=============
Using smaht-submitr
=============

Once you have finished installing this library into your virtual environment,
you should have access to the ``submit-metadata-bundle`` command.
There are 2 types of submissions: accessioning (new cases) and family history (pedigrees)
which both use the ``submit-metadata-bundle`` command.

Formatting Files for Submission
===============================

For details on what file formats are accepted and how the information should be structured,
see our submission help pages at the
`SMaHT Portal <https://data.smaht.org/>`_.

Metadata Bundles
================

There are two types of submissions that fall under "metadata bundles" - namely,
accessioning (new cases) and family history (pedigrees). The default is accessioning,
if no ingestion type is specified. If you would like to submit a family history,
make sure the cases are submitted first.

Accessioning
------------

For help about arguments, do::

   submit-metadata-bundle --help

However, it should suffice for many cases to specify
the bundle file you want to upload and either a site or a
SMaHT environment name (such as ``data`` or ``staging``).
For example::

   submit-metadata-bundle mymetadata.xlsx --server <server_url>

This command should do everything, including upload referenced files
if they are in the same directory. (It will ask for confirmation.) If you belong to
multiple consortia and/or submission centers, you can also add the ``--consortium <consortium>``
and ``--submission-center <submission-center>`` options; if you belong to only one of either,
SMaHT will automatically detect and use it.

To invoke it for validation only, without submitting anything, do::

   submit-metadata-bundle mymetadata.xlsx --validate-only --server <server_url>

To specify a different directory for the files, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder --server <server_url>

The above command will only look in the directory specified (and not any subdirectories)
for the files to upload. To look in the directory and all subdirectories, do::

   submit-metadata-bundle mymetadata.xlsx --upload_folder /path/to/folder --subfolders --server <server_url>

You can resume execution with the upload part by doing::

   resume-uploads <uuid> --env <env>

or::

   resume-uploads <uuid> --server <server_url>

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

Family History
--------------

If, after submitting a case, you would also like to submit a family history for the case,
you use the same command as described above but add the --ingestion_type flag::

    submit-metadata-bundle mypedigree.xlsx --ingestion_type family_history --server <server_url>
