======
Tissue
======



.. raw:: html

    Summary of properties for the SMaHT Portal 
    object type <a target="_blank" href="https://data.smaht.org/profiles/Tissue.json?format=json" style="color:black"><b><u>Tissue</u></b> 🔗</a>.
    Its <b>parent</b> type is: <a href=SampleSource.html><u>SampleSource</u></a>.
    
    Types <b>referencing</b> this type are: <a href='Histology.html'><u>Histology</u></a>.
    Property names which are <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    and those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties.
    Properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>donor</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submission_centers</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>uberon_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>submitted_id</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>donor</b> </td> <td> <a href=Donor.html style='font-weight:bold;color:green;'>Donor</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td width="15%" style="white-space:nowrap;"> <b>array</b> of <b>string</b> </td> <td width="80%"> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>donor</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=Donor.html style='font-weight:bold;color:green;'>Donor</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> Link to the associated donor. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>ischemic_time</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Time interval of ischemia in minutes. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>pathology_notes</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Notes from pathologist report on the tissue. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>ph</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> pH of the tissue. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>preservation_time_interval</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Time interval from beginning of tissue recovery until placed in preservation media in minutes. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>prosector_notes</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Notes from prosector report on the tissue recovery. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>recovery_datetime</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: date | date-time<br /> </td> <td width="80%"> Date and time of tissue recovery. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>recovery_interval</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Total time interval of tissue recovery in minutes. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>sample_count</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Number of samples produced for this source. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>size</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Size of the tissue in cubic centimeters. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submission_centers</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>submitted_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Identifier on submission.<br />Must adhere to (regex) <span style='color:red;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'>^[A-Z0-9]{3,}_TISSUE_[A-Z0-9-_.]{4,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>uberon_id</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Uberon identifier for the tissue.<br />Must adhere to (regex) <span style='color:red;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'>^UBERON:[0-9]$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>volume</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Volume of the tissue in milliliters. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>weight</b> </td> <td width="15%" style="white-space:nowrap;"> <b>number</b> </td> <td width="80%"> Weight of the tissue in grams. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Sunday, February 25, 2024 | 3:53 PM EST | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a></small> ]
