====
Sequencing
====

Description of properties for the SMaHT Portal schema for **Sequencing**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>read_type</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>sequencer</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>target_read_length</b> </td> <td> integer </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>tags</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Identifier on submission. </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>protocols</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Protocols providing experimental details. </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>alternate_accessions</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%"> <b>flow_cell</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Flow cell used for sequencing. </td> </tr> <tr> <td width="5%"> <b>movie_length</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Length of movie used in sequencing (hours). </td> </tr> <tr> <td width="5%"> <b>read_type</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Type of reads obtained from sequencing. </td> </tr> <tr> <td width="5%"> <b>target_coverage</b> </td> <td> number </td> <td> property-attributes-todo </td> <td> Expected coverage for the sequencing. </td> </tr> <tr> <td width="5%"> <b>target_read_count</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Expected read count for the sequencing. </td> </tr> <tr> <td width="5%"> <b>target_read_length</b> </td> <td> integer </td> <td> property-attributes-todo </td> <td> Expected read length for the sequencing. </td> </tr> <tr> <td width="5%"> <b>sequencer</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Instrument used for sequencing. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
