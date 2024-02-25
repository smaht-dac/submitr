================
TissueCollection
================



.. raw:: html

    Description of properties for the SMaHT Portal object type <b>TissueCollection</b>.
    
    Property names which are <span style='color:red'>red</span> are <i>required</i> properties;
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties.
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties. <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>donor</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>donor</b> </td> <td> <a href=Donor.html style='font-weight:bold;color:green;'>Donor</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>blood_cultures_available</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Yes<br />&nbsp;•&nbsp;No<br />&nbsp;•&nbsp;Unknown</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Whether blood cultures were drawn during tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>chest_incision_datetime</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: date-time<br /> </td> <td width="80%"> Date and time of chest incision for tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>collection_site</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;TBD</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Site of tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>core_body_temperature</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Body temperature of the donor during tissue collection in degrees Celsius. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>core_body_temperature_location</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Axilla<br />&nbsp;•&nbsp;Anus</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Location of body temperature measurement for the donor during tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>cross_clamp_applied_datetime</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: date-time<br /> </td> <td width="80%"> Date and time when cross clamp was applied during tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>donor</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Donor.html style='font-weight:bold;color:green;'>Donor</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated donor. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>donor_type</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;TBD</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>ischemic_time</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Time interval in minutes of ischemia for tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>organ_transplant</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Yes<br />&nbsp;•&nbsp;No<br />&nbsp;•&nbsp;Unknown</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Whether the donor had organs removed for transplant. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>organs_transplanted</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> The organs of the donor that were transplanted. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>protocols</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Protocols providing experimental details. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>recovery_kit_id</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier of the tissue recovery kit. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>refrigeration_prior_to_procurement</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Yes<br />&nbsp;•&nbsp;No<br />&nbsp;•&nbsp;Unknown</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Whether the donor was refrigerated prior to tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>refrigeration_prior_to_procurement_time</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Interval of time in hours the donor was refrigerated prior to tissue collection. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br /><span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[A-Z0-9]{3,}_TISSUE-COLLECTION_[A-Z0-9-_.]{4,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>ventilator_less_than_24_hours</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Yes<br />&nbsp;•&nbsp;No<br />&nbsp;•&nbsp;Unknown</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Whether donor was on a ventilator less than 24 hours prior to tissue collection. </td> </tr> </table>
    <p />
