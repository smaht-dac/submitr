=============
MolecularTest
=============



.. raw:: html

    Description of properties for the SMaHT Portal object type <b>MolecularTest</b>.
    
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    In the <i>Properties</i> section, properties in <span style='color:red'>red</span> are <i>required</i> properties,
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>medical_history</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>result_classification</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>title</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>medical_history</b> </td> <td> <a href=MedicalHistory.html style='font-weight:bold;color:green;'>MedicalHistory</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>medical_history</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=MedicalHistory.html style='font-weight:bold;color:green;'>MedicalHistory</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated medical history. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>result</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Result of the molecular test. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u><span style='color:red'>result_classification</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Within Normal Range<br />&nbsp;•&nbsp;Outside Normal Range<br />&nbsp;•&nbsp;Inconclusive</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Categorical classification of the result value. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br /><b>pattern</b>: <small style='font-family:monospace;'>^[A-Z0-9]{3,}_MOLECULAR-TEST_[A-Z0-9-_.]{4,}$</small> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u><span style='color:red'>title</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;CMV Total Ab<br />&nbsp;•&nbsp;EBV IgG Ab<br />&nbsp;•&nbsp;EBV IgM Ab<br />&nbsp;•&nbsp;HBcAb IgM<br />&nbsp;•&nbsp;HBcAb Total<br />&nbsp;•&nbsp;HCV Ab<br />&nbsp;•&nbsp;HBsAb<br />&nbsp;•&nbsp;HBsAg<br />&nbsp;•&nbsp;HCV 1 NAT<br />&nbsp;•&nbsp;HIV 1 NAT<br />&nbsp;•&nbsp;HIV I II Ab<br />&nbsp;•&nbsp;HIV I II Plus O Antibody<br />&nbsp;•&nbsp;RPR VDRL<br />&nbsp;•&nbsp;RPR</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
