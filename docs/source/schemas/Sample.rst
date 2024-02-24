====
Sample
====

Description of properties for the SMaHT Portal schema for **Sample**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table">
        <tr>
            <th> Name </td>
            <th> Type </td>
        </tr>
        <tr> <td> submission_centers </td> <td> array or string </td> </tr> <tr> <td> submitted_id </td> <td> string </td> </tr>
    </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table">
        <tr>
            <th> Name </td>
            <th> Type </td>
        </tr>
        <tr> <td> accession </td> <td> string </td> </tr> <tr> <td> submitted_id </td> <td> string </td> </tr> <tr> <td> uuid </td> <td> string </td> </tr>
    </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    <table class="schema-table">
        <tr>
            <th> Name </td>
            <th> Type </td>
            <th> Attributes </td>
            <th> Description </td>
        </tr>
        <tr>
            <td> <b>{property_name}</b> </td>
            <td> {property_type} </td>
            <td> {property_attributes} </td>
            <td> {property_description} </td>
        </tr>
        <tr>
            <td> <b>submission_centers</b> </td>
            <td> array&nbsp;of&nbsp;string </td>
            <td> required </td>
            <td> foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
            <td> ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
        </tr>
        <tr>
            <td> consortia </td>
            <td> <u>enum</u> <br />abc<br />defghi<br />jk<br />lmnopqrst</td>
            <td> required </td>
            <td> foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
            <td> ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
        </tr>
        <tr>
            <td> <b>identifier</b> </td>
            <td> <u>string</u> </td>
            <td class="schema-table nowrap">
                <ul>
                    <li> unique </li>
                    <li> required </li>
                    <li> pattern:<br />^[A-Za-z0-9-_]+^[A-Za-z0-9-_]+$ </li>
                </ul>
            </td>
            <td> pattern </td>
            <td> ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
        </tr>
    </table>
