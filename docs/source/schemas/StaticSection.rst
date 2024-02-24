====
StaticSection
====

Description of properties for the SMaHT Portal schema for **StaticSection**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array of string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array of string </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>options</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> Options for section display. </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Title for the item. </td> </tr> <tr> <td width="5%"> <b>identifier</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Unique, identifying name for the item. </td> </tr> <tr> <td width="5%"> <b>description</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Plain text description of the item. </td> </tr> <tr> <td width="5%"> <b>submission_centers</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Submission Centers associated with this item. </td> </tr> <tr> <td width="5%"> <b>consortia</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Consortia associated with this item. </td> </tr> <tr> <td width="5%"> <b>aliases</b> </td> <td> array </td> <td> property-attributes-todo </td> <td> Institution-specific ID (e.g. bgm:cohort-1234-a). </td> </tr> <tr> <td width="5%"> <b>body</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Plain html or text content of this section. </td> </tr> <tr> <td width="5%"> <b>file</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Source file to use for populating content. Is superceded by contents of 'body', if one present. </td> </tr> <tr> <td width="5%"> <b>section_type</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> What this section is used for. Defaults to 'Page Section'. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>content_as_html</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Convert RST, HTML and MD content into HTML. </td> </tr> <tr> <td width="5%"> <b>content</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Content for the page. </td> </tr> <tr> <td width="5%"> <b>filetype</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> Type of file used for content. </td> </tr> </table>
