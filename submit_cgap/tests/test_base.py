import contextlib
import os

from dcicutils.qa_utils import override_environ
from unittest import mock
from .. import base as base_module
from ..base import KeyManager


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

    assert base_module.PRODUCTION_SERVER == "https://cgap.hms.harvard.edu"

    assert base_module.LOCAL_SERVER == "http://localhost:8000"
    assert base_module.LOCAL_PSEUDOENV == 'fourfront-cgaplocal'

    assert base_module.DEFAULT_ENV == base_module.PRODUCTION_ENV
    with default_env_for_testing(base_module.LOCAL_PSEUDOENV):
        assert base_module.DEFAULT_ENV == base_module.LOCAL_PSEUDOENV


def test_keymanager():

    original_file = KeyManager.keydicts_filename()

    assert isinstance(original_file, str)

    with KeyManager.alternate_keydicts_filename(None):
        assert KeyManager.keydicts_filename() == original_file

    assert KeyManager.keydicts_filename() == original_file

    with override_environ(CGAP_KEYS_FILE=None):
        assert os.environ.get('CGAP_KEYS_FILE') is None
        with KeyManager.alternate_keydicts_filename_from_environ():
            assert KeyManager.keydicts_filename() == original_file
        assert KeyManager.keydicts_filename() == original_file

    assert KeyManager.keydicts_filename() == original_file

    with override_environ(CGAP_KEYS_FILE=""):
        assert os.environ.get('CGAP_KEYS_FILE') == ""
        with KeyManager.alternate_keydicts_filename_from_environ():
            assert KeyManager.keydicts_filename() == original_file

    assert KeyManager.keydicts_filename() == original_file

    alternate_file = 'some-other-file'

    with KeyManager.alternate_keydicts_filename(alternate_file):
        assert KeyManager.keydicts_filename() == alternate_file

    assert KeyManager.keydicts_filename() == original_file

    with override_environ(CGAP_KEYS_FILE=alternate_file):
        assert os.environ.get('CGAP_KEYS_FILE') == alternate_file
        with KeyManager.alternate_keydicts_filename_from_environ():
            assert KeyManager.keydicts_filename() == alternate_file
        assert KeyManager.keydicts_filename() == original_file

    assert KeyManager.keydicts_filename() == original_file
