======
Tissue
======



..    View <a target="_blank" href="https://data.smaht.org/search/?type=Tissue" style="color:black"><b><i><u>objects</u></i></b></a>
..    of this type: <a target="_blank" href="https://data.smaht.org/search/?type=Tissue"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:2pt;" /></a>

.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Tissue&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Tissue.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Tissue.json" style="color:black"><b><u>Tissue</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Tissue.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    Its <b><a href='../type_hierarchy.html' style='color:black;'>parent</a></b> type is: <a href=sample_source.html><u>SampleSource</u></a>.
    
    Types <b>referencing</b> this type are: <a href='aligned_reads.html'><u>AlignedReads</u></a>, <a href='donor.html'><u>Donor</u></a>, <a href='file.html'><u>File</u></a>, <a href='histology_image.html'><u>HistologyImage</u></a>, <a href='output_file.html'><u>OutputFile</u></a>, <a href='reference_file.html'><u>ReferenceFile</u></a>, <a href='submitted_file.html'><u>SubmittedFile</u></a>, <a href='supplementary_file.html'><u>SupplementaryFile</u></a>, <a href='unaligned_reads.html'><u>UnalignedReads</u></a>, <a href='variant_calls.html'><u>VariantCalls</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    <p />
    <br /><u>Description</u>: Tissues collected from an individual.


.. tip::

  .. raw::  html

    <i>See actual Tissue data <a target='_blank' href='https://data.smaht.org/search/?type=Tissue'><b>here<span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></b></a></i>


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>donor</span></b> </td> <td width="10%"> <a href='donor.html'><b style='color:green;'><u>Donor</u></b></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>external_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>uberon_id</span></b> </td> <td width="10%"> <a href='ontology_term.html'><b style='color:green;'><u>OntologyTerm</u></b></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>donor</span></b> </td> <td width="10%"> <a href=donor.html style='font-weight:bold;color:green;'><u>Donor</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>uberon_id</span></b> </td> <td width="10%"> <a href=ontology_term.html style='font-weight:bold;color:green;'><u>OntologyTerm</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>anatomical_location</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Anatomical location of the tissue in the donor. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>code</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;unique<br /> </td> <td> Code used in file naming scheme. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Consortia associated with this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=Consortium'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>donor</span></b> </td> <td style="white-space:nowrap;"> <u><a href=donor.html style='font-weight:bold;color:green;'><u>Donor</u></a></u><br />•&nbsp;string<br /> </td> <td> Link to the associated donor. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>external_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> External ID for the item provided by submitter.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Za-z0-9-_]{3,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>ischemic_time</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Time interval of ischemia (hours). </td> </tr> <tr> <td style="white-space:nowrap;"> <b>pathology_notes</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Notes from pathologist report on the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>ph</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br />•&nbsp;max value: 14<br /> </td> <td> pH of the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>preservation_medium</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Medium used for preservation. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>preservation_type</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Fixed<br />&nbsp;•&nbsp;Fresh<br />&nbsp;•&nbsp;Frozen<br />&nbsp;•&nbsp;Snap Frozen</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Method of preservation. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>prosector_notes</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Notes from prosector report on the tissue recovery. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>sample_count</b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Number of samples produced from the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>size</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Size of the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>size_unit</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;cm^2<br />&nbsp;•&nbsp;cm^3</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Unit of measurement for size of the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;restricted</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers that created this item.<br /><i>See values <a target='_blank' href='https://data.smaht.org/search/?type=SubmissionCenter'><b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></a></i> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique identifier for the item assigned by the submitter.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_TISSUE_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9|_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>uberon_id</span></b> </td> <td style="white-space:nowrap;"> <u><a href=ontology_term.html style='font-weight:bold;color:green;'><u>OntologyTerm</u></a></u><br />•&nbsp;string<br /> </td> <td> Uberon Ontology identifier for the tissue. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>volume</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Volume of the tissue (mL). </td> </tr> <tr> <td style="white-space:nowrap;"> <b>weight</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Weight of the tissue (g). </td> </tr> </table>
    <p />
