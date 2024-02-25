====
QualityMetric
====

Description of properties for the SMaHT Portal schema for **QualityMetric**.


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>qc_values</b> </td> <td> array of object </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    Properties in <span style='color:red'>red</span> are <i>required</i> properties.
    Properties in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties. <p />
    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>category</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>href</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Use this link to download the QualityMetric zip archive. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>overall_quality_status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Fail<br />&nbsp;•&nbsp;Pass<br />&nbsp;•&nbsp;Warn</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Overall QC decision. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>qc_values</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>object</b> </td> <td width="80%"> QC values and their associated metadata. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>url</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><br />•&nbsp;format: uri </td> <td width="80%"> Location of the main html file. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> </table>
    <p />
