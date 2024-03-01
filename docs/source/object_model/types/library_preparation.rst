==================
LibraryPreparation
==================



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=LibraryPreparation&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/LibraryPreparation.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/LibraryPreparation.json" style="color:black"><b><u>LibraryPreparation</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/LibraryPreparation.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    Its <b>parent</b> type is: <a href=preparation.html><u>Preparation</u></a>.
    
    Types <b>referencing</b> this type are: <a href='library.html'><u>Library</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    View <a target="_blank" href="https://data.smaht.org/search/?type=LibraryPreparation" style="color:black"><b><i><u>objects</u></i></b></a>
    of this type <a target="_blank" href="https://data.smaht.org/search/?type=LibraryPreparation"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a>
    <p />
    



Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>assay_name</span></b> </td> <td width="10%"> array of enum </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b>preparation_kits</b> </td> <td width="10%"> <a href=preparation_kit.html style='font-weight:bold;color:green;'><u>PreparationKit</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b>treatments</b> </td> <td width="10%"> <a href=treatment.html style='font-weight:bold;color:green;'><u>Treatment</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>adapter_inclusion_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Ligation<br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Tagmentation</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Method of library preparation from an analyte. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>amplification_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;MALBAC<br />&nbsp;•&nbsp;MDA<br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;PCR<br />&nbsp;•&nbsp;PTA</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Amplification method used to increase library products. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u><span style='color:red'>assay_name</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;ATAC-Seq<br />&nbsp;•&nbsp;CODEC<br />&nbsp;•&nbsp;DLP+<br />&nbsp;•&nbsp;Duplex Sequencing<br />&nbsp;•&nbsp;FiberSeq<br />&nbsp;•&nbsp;MAS-Seq<br />&nbsp;•&nbsp;NanoSeq<br />&nbsp;•&nbsp;RNA-Seq<br />&nbsp;•&nbsp;STORM-Seq<br />&nbsp;•&nbsp;ScRNA-Seq<br />&nbsp;•&nbsp;WGS</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Name of experimental approach. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Consortia associated with this item.<br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>fragmentation_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Restriction Enzyme<br />&nbsp;•&nbsp;Sonication<br />&nbsp;•&nbsp;Transposase</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Method used for nucleotide fragmentation. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>insert_selection_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Affinity Enrichment<br />&nbsp;•&nbsp;Hybrid Selection<br />&nbsp;•&nbsp;Not applicable<br />&nbsp;•&nbsp;PCR<br />&nbsp;•&nbsp;PolyT Enrichment<br />&nbsp;•&nbsp;RRNA Depletion</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Method for selecting inserts included in library. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>preparation_kits</b> </td> <td style="white-space:nowrap;"> <u><a href=preparation_kit.html style='font-weight:bold;color:green;'><u>PreparationKit</u></a></u><br />•&nbsp;array of string<br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Links to associated preparation kits. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>size_selection_method</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Gel Electrophoresis<br />&nbsp;•&nbsp;Magnetic Beads<br />&nbsp;•&nbsp;Not Applicable</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>enum</b></u><br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Method for selecting fragment sizes. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>strand</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;First Stranded<br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Second Stranded<br />&nbsp;•&nbsp;Unstranded</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Library stranded-ness. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers associated with this item.<br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Identifier on submission.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_LIBRARY-PREPARATION_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_fragment_length</b> </td> <td style="white-space:nowrap;"> <b>integer</b> </td> <td> Desired fragment length for the library. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_insert_length</b> </td> <td style="white-space:nowrap;"> <b>integer</b> </td> <td> Desired insert length for the library. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>treatments</b> </td> <td style="white-space:nowrap;"> <u><a href=treatment.html style='font-weight:bold;color:green;'><u>Treatment</u></a></u><br />•&nbsp;array of string<br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Link to associated treatments performed during library preparation. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>trim_adapter_sequence</b> </td> <td style="white-space:nowrap;"> <b>boolean</b> </td> <td> Whether trimming adapter sequence is recommended. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />