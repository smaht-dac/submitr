============
OntologyTerm
============



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org/search/?type=OntologyTerm">SMaHT Portal</a> 
    object type <a target="_blank" href="https://data.smaht.org/profiles/OntologyTerm.json?format=json" style="color:black"><b><u>OntologyTerm</u></b> 🔗</a>.
    
    
    Types <b>referencing</b> this type are: <a href='Diagnosis.html'><u>Diagnosis</u></a>, <a href='Exposure.html'><u>Exposure</u></a>, <a href='Therapeutic.html'><u>Therapeutic</u></a>, <a href='Treatment.html'><u>Treatment</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties;
    and properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>identifier</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>title</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td style="border-left:1px solid white;border-right:1px solid white;" colSpan="3"> At least <u>one</u> of: <b style='color:darkred;'>consortia</b>, <b style='color:darkred;'>submission_centers</b></td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>aliases</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>identifier</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b>consortia</b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b>submission_centers</b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Unique, identifying name for the item.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z]+:[0-9]+$</b></small></span> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>title</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Title for the item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>url</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: uri<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> An external resource with additional information about the item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Sunday, February 25, 2024 | 10:26 PM EST | <a target="_blank" href="https://data.smaht.org">data.smaht.org</a> | v1.0</small> ]
