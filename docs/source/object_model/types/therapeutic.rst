===========
Therapeutic
===========



..    View <a target="_blank" href="https://data.smaht.org/search/?type=Therapeutic" style="color:black"><b><i><u>objects</u></i></b></a>

.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Therapeutic&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Therapeutic.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Therapeutic.json" style="color:black"><b><u>Therapeutic</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Therapeutic.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    
    
    Types <b>referencing</b> this type are: <a href='diagnosis.html'><u>Diagnosis</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    of this type: <a target="_blank" href="https://data.smaht.org/search/?type=Therapeutic"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:2pt;" /></a>
    <p />
    


.. tip::

  .. raw::  html

    <i>See Therapeutic values <a target='_blank' href='https://data.smaht.org/search/?type=Therapeutic'><b>here<span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></b></a></i>


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>agent</span></b> </td> <td width="10%"> <a href='ontology_term.html'><b style='color:green;'><u>OntologyTerm</u></b></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>medical_history</span></b> </td> <td width="10%"> <a href='medical_history.html'><b style='color:green;'><u>MedicalHistory</u></b></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>agent</span></b> </td> <td width="10%"> <a href=ontology_term.html style='font-weight:bold;color:green;'><u>OntologyTerm</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b>diagnosis</b> </td> <td width="10%"> <a href=diagnosis.html style='font-weight:bold;color:green;'><u>Diagnosis</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>medical_history</span></b> </td> <td width="10%"> <a href=medical_history.html style='font-weight:bold;color:green;'><u>MedicalHistory</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>agent</span></b> </td> <td style="white-space:nowrap;"> <u><a href=ontology_term.html style='font-weight:bold;color:green;'><u>OntologyTerm</u></a></u><br />•&nbsp;string<br /> </td> <td> Link to the associated ontology term for the therapeutic agent. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Consortia associated with this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>diagnosis</b> </td> <td style="white-space:nowrap;"> <u><a href=diagnosis.html style='font-weight:bold;color:green;'><u>Diagnosis</u></a></u><br />•&nbsp;string<br /> </td> <td> Link to the associated diagnosis. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>dose</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Dose of the therapeutic used by the individual. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>dose_units</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;mL<br />&nbsp;•&nbsp;mg</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Units for the dose of the therapeutic. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>frequency</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Once Per Day<br />&nbsp;•&nbsp;Twice Per Day</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Frequency of administration of the therapeutic. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>medical_history</span></b> </td> <td style="white-space:nowrap;"> <u><a href=medical_history.html style='font-weight:bold;color:green;'><u>MedicalHistory</u></a></u><br />•&nbsp;string<br /> </td> <td> Link to the associated medical history. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;restricted</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers that created this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Identifier on submission.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_THERAPEUTIC_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
