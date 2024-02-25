====
Sequencing
====

.. raw:: html

    Description of properties for the SMaHT Portal schema for <b>Sequencing</b>.
    
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    In the <i>Properties</i> section, properties in <span style='color:red'>red</span> are <i>required</i> properties,
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>read_type</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>sequencer</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>target_read_length</b> </td> <td> integer </td> <td> <i>See below for more details.</i> </td> </tr> </table>
|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>accession</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>submitted_id</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>
|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>sequencer</b> </td> <td> <a href=Sequencer.html style='font-weight:bold;color:green;'>Sequencer</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>
|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>flow_cell</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Flow cell used for sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>movie_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Length of movie used in sequencing (hours). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>protocols</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Protocols providing experimental details. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u><span style='color:red'>read_type</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Paired-end<br />&nbsp;•&nbsp;Single-end</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Type of reads obtained from sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>sequencer</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Sequencer.html style='font-weight:bold;color:green;'>Sequencer</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Instrument used for sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br /><b>pattern</b>: <small style='font-family:monospace;'>^[A-Z0-9]{3,}_SEQUENCING_[A-Z0-9-_.]{4,}$</small> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>target_coverage</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Expected coverage for the sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>target_read_count</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Expected read count for the sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>target_read_length</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Expected read length for the sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> </table>
    <p />
