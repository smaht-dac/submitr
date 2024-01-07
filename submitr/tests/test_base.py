import contextlib
import re

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
