=================
SamplePreparation
=================



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org/search/?type=SamplePreparation">SMaHT Portal</a> 
    object type <a target="_blank" href="https://data.smaht.org/profiles/SamplePreparation.json?format=json" style="color:black"><b><u>SamplePreparation</u></b> 🔗</a>.
    Its <b>parent</b> type is: <a href=Preparation.html><u>Preparation</u></a>.
    
    Types <b>referencing</b> this type are: <a href='CellCultureSample.html'><u>CellCultureSample</u></a>, <a href='CellSample.html'><u>CellSample</u></a>, <a href='Sample.html'><u>Sample</u></a>, <a href='TissueSample.html'><u>TissueSample</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties;
    and properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href='SubmissionCenter.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>accession</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>submitted_id</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b>consortia</b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><u>homogenization_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;TBD</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Method of sample homogenization, if applicable. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>preservation_method</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Preservation method for subsequent analysis. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Identifier on submission.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_SAMPLE-PREPARATION_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Monday, February 26, 2024 | 7:35 AM EST | <a target="_blank" href="https://data.smaht.org">data.smaht.org</a> | v1.0</small> ]
