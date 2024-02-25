====
TrackingItem
====

Description of properties for the SMaHT Portal schema for **TrackingItem**.


Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>tracking_type</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%"> <b>uuid</b> </td> <td> string </td> <td> <i>See below for more details.</i> </td> </tr> </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    Properties in <span style='color:red'>red</span> are <i>required</i> properties.
    Properties in <span style='color:blue'>blue</span> are <i>identifying</i> properties. <p />
    Properties whose types are in <span style='color:green'>green</span> are <i>reference</i> properties. <p />
    <table class="schema-table" width="104%"> <tr> <th> Property </td> <th> Type </td> <th> Description </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>display_title</b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>download_tracking</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Subobject to hold download tracking field. Allows additional properties. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>google_analytics</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> A high-level container object containing data from Google Analytics as well as metadata about the report. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>jupyterhub_session</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Subobject to track a JupyterHub session. Allows additional properties. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b>other_tracking</b> </td> <td width="15%" style="white-space:nowrap;"> <b>object</b> </td> <td width="80%"> Subobject to misc. tracking fields. Allows additional properties. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u>status</u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;public<br />&nbsp;•&nbsp;draft<br />&nbsp;•&nbsp;released<br />&nbsp;•&nbsp;in review&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;obsolete<br />&nbsp;•&nbsp;deleted</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> - </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><u><span style='color:red'>tracking_type</span></u><span style='font-weight:normal;font-family:arial;color:#222222;'><br />&nbsp;•&nbsp;other&nbsp;←&nbsp;<small><b>default</b></small><br />&nbsp;•&nbsp;download_tracking<br />&nbsp;•&nbsp;google_analytics<br />&nbsp;•&nbsp;jupyterhub_session</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>enum</b> of string </td> <td width="80%"> What this item tracks. Defaults to other. </td> </tr> <tr> <td width="5%" style="white-space:nowrap;"> <b><span style='color:blue'>uuid</span></b> </td> <td width="15%" style="white-space:nowrap;"> <b>string</b> </td> <td width="80%"> - </td> </tr> </table>
    <p />
