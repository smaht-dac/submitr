====
IngestionSubmission
====

Description of properties for the SMaHT Portal schema for **IngestionSubmission**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>ingestion_type</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>documents</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Documents that provide additional information (not data file). </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%"> <b>additional_data</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> Additional structured information resulting from processing, the nature of which may vary by ingestion_type and other factors. </td> </tr> <tr> <td width="5%"> <b>errors</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> A list of error messages if processing was aborted before results were obtained. </td> </tr> <tr> <td width="5%"> <b>ingestion_type</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> The type of processing requested for this submission. </td> </tr> <tr> <td width="5%"> <b>object_bucket</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> The name of the S3 bucket in which the 'object_name' resides. </td> </tr> <tr> <td width="5%"> <b>object_name</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> The name of the S3 object corresponding to the submitted document. </td> </tr> <tr> <td width="5%"> <b>parameters</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> A record of explicitly offered form parameters in the submission request. </td> </tr> <tr> <td width="5%"> <b>processing_status</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> A structured description of what has happened so far as the submission is processed. </td> </tr> <tr> <td width="5%"> <b>result</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> An object representing a result if processing ran to completion, whether the outcome was success or failure. </td> </tr> <tr> <td width="5%"> <b>submission_id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> The name of a folder in the S3 bucket that contains all artifacts related to this submission. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
