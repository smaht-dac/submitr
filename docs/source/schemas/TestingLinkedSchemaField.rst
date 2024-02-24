====
TestingLinkedSchemaField
====

Description of properties for the SMaHT Portal schema for **TestingLinkedSchemaField**.

Required Properties
~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%">
        <tr>
            <th> Name </td>
            <th> Type </td>
        </tr>
        {required_properties_list}
    </table>

|

Identifying Properties
~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <table class="schema-table" width="100%">
        <tr>
            <th> Name </td>
            <th> Type </td>
        </tr>
        {identifying_properties_list}
    </table>

|

Properties
~~~~~~~~~~

.. raw:: html

    {properties_list}
    <table class="schema-table" width="100%">
        <tr>
            <th> Name </td>
            <th> Type </td>
            <th> Attributes </td>
            <th> Description </td>
        </tr>
        {full_property_row}
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
        </tr>
        <tr>
            <td> consortia </td>
            <td> <u>enum</u> <br />abc<br />defghi<br />jk<br />lmnopqrst</td>
            <td> required </td>
            <td> foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor foo,Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labor </td>
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
        </tr>
    </table>
