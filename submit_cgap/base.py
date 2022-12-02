import os

from dcicutils.creds_utils import CGAPKeyManager


# TODO: Integrate this better with dcicutils.env_utils

LOCAL_SERVER = "http://localhost:8000"
LOCAL_PSEUDOENV = 'fourfront-cgaplocal'

PRODUCTION_SERVER = 'https://cgap.hms.harvard.edu'
PRODUCTION_ENV = 'fourfront-cgap'

DEFAULT_ENV_VAR = 'SUBMITCGAP_ENV'


def _compute_default_env():
    return os.environ.get(DEFAULT_ENV_VAR, PRODUCTION_ENV)


DEFAULT_ENV = _compute_default_env()


KEY_MANAGER = CGAPKeyManager()
