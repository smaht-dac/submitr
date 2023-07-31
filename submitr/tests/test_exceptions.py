from ..exceptions import CGAPPermissionError


def test_cgap_permission_error():

    server = "http://localhost:8888"  # Not an address we use, but that shouldn't matter.
    error = CGAPPermissionError(server)

    assert isinstance(error, PermissionError)
    assert isinstance(error, CGAPPermissionError)

    assert error.server == server

    assert str(error) == ("Your credentials were rejected by http://localhost:8888."
                          " Either this is not the right server, or you need to obtain up-to-date access keys.")
