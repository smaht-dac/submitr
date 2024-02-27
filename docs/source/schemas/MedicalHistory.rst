==============
MedicalHistory
==============



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=MedicalHistory" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/MedicalHistory.json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/MedicalHistory.json?format=json" style="color:black"><b><u>MedicalHistory</u></b> 🔗</a>.
    
    
    Types <b>referencing</b> this type are: <a href='Diagnosis.html'><u>Diagnosis</u></a>, <a href='Exposure.html'><u>Exposure</u></a>, <a href='MolecularTest.html'><u>MolecularTest</u></a>, <a href='Therapeutic.html'><u>Therapeutic</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties whose types are in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href='SubmissionCenter.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>accession</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>submitted_id</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b>consortia</b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td style="border-left:1px solid white;border-right:1px solid white;"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th style="border-left:1px solid white;border-right:1px solid white;"> Property </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Type </th> <th style="border-left:1px solid white;border-right:1px solid white;"> Description </th> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=Consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><u>primary_source_of_information</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;TBD</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Source of information for the medical history. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> - </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><a href=SubmissionCenter.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Identifier on submission.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_MEDICAL-HISTORY_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br /> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td width="5%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="border-left:1px solid white;border-right:1px solid white;white-space:nowrap;"> <b>string</b> </td> <td width="80%" style="border-left:1px solid white;border-right:1px solid white;"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
