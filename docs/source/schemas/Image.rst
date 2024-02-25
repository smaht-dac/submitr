=====
Image
=====



.. raw:: html

    Description of properties for the SMaHT Portal 
    object type <a target="_blank" href="https://data.smaht.org/profiles/Image.json?format=json" style="color:black"><b>Image</b> 🔗</a>.
    
    Property names which are <span style='color:red'>red</span> are <i>required</i> properties;
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties.
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    
    <p />
    



Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>aliases</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|




Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>attachment</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> File attached to this Item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> blob_id</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> download</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> File Name of the attachment. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> height</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Height of the image attached, in pixels. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> href</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Path to download the file attached to this Item. [Internal webapp URL for document file] </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> md5sum</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Use this to ensure that your file was downloaded without errors or corruption. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> size</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Size of the attachment on disk. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> <u>type</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;application/msword<br />&nbsp;•&nbsp;application/vnd.ms-excel<br />&nbsp;•&nbsp;application/vnd.openxmlformats-o<br />&nbsp;&nbsp;&nbsp;fficedocument.spreadsheetml.sheet<br />&nbsp;•&nbsp;application/pdf<br />&nbsp;•&nbsp;application/zip<br />&nbsp;•&nbsp;application/proband+xml<br />&nbsp;•&nbsp;text/plain<br />&nbsp;•&nbsp;text/tab-separated-values<br />&nbsp;•&nbsp;image/jpeg<br />&nbsp;•&nbsp;image/tiff<br />&nbsp;•&nbsp;image/gif<br />&nbsp;•&nbsp;text/html<br />&nbsp;•&nbsp;image/png<br />&nbsp;•&nbsp;image/svs<br />&nbsp;•&nbsp;text/autosql</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>attachment</span> <b>.</b> width</b> </td> <td width="15%" style="white-space:nowrap;"> <b>integer</b> </td> <td width="80%"> Width of the image attached, in pixels. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>caption</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Last generated: Sunday, February 25, 2024 | 12:56 PM EST | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a></small> ]
