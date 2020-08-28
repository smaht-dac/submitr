import io
import json

from dcicutils.qa_utils import override_environ, MockFileSystem
from unittest import mock
from ..auth import (
    CGAPPermissionError, auth_tuple_to_cgap_auth_dict, cgap_auth_to_tuple,
    get_cgap_auth_dict, get_cgap_auth_tuple, get_cgap_keypair, get_cgap_keypairs,
    ACCESS_KEY_FILENAME, KEY_ID_VAR, SECRET_VAR, DEFAULT_ENV_VAR, KEYPAIRS_FILENAME,
)


def test_cgap_permission_error():

    server = "http://localhost:8888"  # Not an address we use, but that shouldn't matter.
    error = CGAPPermissionError(server)

    assert isinstance(error, PermissionError)
    assert isinstance(error, CGAPPermissionError)

    assert error.server == server

    assert str(error) == ("Your credentials (the access key information in environment variables"
                          " SUBMIT_CGAP_ACCESS_KEY_ID and SUBMIT_CGAP_SECRET_ACCESS_KEY) were rejected"
                          " by http://localhost:8888. Either this is not the right server,"
                          " or you need to obtain up-to-date access keys.")


def test_auth_env_variables():

    # A minimal test that all our variables fit the naming scheme SUBMIT_CGAP_xxx.
    vars = {'KEY_ID_VAR': KEY_ID_VAR, 'SECRET_VAR': SECRET_VAR, 'DEFAULT_ENV_VAR': DEFAULT_ENV_VAR}
    for name, val in vars.items():
        assert val.startswith("SUBMIT_CGAP_"), "The variable %s has an unexpected value: %s" % (name, val)


def test_auth_filenames():

    # A minimal test that we picked a name that is a hidden file with a CGAP-related name.
    filenames = {'ACCESS_KEY_FILENAME': ACCESS_KEY_FILENAME, 'KEYPAIRS_FILENAME': KEYPAIRS_FILENAME}
    for name, val in filenames.items():
        assert val.startswith(".cgap"), "The variable %s has unexpected value: %s" % (name, val)


def test_cgap_auth_tuple():
    key = "abc123"
    secret = "abracadabra"

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=key, SUBMIT_CGAP_SECRET_ACCESS_KEY=secret):
        assert get_cgap_auth_tuple() == (key, secret)

    def assure_missing_env_variable_error():
        try:
            get_cgap_auth_tuple()
        except Exception as e:
            assert str(e) == ("Both of the environment variables SUBMIT_CGAP_ACCESS_KEY_ID and"
                              " SUBMIT_CGAP_SECRET_ACCESS_KEY must be set. Appropriate values"
                              " can be obtained by creating an access key in your CGAP user profile.")
        else:
            raise AssertionError("Expected error was not raised.")

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=key, SUBMIT_CGAP_SECRET_ACCESS_KEY=None):
        assure_missing_env_variable_error()

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=None, SUBMIT_CGAP_SECRET_ACCESS_KEY=secret):
        assure_missing_env_variable_error()

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=None, SUBMIT_CGAP_SECRET_ACCESS_KEY=None):
        assure_missing_env_variable_error()


def test_cgap_auth_dict():
    key = "abc123"
    secret = "abracadabra"
    server = "http://localhost:8888"

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=key, SUBMIT_CGAP_SECRET_ACCESS_KEY=secret):
        assert get_cgap_auth_dict(server) == {'key': key, 'secret': secret, 'server': server}

    def assure_missing_env_variable_error():
        try:
            get_cgap_auth_dict(server)
        except Exception as e:
            assert str(e) == ("Both of the environment variables SUBMIT_CGAP_ACCESS_KEY_ID and"
                              " SUBMIT_CGAP_SECRET_ACCESS_KEY must be set. Appropriate values"
                              " can be obtained by creating an access key in your CGAP user profile.")
        else:
            raise AssertionError("Expected error was not raised.")

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=key, SUBMIT_CGAP_SECRET_ACCESS_KEY=None):
        assure_missing_env_variable_error()

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=None, SUBMIT_CGAP_SECRET_ACCESS_KEY=secret):
        assure_missing_env_variable_error()

    with override_environ(SUBMIT_CGAP_ACCESS_KEY_ID=None, SUBMIT_CGAP_SECRET_ACCESS_KEY=None):
        assure_missing_env_variable_error()


def test_cgap_auth_to_tuple():

    assert cgap_auth_to_tuple({'key': 'foo', 'secret': 'bar', 'server': 'baz'}) == ('foo', 'bar')


def test_auth_tuple_to_cgap_auth_dict():

    assert auth_tuple_to_cgap_auth_dict(('foo', 'bar'), server='baz') == {
        'key': 'foo',
        'secret': 'bar',
        'server': 'baz',
    }


def test_get_cgap_keypair_and_keypairs():

    expected_content = {'fourfront-cgapfoo': ['key123', 'secret123'], 'fourfront-cgaplocal': ['key456', 'secret456']}

    mfs = MockFileSystem(files={
        ".cgap-keypairs.json":
            json.dumps(expected_content)
    })

    with mock.patch("io.open", mfs.open):

        assert get_cgap_keypairs() == expected_content
        assert get_cgap_keypair('fourfront-cgapfoo') == ('key123', 'secret123')
        assert get_cgap_keypair('fourfront-cgaplocal') == ('key456', 'secret456')
        assert get_cgap_keypair(None) == ('key456', 'secret456')
        assert get_cgap_keypair() == ('key456', 'secret456')
