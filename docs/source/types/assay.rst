=====
Assay
=====



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Assay&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Assay.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Assay.json" style="color:black"><b><u>Assay</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Assay.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    
    
    Types <b>referencing</b> this type are: <a href='file_set.html'><u>FileSet</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    View <a target="_blank" href="https://data.smaht.org/search/?type=Assay" style="color:black"><b><i><u>objects</u></i></b></a>
    of this type <a target="_blank" href="https://data.smaht.org/search/?type=Assay"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a>
    <p />
    



Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:red'>code</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>identifier</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>title</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr style="margin-top:0;margin-bottom:0;"> <td style="padding-top:3pt;padding-bottom:3pt;border-top:2px solid #2E86C1;border-bottom:2px solid #2E86C1;color:darkred;" colSpan="3"> <i>At least <u>one</u> of the following ...</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:darkred'>consortia</span></b> </td> <td width="10%"> <a href='consortium.html'><b style='color:green;'><u>Consortium</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../consortia.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b><span style='color:darkred'>submission_centers</span></b> </td> <td width="10%"> <a href='submission_center.html'><b style='color:green;'><u>SubmissionCenter</u></b></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../submission_centers.html'>here</a> to see values.</i></small></td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>accession</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>identifier</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../consortia.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../submission_centers.html'>here</a> to see values.</i></small></td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>accession</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> A unique identifier to be used to reference the object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b>alternate_accessions</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;restricted<br /> </td> <td> Accessions previously assigned to objects that have been merged with this object. [Only admins are allowed to set or update this value.] </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>code</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Code used in file naming scheme.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[0-9]$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Consortia associated with this item.<br /><small><i>Click <a href='../consortia.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>description</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Plain text description of the item. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;min length: 2<br /> </td> <td> Unique, identifying name for the item.<br />Must adhere to (regex) <span style='color:darkred;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[A-Za-z0-9-_]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>submission_centers</b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers associated with this item.<br /><small><i>Click <a href='../submission_centers.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:red'>title</span></b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;min length: 3<br /> </td> <td> Title for the item. </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
