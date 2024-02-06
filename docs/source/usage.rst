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
`SMaHT Portal <https://data.smaht.org/doc/>`_.

Most commonly, the file format recommended is an Excel spreadsheet file (e.g. ``your_metadata_file.xlsx``),
comprised of one or more sheets. Each sheet name must be the name of a SMaHT Portal entity or `object` defined within the system.

Each sheet must have as its first row, a special `header` row, which enumerates the names of the object properties as the column names;
each column name must match exactly the name of the property for the Portal object.
Each sheet may contain any number of rows, each representing an instance of the object.

Note that the first row which is entirely empty marks the end of the input, and any subsequenct rows will be entirely ignored.

And similarly, the first column in the header column which is empty marks the end of the header,
and any subsequent columns will be entirely ignored.

Here is screenshot of a simple example Excel spreadsheet: 

.. image:: _static/images/excel_screenshot.png
    :target: _static/images/excel_screenshot.png
    :alt: Excel Spreadsheet Screenshot

Notice that the first row comprises the property/column `header`, defining properties named ``submitted_id``, ``submission_centers``, and so on.

And also notice the multiple tabs at the bottom for the different sheets within the spreadsheet,
representing (in this example) data for the objects ``CellCultureSample``, ``Analyte``, and so on.

N.B. Though ``submission_center`` is shown in the above screenshot,
that particular field is not actually required, as it is automatically added by the ``smaht-submitr`` tool.

**Column Deletions**

A column value within a (non-header) row may be empty, but this only means that the value will be ignored
when creating or updating the associated object. In order to actually `delete` a property value from an object,
a special value - ``*delete*`` - should be used as the the property value.

**Nested Properties**

Some Portal object properties defined to contain other `nested` objects.
Since a (Excel spreadsheet) inherently defines a "flat" structure,
rather than the more hierarchical structure supported by Portal objects, in which such nested objects can be defined,
a special syntactic convention is needed to be able to reference the properties of these nested objects.
For this we will use a `dot-notation` whereby dots (``.``) are used to separate a parent property from its child property.
For example, an object may define a ``components`` property which itself may contain a ``cell_culture`` property;
to reference the ``cell_culture`` property then, the spreadsheet column header would need to be ``components.cell_culture``.

**Array Type Properties**

Some Portal object properties are defined to be lists (or `arrays`) of values.
Defining the values for such array properties, separate the individual array values by a comma (``,``).
For example if an object defines a ``molecules`` property as an array type, then to set this
value to an array with the two elements ``DNA`` and ``RNA``, use the value ``DNA,RNA`` in the associated spreadsheet cell.

Less common, but still supported, is the ability to set values for individual array elements.
This is accomplished by the convention suffixing the property name in the column header with
a pound sign (``#``) folowing by an integer representing the zero-indexed array element.
For example to set the first element of the ``molecules`` property (using the example above), use column header value ``molecule#0``.

**Boolean Type Properties**

For Portal object properties which are defined as `boolean` values, meaning either `true` or `false`,
simply use these values, i.e. ``true`` or ``false``.

**Property References**

Some Portal object properties are defined as being references to other Portal objects (also known as `linkTo` properties).
The values of these in the spreadsheet should be the unique identifying value for that object.
It is important to know that the ``smaht-submitr`` tool and SMaHT will ensure that the referenced
objects actually exist within the SMaHT Portal, `or` are defined within the spreadsheet itself;
if this is not the case then an error will be the result.
The identifying value for an object varies depending on the specific object in question,
though the ``uuid`` is common to all objects; other common identifying properties
are ``submitted_id`` and ``accession``.

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

This command should do everything, including uploading referenced file; it will prompt first for confirmation;
see the `Uploading Referenced Files` section just below for more on this.

If you belong to
multiple consortia and/or submission centers, you can also add the ``--consortium <consortium>``
and ``--submission-center <submission-center>`` options; if you belong to only one of either,
the command will automatically detect (based on your user profile) and use those.

**Uploading Referenced Files**

As mentioned above, after ``submit-metadata-bundle`` processes the main submission file, it will (after prompting) upload files referenced within the submission file. These files should reside
in the same directory as the submission file.
Or, if they do not, then yo must specify the directory where these files can be found, like this::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --directory <path-to-files>

The above commands will only look for the files to upload only directly within the specified directory
(and not any sub-directories therein). To look within subdirectories, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --directory <path-to-files> --subdirectories

**Valdation Only**

To invoke the submission for validation only, without having SMaHT actually ingest anything into its data store, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --validate-only

To be clear, this `will` submit the file to SMaHT for processing, but no data ingestion will take place, and any problems
will be reported back to you from the SMaHT server. To sanity check the file you are submitting  `before` actually
submitting it to SMaHT, you should use the ``--check`` option described now below.

**Sanity Checking**

To invoke the submission for with `local` sanity checking, where "local" means - `before` actually submitting to SMaHT, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --check

And to invoke the submission for with `only` local sanity checking, without actually submitting to SMaHT at all, do::

   submit-metadata-bundle your_metadata_file.xlsx --env <environment-name> --check-only

These ``--check`` and ``--check-only`` options can be very useful and their use is encouraged.
They ensure that everything is in order before sending the submission off to SMaHT for processing.
In fact this (``--check`` ) is actually the `default` behavior unless your user profile indicates that you are an `admin` user.
To be more specific, these sanity checks include the following:

#. Ensures the basic integrity of the format of the submission file.
#. Validates the objects defined within the submission file against the corresponding Portal schemas for these objects.
#. Confirms that any objects referenced within the submission file can be resolved; i.e. either they already exist within the Portal, or are defined within the submission file itself.
#. Checks that referenced files (to be subsequently uploaded) actually exist on the file system.

**Example Screenshots**

The output of a successfully completed ``submit-metadata-bundle`` will look something like this:

.. image:: _static/images/submitr_output.png
    :target: _static/images/submitr_output.png
    :alt: Excel Spreadsheet Screenshot

When specifying the ``--check`` the additional sanity checking output will look something like this:

.. image:: _static/images/submitr_check.png
    :target: _static/images/submitr_check.png
    :alt: Excel Spreadsheet Screenshot

Resuming Uploads
================
When using ``submit-metadata-bundle`` you can choose `not` to upload any referenced files when prompted.
In this case, you will probably want to manually upload them subsequently using the ``resume-uploads`` command.

You can resume execution with the upload part by doing::

   resume-uploads --env <environment-name> <uuid>

where the ``uuid`` argument is the UUID for the submission which should have been displayed in the output of the ``submit-metadata-bundle`` command.

You can upload individual files referenced in the original submission separately by doing::

   resume-uploads --env <environment-name> <referenced-file-uuid-or-accesssion-id> --uuid <item-uuid>

where the ``<referenced-file-uuid-or-accesssion-id>`` is the uuid (or the accession ID or accession based file name) of the 
individual file referenced (`not` the submission or metadata bundle UUID) which you wish to upload;
this uuid (or accession ID or accession based file name) is included in the output of ``submit-metadata-bundle``. 

For both of these commands above, you will be asked to confirm if you would like to continue with the stated action.
If you would like to skip these prompts so the commands can be run by a
scheduler or in the background, you can pass the ``--no_query`` or ``-nq`` argument, such as::

    submit-metadata-bundle your_metadata_file.xlsx --no_query

Getting Submission Info
=======================
To view relevant information about a submission using, do::

   check-submission --env <environment-name> <uuid>

where the ``uuid`` argument is the UUID for the submission which should have been displayed in the output of the ``submit-metadata-bundle`` command.
