====
TissueCollection
====

Description of properties for the SMaHT Portal schema for **TissueCollection**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>donor</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>tags</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Identifier on submission. </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>protocols</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Protocols providing experimental details. </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>alternate_accessions</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>blood_cultures_available</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Whether blood cultures were drawn during tissue collection. </td> </tr> <tr> <td width="5%"> <b>chest_incision_datetime</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Date and time of chest incision for tissue collection. </td> </tr> <tr> <td width="5%"> <b>collection_site</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Site of tissue collection. </td> </tr> <tr> <td width="5%"> <b>core_body_temperature</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Body temperature of the donor during tissue collection in degrees Celsius. </td> </tr> <tr> <td width="5%"> <b>core_body_temperature_location</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Location of body temperature measurement for the donor during tissue collection. </td> </tr> <tr> <td width="5%"> <b>cross_clamp_applied_datetime</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Date and time when cross clamp was applied during tissue collection. </td> </tr> <tr> <td width="5%"> <b>donor_type</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>ischemic_time</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Time interval in minutes of ischemia for tissue collection. </td> </tr> <tr> <td width="5%"> <b>organ_transplant</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Whether the donor had organs removed for transplant. </td> </tr> <tr> <td width="5%"> <b>organs_transplanted</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> The organs of the donor that were transplanted. </td> </tr> <tr> <td width="5%"> <b>recovery_kit_id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Identifier of the tissue recovery kit. </td> </tr> <tr> <td width="5%"> <b>refrigeration_prior_to_procurement</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Whether the donor was refrigerated prior to tissue collection. </td> </tr> <tr> <td width="5%"> <b>refrigeration_prior_to_procurement_time</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Interval of time in hours the donor was refrigerated prior to tissue collection. </td> </tr> <tr> <td width="5%"> <b>ventilator_less_than_24_hours</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Whether donor was on a ventilator less than 24 hours prior to tissue collection. </td> </tr> <tr> <td width="5%"> <b>donor</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Link to the associated donor. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
