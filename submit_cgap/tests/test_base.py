import contextlib
import re

from dcicutils.common import APP_CGAP, APP_FOURFRONT
from dcicutils.creds_utils import CGAPKeyManager, FourfrontKeyManager, KeyManager
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

    manager = base_module.GenericKeyManager()
    assert isinstance(manager, base_module.GenericKeyManager)
    assert manager.selected_app == APP_CGAP
    assert isinstance(manager._key_manager, CGAPKeyManager)  # noQA - protected member access

    manager.select_app(APP_FOURFRONT)
    assert manager.selected_app == APP_FOURFRONT
    assert isinstance(manager._key_manager, FourfrontKeyManager)  # noQA - protected member access

    with manager.locally_selected_app(APP_CGAP):
        assert manager.selected_app == APP_CGAP
        assert isinstance(manager._key_manager, CGAPKeyManager)  # noQA - protected member access

    assert manager.selected_app == APP_FOURFRONT
    assert isinstance(manager._key_manager, FourfrontKeyManager)  # noQA - protected member access

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
