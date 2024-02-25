===================
IngestionSubmission
===================



.. raw:: html

    Description of properties for the SMaHT Portal object type <b>IngestionSubmission</b>.
    
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    In the <i>Properties</i> section, properties in <span style='color:red'>red</span> are <i>required</i> properties,
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    <br /><u>Description</u>: Schema for metadata related to submitted ingestion requests

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>ingestion_type</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|




Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>additional_data</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Additional structured information resulting from processing, the nature of which may vary by ingestion_type and other factors. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>documents</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Documents that provide additional information (not data file). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>errors</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> A list of error messages if processing was aborted before results were obtained. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u><span style='color:red'>ingestion_type</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;accessioning<br />&nbsp;•&nbsp;data_bundle<br />&nbsp;•&nbsp;metadata_bundle<br />&nbsp;•&nbsp;simulated_bundle</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> The type of processing requested for this submission. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>object_bucket</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> The name of the S3 bucket in which the 'object_name' resides. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>object_name</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> The name of the S3 object corresponding to the submitted document. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>parameters</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> A record of explicitly offered form parameters in the submission request. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>processing_status</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> A structured description of what has happened so far as the submission is processed. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>processing_status</span> <b>.</b> <u>outcome</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;unknown&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;success<br />&nbsp;•&nbsp;failure<br />&nbsp;•&nbsp;error</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> A token describing the nature of the final outcome, if any. Options are unknown, success, failure, or error. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>processing_status</span> <b>.</b> progress</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><span style='font-weight:normal'><br />•&nbsp;default: unavailable</span> </td> <td width="80%"> An adjectival word or phrase assessing progress, such as 'started', 'awaiting prerequisites', '88% done', or 'unavailable'. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>processing_status</span> <b>.</b> <u>state</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;created&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;submitted<br />&nbsp;•&nbsp;processing<br />&nbsp;•&nbsp;done</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> A state machine description of how processing is progressing (created, submitted, processed, or done). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>result</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> An object representing a result if processing ran to completion, whether the outcome was success or failure. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_id</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> The name of a folder in the S3 bucket that contains all artifacts related to this submission. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
