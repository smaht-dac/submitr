====
StaticSection
====

Description of properties for the SMaHT Portal schema for **StaticSection**.
Parent schema is `UserContent <UserContent.html>`_.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td colSpan="3"> At least <u>one</u> of: <b>consortia</b>, <b>submission_centers</b></td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    Properties in <span style='color:red'>red</span> are <i>required</i> properties.
    Properties in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties. <p />
    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>aliases</span></b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>body</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain html or text content of this section. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>consortia</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Consortia associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>content</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Content for the page. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>content_as_html</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Convert RST, HTML and MD content into HTML. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>description</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Plain text description of the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>file</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Source file to use for populating content. Is superceded by contents of 'body', if one present. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>filetype</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Type of file used for content. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:red'>identifier</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Unique, identifying name for the item.<br /><b>pattern</b>: <small style='font-family:monospace;'>^([A-Za-z0-9-_]+[.])*[A-Za-z0-9-_]+$</small> </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>options</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Options for section display. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>section_type</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;Page Section&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;Announcement<br />&nbsp;•&nbsp;Search Info Header<br />&nbsp;•&nbsp;Item Page Header<br />&nbsp;•&nbsp;Home Page Slide</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> What this section is used for. Defaults to 'Page Section'. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>submission_centers</b> </td> <td width="15%" style="white-space:nowrap;"> <u><b>array</b> of <b>string</b></u><br />•&nbsp;unique </td> <td width="80%"> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> Title for the item. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> </table>
    <p />
