==========
Sequencing
==========



..    View <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing" style="color:black"><b><i><u>objects</u></i></b></a>
..    of this type: <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:2pt;" /></a>

.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json" style="color:black"><b><u>Sequencing</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    
    
    Types <b>referencing</b> this type are: <a href='aligned_reads.html'><u>AlignedReads</u></a>, <a href='file.html'><u>File</u></a>, <a href='file_set.html'><u>FileSet</u></a>, <a href='histology_image.html'><u>HistologyImage</u></a>, <a href='output_file.html'><u>OutputFile</u></a>, <a href='reference_file.html'><u>ReferenceFile</u></a>, <a href='submitted_file.html'><u>SubmittedFile</u></a>, <a href='supplementary_file.html'><u>SupplementaryFile</u></a>, <a href='unaligned_reads.html'><u>UnalignedReads</u></a>, <a href='variant_calls.html'><u>VariantCalls</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    <p />
    <br /><u>Description</u>: Sequencing items contain information on the sequencing of libraries.


.. tip::

  .. raw::  html

    <i>See actual Sequencing data <a target='_blank' href='https://data.smaht.org/search/?type=Sequencing'><b>here<span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></b></a></i>


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>read_type</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>sequencer</span></b> </td> <td width="10%"> <a href='sequencer.html'><b style='color:green;'><u>Sequencer</u></b></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>target_read_length</span></b> </td> <td width="10%"> integer </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b>preparation_kits</b> </td> <td width="10%"> <a href=preparation_kit.html style='font-weight:bold;color:green;'><u>PreparationKit</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b>protocols</b> </td> <td width="10%"> <a href=protocol.html style='font-weight:bold;color:green;'><u>Protocol</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>sequencer</span></b> </td> <td width="10%"> <a href=sequencer.html style='font-weight:bold;color:green;'><u>Sequencer</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Consortia associated with this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>flow_cell</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Flow cell used for sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>movie_length</b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Length of movie used in sequencing (hours). </td> </tr> <tr> <td style="white-space:nowrap;"> <b>on_target_rate</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> An expected ratio, the number of reads with enrichment signals for the targeted element versus the overall reads sequenced. Relevant for target capture sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>preparation_kits</b> </td> <td style="white-space:nowrap;"> <u><a href=preparation_kit.html style='font-weight:bold;color:green;'><u>PreparationKit</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Links to sequencing preparation kits. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>protocols</b> </td> <td style="white-space:nowrap;"> <u><a href=protocol.html style='font-weight:bold;color:green;'><u>Protocol</u></a></u><br />•&nbsp;array of string<br />•&nbsp;min items: 1<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Protocols providing experimental details. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u><span style='color:red'>read_type</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Paired-end<br />&nbsp;•&nbsp;Single-end</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Type of reads obtained from sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>sequencer</span></b> </td> <td style="white-space:nowrap;"> <u><a href=sequencer.html style='font-weight:bold;color:green;'><u>Sequencer</u></a></u><br />•&nbsp;string<br /> </td> <td> Instrument used for sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;restricted</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers that created this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique identifier for the item assigned by the submitter.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_SEQUENCING_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9|_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_coverage</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected coverage for the sequencing. For Duplex sequencing, this applies to the target duplex coverage for sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_monomer_length</b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Target monomer length for Kinnex/MAS-Seq (bp). </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_read_count</b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected read count for the sequencing, in read pairs if paired-end. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>target_read_length</span></b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected read length for the sequencing (bp). </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
