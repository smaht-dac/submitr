================
SubmissionCenter
================



.. raw:: html

    Description of properties for the SMaHT Portal 
    object type <a target="_blank" href="https://data.smaht.org/profiles/SubmissionCenter.json?format=json" style="color:black"><b>SubmissionCenter</b> 🔗</a>.
    
    Property names which are <span style='color:red'>red</span> are <i>required</i> properties;
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties.
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    Types referencing this type: <a href='AlignedReads.html'>AlignedReads</a>, <a href='File.html'>File</a>, <a href='OutputFile.html'>OutputFile</a>, <a href='ReferenceFile.html'>ReferenceFile</a>, <a href='SubmittedFile.html'>SubmittedFile</a>, <a href='UnalignedReads.html'>UnalignedReads</a>, <a href='VariantCalls.html'>VariantCalls</a>.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>code</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>identifier</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>title</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>aliases</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>identifier</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Reference Properties
~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>leader</b> </td> <td> <a href=User.html style='font-weight:bold;color:green;'>User</a><br /><span style='color:green;'>string</span> </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>code</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Code used in file naming scheme.<br />Must adhere to (regex) <span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[a-z0-9]{3,}$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique, identifying name for the item.<br />Must adhere to (regex) <span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[A-Za-z0-9-_]+$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>leader</b> </td> <td width="15%" style="white-space:nowrap;"> <a href=User.html style='font-weight:bold;color:green;'>User</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> The leader of the submission center. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>static_content</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>object</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Array of objects containing linkTo UserContent and 'position' to be placed on Item view(s). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>static_content</span> <b>.</b> <span style='color:red'>content</span></b> </td> <td width="15%" style="white-space:nowrap;"> <a href=UserContent.html style='font-weight:bold;color:green;'>UserContent</a><br /><span style='color:green;'>string</span> </td> <td width="80%"> A UserContent Item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>static_content</span> <b>.</b> description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Description or note about this content. Might be displayed as a footnote or caption, if applicable for view. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>static_content</span> <b>.</b> <span style='color:red'>location</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b><span style='font-weight:normal'><br />•&nbsp;default: header</span> </td> <td width="80%"> Where this content should be displayed. Item schemas could potentially define an enum to contrain values. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>static_headers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Array of linkTos for static sections to be displayed at the top of an item page. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;in review<br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>title</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>url</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: uri<br /> </td> <td width="80%"> An external resource with additional information about the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Last generated: 12:54 PM EST | Sunday, February 25, 2024 | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a></small> ]
