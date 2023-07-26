import contextlib
import pytest
import re

from dcicutils.common import APP_CGAP, APP_FOURFRONT, APP_SMAHT
from dcicutils.creds_utils import CGAPKeyManager, FourfrontKeyManager, SMaHTKeyManager, KeyManager
from dcicutils.misc_utils import override_environ
from unittest import mock
from .. import base as base_module


# The SUBMITCGAP_ENV environment variable is used at application startup to compute a value of DEFAULT_ENV
# so to test effect of binding it, we have to both bind the environment variable and re-run the setup of
# that variable in two steps...
@contextlib.contextmanager
def default_env_for_testing(default_env):
    with override_environ(**{base_module.DEFAULT_ENV_VAR: default_env}):  # step 1 of 2
        with mock.patch.object(base_module, "DEFAULT_ENV",  # step 2 of 2
                               base_module._compute_default_env()):  # noqa - need private function for testing
            yield


def test_defaults():

    assert 'amazon' not in base_module.PRODUCTION_SERVER  # e.g., https://cgap-mgb.hms.harvar.edu (not an amazon URL)

    assert re.match("https?://(localhost|127[.]0[.]0[.][0-9]+:[0-9][0-9][0-9][0-9])",  # e.g., http://localhost:8000
                    base_module.LOCAL_SERVER)
    assert 'local' in base_module.LOCAL_PSEUDOENV  # e.g., 'fourfront-cgaplocal'

    assert base_module.DEFAULT_ENV == base_module.PRODUCTION_ENV
    with default_env_for_testing(base_module.LOCAL_PSEUDOENV):
        assert base_module.DEFAULT_ENV == base_module.LOCAL_PSEUDOENV


def test_generic_key_manager():

    def key_manager(generic_key_manager):
        return generic_key_manager._key_manager  # noQA - protected member access

    manager = base_module.GenericKeyManager()
    assert isinstance(manager, base_module.GenericKeyManager)
    assert manager.selected_app == APP_CGAP
    assert isinstance(key_manager(manager), CGAPKeyManager)
    assert isinstance(key_manager(manager), KeyManager)

    manager.select_app(APP_FOURFRONT)
    assert manager.selected_app == APP_FOURFRONT
    assert isinstance(key_manager(manager), FourfrontKeyManager)
    assert isinstance(key_manager(manager), KeyManager)

    invalid_app = APP_CGAP + APP_FOURFRONT

    with pytest.raises(ValueError):
        manager.select_app(invalid_app)

    with manager.locally_selected_app(APP_CGAP):
        assert manager.selected_app == APP_CGAP
        assert isinstance(key_manager(manager), CGAPKeyManager)

        with manager.locally_selected_app(APP_SMAHT):
            assert manager.selected_app == APP_SMAHT
            assert isinstance(key_manager(manager), SMaHTKeyManager)

        assert manager.selected_app == APP_CGAP
        assert isinstance(key_manager(manager), CGAPKeyManager)

    assert manager.selected_app == APP_FOURFRONT
    assert isinstance(key_manager(manager), FourfrontKeyManager)

    mocked_envname = 'some-env'
    mocked_server = 'some-server'
    mocked_keydict = {'key': 'mykey', 'secret': 'mysecret', 'server': mocked_server}

    with mock.patch.object(FourfrontKeyManager, "get_keydict_for_env") as mock_get_keydict_for_env:
        def mocked_get_keydict_for_env(env):
            assert env == mocked_envname
            return mocked_keydict
        mock_get_keydict_for_env.side_effect = mocked_get_keydict_for_env
        res = manager.get_keydict_for_env(mocked_envname)
        assert res == mocked_keydict

    with mock.patch.object(FourfrontKeyManager, "get_keydict_for_server") as mock_get_keydict_for_server:
        def mocked_get_keydict_for_server(server):
            assert server == mocked_server
            return mocked_keydict
        mock_get_keydict_for_server.side_effect = mocked_get_keydict_for_server
        res = manager.get_keydict_for_server(mocked_server)
        assert res == mocked_keydict

    assert manager.keys_file == key_manager(manager).keys_file
