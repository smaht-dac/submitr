=======
Analyte
=======



.. raw:: html

    Description of properties for the SMaHT Portal object type <b>Analyte</b>.
    
    Property names which are <span style='color:red'>red</span> are <i>required</i> properties;
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties.
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    Types referencing this type: <a href='Library.html'>Library</a>.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>components</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>molecule</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>samples</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>analyte_preparation</b> </td> <td> <a href=AnalytePreparation.html style='font-weight:bold;color:green;'>AnalytePreparation</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>a260_a280_ratio</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Ratio of nucleic acid absorbance at 260 nm and 280 nm, used to determine a measure of DNA purity. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>analyte_preparation</b> </td> <td width="15%" style="white-space:nowrap;"> <a href=AnalytePreparation.html style='font-weight:bold;color:green;'>AnalytePreparation</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to associated analyte preparation. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>components</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Biological features included in the analyte. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>concentration</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Analyte concentration. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>concentration_unit</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;ng/uL<br />&nbsp;•&nbsp;mg/mL</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Unit of the concentration. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>molecule</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Molecule of interest for the analyte. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>protocols</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Protocols providing experimental details. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>ribosomal_rna_ratio</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> The 28S/18S ribosomal RNA band ratio used to assess the quality of total RNA. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>rna_integrity_number</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Assessment of the integrity of RNA based on electrophoresis. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>rna_integrity_number_instrument</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Agilent Bioanalyzer<br />&nbsp;•&nbsp;Caliper Life Sciences LabChip GX</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Instrument used for RIN assessment. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>sample_quantity</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> The amount of sample used to generate the analyte. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>sample_quantity_unit</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;cells<br />&nbsp;•&nbsp;uL<br />&nbsp;•&nbsp;mL<br />&nbsp;•&nbsp;ug<br />&nbsp;•&nbsp;mg<br />&nbsp;•&nbsp;g</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Unit of the sample quantity. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>samples</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Link to associated samples. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br /><span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[A-Z0-9]{3,}_ANALYTE_[A-Z0-9-_.]{4,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>volume</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Analyte volume. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>volume_unit</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;uL<br />&nbsp;•&nbsp;mL</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> Unit of the volume. </td> </tr> </table>
    <p />
