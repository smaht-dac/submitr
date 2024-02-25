====
UserContent
====

.. raw:: html

    Description of properties for the SMaHT Portal schema for <b>UserContent</b>.
    
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties.
    In the <i>Properties</i> section, properties in <span style='color:red'>red</span> are <i>required</i> properties,
    and those in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>
|


Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>
|




Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>content_as_html</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Convert RST, HTML and MD content into HTML. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique, identifying name for the item.<br /><b>pattern</b>: <small style='font-family:monospace;'>^[A-Za-z0-9-_]+$</small> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>options</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Options for section display. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>options</span> <b>.</b> collapsible</b> </td> <td width="15%" style="white-space:nowrap;"> <b>boolean</b> </td> <td width="80%"> Whether this StaticSection should be collapsible (wherever collapsibility is an option). This property is ignored in some places, e.g. lists where all sections are explicitly collapsible. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>options</span> <b>.</b> default_open</b> </td> <td width="15%" style="white-space:nowrap;"> <b>boolean</b> </td> <td width="80%"> Whether this StaticSection should appear as expanded by default (in places where it may be collapsible). Does not necessarily depend on 'collapsible' being true, e.g. in lists where all sections are explicitly collapsible. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>options</span> <b>.</b> image</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Image or screenshot URL for this Item to use as a preview. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;padding-left:20pt"> <b><span style='font-weight:normal;'>options</span> <b>.</b> title_icon</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Icon to be showed next to title in selected places. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;shared<br />&nbsp;•&nbsp;current&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;inactive<br />&nbsp;•&nbsp;in review<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> </table>
    <p />
