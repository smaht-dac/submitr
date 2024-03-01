==========
Sequencing
==========



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json" style="color:black"><b><u>Sequencing</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Sequencing.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    
    
    Types <b>referencing</b> this type are: <a href='file_set.html'><u>FileSet</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    View <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing" style="color:black"><b><i><u>objects</u></i></b></a>
    of this type <a target="_blank" href="https://data.smaht.org/search/?type=Sequencing"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a>
    <p />
    



Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>instrument_model</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>platform</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>read_type</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>target_read_length</span></b> </td> <td width="10%"> integer </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b>protocols</b> </td> <td width="10%"> <a href=protocol.html style='font-weight:bold;color:green;'><u>Protocol</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b>sequencer</b> </td> <td width="10%"> <a href=sequencer.html style='font-weight:bold;color:green;'><u>Sequencer</u></a><br />string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small></td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Consortia associated with this item.<br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>flowcell</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Flowcell used for sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u><span style='color:red'>instrument_model</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;NovaSeq<br />&nbsp;•&nbsp;NovaSeq 6000<br />&nbsp;•&nbsp;NovaSeq X<br />&nbsp;•&nbsp;NovaSeq X Plus<br />&nbsp;•&nbsp;PromethION<br />&nbsp;•&nbsp;Revio<br />&nbsp;•&nbsp;UG100<br />&nbsp;•&nbsp;Ultralong Promethion R10<br />&nbsp;•&nbsp;Xenium</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Model of instrument used to obtain data. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u><span style='color:red'>platform</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;10X Genomics<br />&nbsp;•&nbsp;Illumina<br />&nbsp;•&nbsp;ONT<br />&nbsp;•&nbsp;PacBio<br />&nbsp;•&nbsp;Ultima</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Name of the platform used to obtain data. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>protocols</b> </td> <td style="white-space:nowrap;"> <u><a href=protocol.html style='font-weight:bold;color:green;'><u>Protocol</u></a></u><br />•&nbsp;array of string<br />•&nbsp;min items: 1<br />•&nbsp;unique<br /> </td> <td> Protocols providing experimental details. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u><span style='color:red'>read_type</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Not Applicable<br />&nbsp;•&nbsp;Paired-end<br />&nbsp;•&nbsp;Single-end</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> Type of reads obtained from sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>sequencer</b> </td> <td style="white-space:nowrap;"> <u><b><a href=sequencer.html style='font-weight:bold;color:green;'><u>Sequencer</u></a></b></u><br />•&nbsp;string<br /> </td> <td> Instrument used for sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers associated with this item.<br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Identifier on submission.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Z0-9]{3,}_SEQUENCING_[A-Z0-9-_.]{4,}$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_coverage</b> </td> <td style="white-space:nowrap;"> <u><b>number</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected coverage for the sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>target_read_count</b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected read count for the sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>target_read_length</span></b> </td> <td style="white-space:nowrap;"> <u><b>integer</b></u><br />•&nbsp;min value: 0<br /> </td> <td> Expected read length for the sequencing. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
