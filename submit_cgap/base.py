import contextlib
import functools
import os

from dcicutils.misc_utils import local_attrs


# TODO: Integrate this better with dcicutils.env_utils

LOCAL_SERVER = "http://localhost:8000"
LOCAL_PSEUDOENV = 'fourfront-cgaplocal'

PRODUCTION_SERVER = 'https://cgap.hms.harvard.edu'
PRODUCTION_ENV = 'fourfront-cgap'

DEFAULT_ENV_VAR = 'SUBMITCGAP_ENV'


def _compute_default_env():
    return os.environ.get(DEFAULT_ENV_VAR, PRODUCTION_ENV)


DEFAULT_ENV = _compute_default_env()


class KeyManager:

    # This is not necessarily the actual keydicts filename. It can e overridden by environment variable CGAP_KEYS_FILE
    DEFAULT_KEYDICTS_FILENAME = os.path.expanduser('~/.cgap-keys.json')

    _KEYDICTS_FILENAME = DEFAULT_KEYDICTS_FILENAME

    @classmethod
    def keydicts_filename(cls):
        return cls._KEYDICTS_FILENAME

    @classmethod
    @contextlib.contextmanager
    def alternate_keydicts_filename(cls, filename):
        if filename is None:
            yield  # If no alternate filename given, change nothing
        else:
            with local_attrs(cls, _KEYDICTS_FILENAME=filename):
                yield

    @classmethod
    @contextlib.contextmanager
    def alternate_keydicts_filename_from_environ(cls):
        filename = os.environ.get('CGAP_KEYS_FILE') or None  # Treats empty string as undefined
        with cls.alternate_keydicts_filename(filename=filename):
            yield


def UsingCGAPKeysFile(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        with KeyManager.alternate_keydicts_filename_from_environ():
            return fn(*args, **kwargs)
    return wrapped
