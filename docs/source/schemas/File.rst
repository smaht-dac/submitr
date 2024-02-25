====
File
====



.. raw:: html

    Description of properties for the SMaHT Portal object type <b>File</b>.
    
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    In the <i>Properties</i> section, properties in <span style='color:red'>red</span> are <i>required</i> properties,
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>data_category</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>data_type</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>file_format</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>file_format</b> </td> <td> <a href=FileFormat.html style='font-weight:bold;color:green;'>FileFormat</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>sequencing_center</b> </td> <td> <a href=SubmissionCenter.html style='font-weight:bold;color:green;'>SubmissionCenter</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>content_md5sum</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><br />•&nbsp;format: hex </td> <td width="80%"> The MD5 checksum of the uncompressed file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>data_category</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Category for information in the file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>data_type</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A calculated title for every object. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>file_format</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=FileFormat.html style='font-weight:bold;color:green;'>FileFormat</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>file_size</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Size of file on disk. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>filename</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> The local file name used at time of submission. Must be alphanumeric, with the exception of the following special characters: '+=,.@-_'.<br /><b>pattern</b>: <small style='font-family:monospace;'>^[\w+=,.@-]*$</small> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>href</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Use this link to download this file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>md5sum</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><br />•&nbsp;format: hex </td> <td width="80%"> The MD5 checksum of the file being transferred. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>o2_path</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Path to file on O2. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>quality_metrics</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Associated QC reports. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>s3_lifecycle_category</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;ignore<br />&nbsp;•&nbsp;long_term_access<br />&nbsp;•&nbsp;long_term_access_long_term_archive<br />&nbsp;•&nbsp;long_term_archive<br />&nbsp;•&nbsp;no_storage<br />&nbsp;•&nbsp;short_term_access<br />&nbsp;•&nbsp;short_term_access_long_term_archive<br />&nbsp;•&nbsp;short_term_archive</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> The lifecycle category determines how long a file remains in a certain storage class. If set to ignore, lifecycle management will have no effect on this file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>s3_lifecycle_last_checked</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Date when the lifecycle status of the file was last checked. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>s3_lifecycle_status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deep archive<br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;glacier<br />&nbsp;•&nbsp;infrequent access<br />&nbsp;•&nbsp;standard&nbsp;←&nbsp;<small><b>default</b></small></span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Current S3 storage class of this object. [Files in Standard and Infrequent Access are accessible without restriction. Files in Glacier and Deep Archive need to be requested and cannot be downloaded] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>sequencing_center</b> </td> <td width="15%" style="white-space:nowrap;"> <a href=SubmissionCenter.html style='font-weight:bold;color:green;'>SubmissionCenter</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Sequencing Center. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;uploading&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;uploaded<br />&nbsp;•&nbsp;upload failed<br />&nbsp;•&nbsp;to be uploaded by workflow<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review<br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;archived<br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;public</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>upload_credentials</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>upload_key</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> File object name in S3. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
