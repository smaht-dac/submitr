=====
Image
=====



.. raw:: html

    Summary of <a target="_blank" href="https://data.smaht.org" style="color:black">SMaHT Portal</a> 
    <a target="_blank" href="https://data.smaht.org/search/?type=Image&format=json" style="color:black">object</a> <a target="_blank" href="https://data.smaht.org/profiles/Image.json?format=json" style="color:black">type</a>
    <a target="_blank" href="https://data.smaht.org/profiles/Image.json" style="color:black"><b><u>Image</u></b></a><a target="_blank" href="https://data.smaht.org/profiles/Image.json"><span class="fa fa-external-link" style="position:relative;top:1pt;left:4pt;color:black;" /></a> .
    
    
    Types <b>referencing</b> this type are: <a href='histology.html'><u>Histology</u></a>.
    Property names in <span style='color:red'><b>red</b></span> are
    <a href="#required-properties" style="color:#222222"><i><b><u>required</u></b></i></a> properties;
    those in <span style='color:blue'><b>blue</b></span> are
    <a href="#identifying-properties" style="color:#222222"><i><b><u>identifying</u></b></i></a> properties;
    and properties with types in <span style='color:green'><b>green</b></span> are
    <a href="#reference-properties" style="color:#222222"><i><b><u>reference</u></b></i></a> properties.
    View <a target="_blank" href="https://data.smaht.org/search/?type=Image" style="color:black"><b><i><u>objects</u></i></b></a>
    of this type <a target="_blank" href="https://data.smaht.org/search/?type=Image"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a>
    <p />
    





Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td width="5%"> <b><span style='color:blue'>aliases</span></b> </td> <td width="10%"> array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td width="10%"> string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </td> <th width="15%" > Type </td> <th width="80%"> Description </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td width="10%"> <a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small></td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td width="10%"> <a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a><br />array of string </td> <td width="85%"> <i>See <a href="#properties">below</a> for more details.</i> <br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small></td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th width="5%"> Property </th> <th width="15%"> Type </th> <th width="80%"> Description </th> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Institution-specific ID (e.g. bgm:cohort-1234-a).<br />Must adhere to (regex) <span style='color:darkblue;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[^\s\\\/]+:[^\s\\\/]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>attachment</b> </td> <td style="white-space:nowrap;"> <b>object</b> </td> <td> File attached to this Item. </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> blob_id</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> download</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> File Name of the attachment. </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> height</b> </td> <td style="white-space:nowrap;"> <b>integer</b> </td> <td> Height of the image attached, in pixels. </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> href</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Path to download the file attached to this Item. [Internal webapp URL for document file] </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> md5sum</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Use this to ensure that your file was downloaded without errors or corruption. </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> size</b> </td> <td style="white-space:nowrap;"> <b>integer</b> </td> <td> Size of the attachment on disk. </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> <u>type</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;application/msword<br />&nbsp;•&nbsp;application/pdf<br />&nbsp;•&nbsp;application/proband+xml<br />&nbsp;•&nbsp;application/vnd.ms-excel<br />&nbsp;•&nbsp;application/vnd.openxmlformats-o<br />&nbsp;&nbsp;&nbsp;fficedocument.spreadsheetml.sheet<br />&nbsp;•&nbsp;application/zip<br />&nbsp;•&nbsp;image/gif<br />&nbsp;•&nbsp;image/jpeg<br />&nbsp;•&nbsp;image/png<br />&nbsp;•&nbsp;image/svs<br />&nbsp;•&nbsp;image/tiff<br />&nbsp;•&nbsp;text/autosql<br />&nbsp;•&nbsp;text/html<br />&nbsp;•&nbsp;text/plain<br />&nbsp;•&nbsp;text/tab-separated-values</span></b> </td> <td style="white-space:nowrap;"> <b>enum</b> of <b>string</b> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> width</b> </td> <td style="white-space:nowrap;"> <b>integer</b> </td> <td> Width of the image attached, in pixels. </td> </tr><tr> <td style="white-space:nowrap;"> <b>caption</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>consortia</b> </td> <td style="white-space:nowrap;"> <u><a href=consortium.html style='font-weight:bold;color:green;'><u>Consortium</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br />•&nbsp;restricted<br /> </td> <td> Consortia associated with this item.<br /><small><i>Click <a href='../../consortia.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>description</b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Plain text description of the item. </td> </tr> <tr> <td style="white-space:nowrap;"> <b>display_title</b> </td> <td style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;deleted<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;released</span></b> </td> <td style="white-space:nowrap;"> <u><b>enum</b> of <b>string</b></u><br />•&nbsp;default: in review<br /> </td> <td> - </td> </tr> <tr> <td style="white-space:nowrap;"> <b>submission_centers</b> </td> <td style="white-space:nowrap;"> <u><a href=submission_center.html style='font-weight:bold;color:green;'><u>SubmissionCenter</u></a></u><br />•&nbsp;array of string<br />•&nbsp;unique<br /> </td> <td> Submission Centers associated with this item.<br /><small><i>Click <a href='../../submission_centers.html'>here</a> to see values.</i></small> </td> </tr> <tr> <td style="white-space:nowrap;"> <b>tags</b> </td> <td style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;min string length: 1<br />•&nbsp;max string length: 50<br />•&nbsp;unique<br /> </td> <td> Key words that can tag an item - useful for filtering.<br />Must adhere to (regex) <span style='color:inherit;'><u>pattern</u>:&nbsp;<small style='font-family:monospace;'><b>^[a-zA-Z0-9_-]+$</b></small></span> </td> </tr> <tr> <td style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td style="white-space:nowrap;"> <b>string</b> </td> <td> Unique ID by which this object is identified. </td> </tr> </table>
    <p />
