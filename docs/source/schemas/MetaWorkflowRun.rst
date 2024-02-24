====
MetaWorkflowRun
====

Description of properties for the SMaHT Portal schema for **MetaWorkflowRun**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>meta_workflow</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    {identifying_properties_table}

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Title for the item </td> </tr> <tr> <td width="5%"> <b>tags</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>description</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Plain text description of the item </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> A unique identifier to be used to reference the object. </td> </tr> <tr> <td width="5%"> <b>alternate_accessions</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Accessions previously assigned to objects that have been merged with this object. </td> </tr> <tr> <td width="5%"> <b>meta_workflow</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> The meta workflow associated with the meta-workflow run. </td> </tr> <tr> <td width="5%"> <b>final_status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>failed_jobs</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> List of failed Tibanna job ids for this meta workflow run </td> </tr> <tr> <td width="5%"> <b>cost</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Total cost of the meta workflow run (includes failed jobs) </td> </tr> <tr> <td width="5%"> <b>file_sets</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> File collections associated with this MetaWorkflowRun </td> </tr> <tr> <td width="5%"> <b>workflow_runs</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> The list of workflow runs with their status and output files </td> </tr> <tr> <td width="5%"> <b>input</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> The input files and parameters used for the meta workflow run. </td> </tr> <tr> <td width="5%"> <b>@id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>@type</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
