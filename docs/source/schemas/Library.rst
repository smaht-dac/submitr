=======
Library
=======



.. raw:: html

    Summary of properties for the <a target="_blank" href="https://data.smaht.org/search/?type=Library">SMaHT Portal</a> 
    object type <a target="_blank" href="https://data.smaht.org/profiles/Library.json?format=json" style="color:black"><b><u>Library</u></b> 🔗</a>.
    
    
    Types <b>referencing</b> this type are: <a href='FileSet.html'><u>FileSet</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties;
    and properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>analyte</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>analyte</b> </td> <td> <a href=Analyte.html style='font-weight:bold;color:green;'><u>Analyte</u></a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>library_preparation</b> </td> <td> <a href=LibraryPreparation.html style='font-weight:bold;color:green;'><u>LibraryPreparation</u></a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>a260_a280_ratio</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Ratio of nucleic acid absorbance at 260 nm and 280 nm, used to determine a measure of DNA purity. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>adapter_name</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Name of sequencing adapter. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>adapter_sequence</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Base sequence of sequencing adapter. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>amplification_cycles</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Number of PCR Cycles used for additional amplification. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>amplification_end_mass</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Weight of analyte after PCR (ng). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>amplification_start_mass</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Weight of analyte prior to PCR (ng). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>analyte</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Analyte.html style='font-weight:bold;color:green;'><u>Analyte</u></a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to associated analyte. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>analyte_weight</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Weight of analyte used to prepare library (mg). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>barcode_sequences</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Barcode sequence for multiplexed sequencing. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>fragment_maximum_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Maximum length of the sequenced fragments (e.g., as predicted by Agilent Bioanalyzer). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>fragment_mean_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Mean length of the sequenced fragments (e.g., as predicted by Agilent Bioanalyzer). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>fragment_minimum_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Minimum length of the sequenced fragments (e.g., as predicted by Agilent Bioanalyzer). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>fragment_standard_deviation_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Standard deviation of length of the sequenced fragments (e.g., as predicted by Agilent Bioanalyzer). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>insert_maximum_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Maximum length of the sample molecule in the fragments to be sequenced. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>insert_mean_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Mean length of the sample molecule in the fragments to be sequenced. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>insert_minimum_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Minimum length of the sample molecule in the fragments to be sequenced. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>insert_standard_deviation_length</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Standard deviation of the length of the sample molecule in the fragments to be sequenced. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>library_preparation</b> </td> <td width="15%" style="white-space:nowrap;"> <a href=LibraryPreparation.html style='font-weight:bold;color:green;'><u>LibraryPreparation</u></a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to associated library preparation. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>preparation_date</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: date<br /> </td> <td width="80%"> Date of library preparation. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>protocols</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Protocols providing experimental details. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br />Must adhere to (regex) <span style='color:red;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'>^[A-Z0-9]{3,}_LIBRARY_[A-Z0-9-_.]{4,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Sunday, February 25, 2024 | 6:13 PM EST | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a> | v1.0</small> ]
