====
WorkflowRun
====

Description of properties for the SMaHT Portal schema for **WorkflowRun**.


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>workflow</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    Properties in <span style='color:red'>red</span> are <i>required</i> properties.
    Properties in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties. <p />
    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>input_files</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>object</b> </td> <td width="80%"> The files used as initial input for the workflow. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>job_id</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>output_files</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>object</b> </td> <td width="80%"> All files that are saved as output of the workflow. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>parameters</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>object</b> </td> <td width="80%"> Parameters of the workflow run. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>postrun_json</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><br />•&nbsp;format: uri </td> <td width="80%"> Location of the AWSEM postrun json file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>run_status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;started&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;running<br />&nbsp;•&nbsp;output_files_transferring<br />&nbsp;•&nbsp;output_file_transfer_finished<br />&nbsp;•&nbsp;complete<br />&nbsp;•&nbsp;error</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>run_url</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><br />•&nbsp;format: uri </td> <td width="80%"> Url to AWS run info. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>workflow</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Workflow.html style='font-weight:bold;color:green;'>Workflow</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> The workflow that was run. </td> </tr> </table>
    <p />
