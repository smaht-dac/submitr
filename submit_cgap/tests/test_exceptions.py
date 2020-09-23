from ..base import KeyManager
from ..exceptions import CGAPPermissionError, CGAPKeyMissing, CGAPEnvKeyMissing, CGAPServerKeyMissing


def test_cgap_permission_error():

    server = "http://localhost:8888"  # Not an address we use, but that shouldn't matter.
    error = CGAPPermissionError(server)

    assert isinstance(error, PermissionError)
    assert isinstance(error, CGAPPermissionError)

    assert error.server == server

    assert str(error) == ("Your credentials were rejected by http://localhost:8888."
                          " Either this is not the right server, or you need to obtain up-to-date access keys.")


def test_cgap_key_missing():

    error = CGAPKeyMissing(context="testing")

    assert isinstance(error, RuntimeError)
    assert isinstance(error, CGAPKeyMissing)

    assert str(error) == "Missing credential in file %s for testing." % KeyManager.keydicts_filename()


def test_cgap_env_key_missing():
    some_env = 'fourfront-cgapsomething'

    error = CGAPEnvKeyMissing(env=some_env)

    assert isinstance(error, RuntimeError)
    assert isinstance(error, CGAPKeyMissing)

    assert str(error) == ("Missing credential in file %s for beanstalk environment %s."
                          % (KeyManager.keydicts_filename(), some_env))


def test_cgap_server_key_missing():

    some_server = "http://127.0.0.1:5000"

    error = CGAPServerKeyMissing(server=some_server)

    assert isinstance(error, RuntimeError)
    assert isinstance(error, CGAPKeyMissing)

    assert str(error) == ("Missing credential in file %s for server %s."
                          % (KeyManager.keydicts_filename(), some_server))
