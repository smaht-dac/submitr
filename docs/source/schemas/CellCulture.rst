====
CellCulture
====

Description of properties for the SMaHT Portal schema for **CellCulture**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>cell_line</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>sample_count</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Number of samples produced for this source. </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Identifier on submission. </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>tags</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>protocols</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Protocols providing experimental details. </td> </tr> <tr> <td width="5%"> <b>description</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Plain text description of the item. </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>alternate_accessions</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>culture_duration</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Total number of culturing days. </td> </tr> <tr> <td width="5%"> <b>culture_harvest_date</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> YYYY-MM-DD format date for cell culture harvest. </td> </tr> <tr> <td width="5%"> <b>culture_start_date</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> YYYY-MM-DD format date for cell culture start date. </td> </tr> <tr> <td width="5%"> <b>doubling_number</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Number of times the population has doubled since the time of culture start date until harvest. </td> </tr> <tr> <td width="5%"> <b>doubling_time</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Average time from culture start date until harvest it takes for the population to double (hours). </td> </tr> <tr> <td width="5%"> <b>growth_medium</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Medium used for cell culture. </td> </tr> <tr> <td width="5%"> <b>karyotype</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Chromosome count and any noted rearrangements or copy number variation. </td> </tr> <tr> <td width="5%"> <b>lot_number</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Lot number of cell line. </td> </tr> <tr> <td width="5%"> <b>passage_number</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Number of times the cell line has been passaged since the culture start date until harvest. </td> </tr> <tr> <td width="5%"> <b>cell_line</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Cell line used for the cell culture. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
