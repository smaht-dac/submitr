====
TrackingItem
====

Description of properties for the SMaHT Portal schema for **TrackingItem**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>tracking_type</b> </td> <td> string </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Name </td> <th> Type </td> <th> Attributes </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>status</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> <tr> <td width="5%"> <b>tracking_type</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> What this item tracks. Defaults to other. </td> </tr> <tr> <td width="5%"> <b>download_tracking</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> Subobject to hold download tracking field. Allows additional properties. </td> </tr> <tr> <td width="5%"> <b>google_analytics</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> A high-level container object containing data from Google Analytics as well as metadata about the report. </td> </tr> <tr> <td width="5%"> <b>jupyterhub_session</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> Subobject to track a JupyterHub session. Allows additional properties. </td> </tr> <tr> <td width="5%"> <b>other_tracking</b> </td> <td> object </td> <td> property-attributes-todo </td> <td> Subobject to misc. tracking fields. Allows additional properties. </td> </tr> <tr> <td width="5%"> <b>display_title</b> </td> <td> string </td> <td> property-attributes-todo </td> <td> - </td> </tr> </table>
