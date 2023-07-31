import contextlib
import os

from dcicutils.common import OrchestratedApp, APP_CGAP, APP_FOURFRONT, APP_SMAHT, ORCHESTRATED_APPS
from dcicutils.creds_utils import KeyManager, CGAPKeyManager, FourfrontKeyManager, SMaHTKeyManager
from dcicutils.exceptions import InvalidParameterError


# TODO: Integrate this better with dcicutils.env_utils

LOCAL_SERVER = "http://localhost:8000"
LOCAL_PSEUDOENV = 'fourfront-cgaplocal'

PRODUCTION_SERVER = 'https://cgap.hms.harvard.edu'
PRODUCTION_ENV = 'fourfront-cgap'

DEFAULT_ENV_VAR = 'SUBMITCGAP_ENV'
DEFAULT_APP_VAR = 'SUBMITCGAP_APP'

DEFAULT_DEFAULT_ENV = PRODUCTION_ENV
DEFAULT_DEFAULT_APP = APP_CGAP


def _compute_default_env():  # factored out as a function for testing
    return os.environ.get(DEFAULT_ENV_VAR, DEFAULT_DEFAULT_ENV)


def _compute_default_app():  # factored out as a function for testing
    return os.environ.get(DEFAULT_APP_VAR, DEFAULT_DEFAULT_APP)


DEFAULT_ENV = _compute_default_env()
DEFAULT_APP = _compute_default_app()


class GenericKeyManager:

    # TODO: This might want to move to dcicutils at some point, but it'd need more trampoline methods
    #       -kmp 24-Feb-2023

    def __init__(self):
        self._cgap_key_manager: KeyManager = CGAPKeyManager()
        self._fourfront_key_manager: KeyManager = FourfrontKeyManager()
        self._smaht_key_manager: KeyManager = SMaHTKeyManager()
        self._key_manager: KeyManager = self._cgap_key_manager
        self._selected_app = DEFAULT_APP

    def select_app(self, app: OrchestratedApp):
        if app == APP_CGAP:
            self._key_manager = self._cgap_key_manager
        elif app == APP_FOURFRONT:
            self._key_manager = self._fourfront_key_manager
        elif app == APP_SMAHT:
            self._key_manager = self._smaht_key_manager
        else:
            raise InvalidParameterError(parameter='app', value=app, options=ORCHESTRATED_APPS)
        self._selected_app = app

    @property
    def selected_app(self):
        return self._selected_app

    @contextlib.contextmanager
    def locally_selected_app(self, app: OrchestratedApp):
        old_app = self.selected_app
        try:
            self.select_app(app)
            yield
        finally:
            self.select_app(old_app)

    def get_keydict_for_env(self, env):
        return self._key_manager.get_keydict_for_env(env)

    def get_keydict_for_server(self, server):
        return self._key_manager.get_keydict_for_server(server)

    def keydict_to_keypair(self, auth_dict):
        return self._key_manager.keydict_to_keypair(auth_dict)

    @property
    def keys_file(self):
        return self._key_manager.keys_file


KEY_MANAGER = GenericKeyManager()
