import os
from dcicutils.common import APP_SMAHT


# TODO: Integrate this better with dcicutils.env_utils

LOCAL_SERVER = "http://localhost:8000"
LOCAL_PSEUDOENV = 'smaht-local'

PRODUCTION_SERVER = 'https://data.smaht.org'
PRODUCTION_ENV = 'data'

DEFAULT_ENV_VAR = 'SUBMITR_ENV'
DEFAULT_APP_VAR = 'SUBMITR_APP'

DEFAULT_DEFAULT_ENV = PRODUCTION_ENV
DEFAULT_DEFAULT_APP = APP_SMAHT


def _compute_default_env():  # factored out as a function for testing
    return os.environ.get(DEFAULT_ENV_VAR, DEFAULT_DEFAULT_ENV)


def _compute_default_app():  # factored out as a function for testing
    return os.environ.get(DEFAULT_APP_VAR, DEFAULT_DEFAULT_APP)


DEFAULT_ENV = _compute_default_env()
DEFAULT_APP = _compute_default_app()
