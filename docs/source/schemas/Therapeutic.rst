===========
Therapeutic
===========



.. raw:: html

    Summary of properties for the SMaHT Portal 
    object type <a target="_blank" href="https://data.smaht.org/profiles/Therapeutic.json?format=json" style="color:black"><b><u>Therapeutic</u></b> 🔗</a>.
    
    
    
    Property names which are <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    and those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties.
    Properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>agent</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>medical_history</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>agent</b> </td> <td> <a href=OntologyTerm.html style='font-weight:bold;color:green;'>OntologyTerm</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>diagnosis</b> </td> <td> <a href=Diagnosis.html style='font-weight:bold;color:green;'>Diagnosis</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>medical_history</b> </td> <td> <a href=MedicalHistory.html style='font-weight:bold;color:green;'>MedicalHistory</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>agent</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=OntologyTerm.html style='font-weight:bold;color:green;'>OntologyTerm</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated ontology term for the therapeutic agent. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>diagnosis</b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Diagnosis.html style='font-weight:bold;color:green;'>Diagnosis</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated diagnosis. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>dose</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Dose of the therapeutic used by the individual. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>dose_units</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;mg<br />&nbsp;•&nbsp;mL</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Units for the dose of the therapeutic. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>frequency</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Once Per Day<br />&nbsp;•&nbsp;Twice Per Day</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Frequency of administration of the therapeutic. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>medical_history</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=MedicalHistory.html style='font-weight:bold;color:green;'>MedicalHistory</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated medical history. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br />Must adhere to (regex) <span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[A-Z0-9]{3,}_THERAPEUTIC_[A-Z0-9-_.]{4,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Sunday, February 25, 2024 | 3:14 PM EST | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a></small> ]
