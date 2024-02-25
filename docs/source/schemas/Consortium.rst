==========
Consortium
==========



.. raw:: html

    Description of properties for the SMaHT Portal 
    object type <a target="_blank" href="https://data.smaht.org/profiles/Consortium.json?format=json" style="color:black"><b>Consortium</b> 🔗</a>.
    
    
    
    Property names which are <span style='color:red'><b>red</b></span> are <i><b>required</b></i> properties;
    and those in <span style='color:blue'><b>blue</b></span> are <i><b>identifying</b></i> properties.
    Properties whose types are in <span style='color:green'><b>green</b></span> are <i><b>reference</b></i> properties.
    <p />
    

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>identifier</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:red'>title</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>aliases</span></b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>identifier</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b><span style='color:blue'>uuid</span></b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|




Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique<br /> </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>code</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Code used in file naming scheme. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;calculated<br /> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique, identifying name for the item.<br />Must adhere to (regex) <span style='color:red;'><b>pattern</b>:&nbsp;<small style='font-family:monospace;'>^[A-Za-z0-9-_]+$</small></span> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;in review<br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>tags</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;max items: 50<br />•&nbsp;unique<br /> </td> <td width="80%"> Key words that can tag an item - useful for filtering. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>title</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>url</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>string</b></u><br />•&nbsp;format: uri<br /> </td> <td width="80%"> An external resource with additional information about the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique ID by which this object is identified. </td> </tr> </table>
    <p />

.. raw:: html

    <br />[ <small>Generated: Sunday, February 25, 2024 | 2:55 PM EST | <a target="_blank" href="https://data.smaht.org">https://data.smaht.org</a></small> ]
