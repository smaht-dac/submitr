import json
import os
import tempfile
from dcicutils.file_utils import create_random_file, compute_file_md5, get_file_size, normalize_path
from dcicutils.structured_data import Portal
from dcicutils.tmpfile_utils import (
    is_temporary_directory, remove_temporary_directory)
from submitr.rclone import RCloneConfig, RCloneAmazon, RCloneGoogle

TMPDIR = None
RANDOM_TMPFILE_SIZE = 2048


def setup_module():
    global TMPDIR
    TMPDIR = tempfile.mkdtemp()


def teardown_module():
    global TMPDIR
    remove_temporary_directory(TMPDIR)


class Mock_CloudStorage:
    # We simply use the file system, within a temporary directory, via global
    # TMPDIR (above), to simulate/mock AWS S3 and Google Cloud Storage (GCS).
    def __init__(self, subdir):  # noqa
        global TMPDIR
        assert isinstance(TMPDIR, str) and TMPDIR and is_temporary_directory(TMPDIR)
        assert isinstance(subdir, str) and subdir
        self._tmpdir = os.path.join(TMPDIR, subdir)
        os.makedirs(self._tmpdir, exist_ok=True)
        assert is_temporary_directory(self._tmpdir)
    def path_exists(self, path):  # noqa
        return os.path.isfile(path) if (path := self._realpath(path)) else None
    def file_size(self, file):  # noqa
        return get_file_size(file) if (self.path_exists(file) and (file := self._realpath(file))) else None
    def file_checksum(self, file):  # noqa
        return compute_file_md5(file) if (self.path_exists(file) and (file := self._realpath(file))) else None
    def _realpath(self, path):  # noqa
        if isinstance(self, RCloneConfig):
            return os.path.join(self._tmpdir, path) if (path := super().path(path)) else None
        return os.path.join(self._tmpdir, path) if (path := normalize_path(path)) else None
    def _root(self):  # noqa
        return self._tmpdir
    def _create_files_for_testing(self, *args, **kwargs):  # noqa
        for arg in args:
            if isinstance(arg, str):
                self._create_file_for_testing(arg, nbytes=kwargs.get("nbytes"))
            elif isinstance(arg, (list, tuple)):
                for file in arg:
                    if isinstance(file, str):
                        self._create_files_for_testing(file, nbytes=kwargs.get("nbytes"))
    def _create_file_for_testing(self, file, nbytes=None):  # noqa
        if not isinstance(nbytes, int) or nbytes < 0:
            nbytes = RANDOM_TMPFILE_SIZE
        if (file := normalize_path(file)) and (not file.startswith(os.path.sep) or (file := file[1:])):
            if file := self._realpath(file):
                if file_directory := os.path.dirname(file):
                    os.makedirs(file_directory, exist_ok=True)
                create_random_file(file, nbytes=nbytes)
    def _clear_files(self):  # noqa
        assert is_temporary_directory(self._tmpdir)
        remove_temporary_directory(self._tmpdir)
        os.makedirs(self._tmpdir, exist_ok=True)
        assert is_temporary_directory(self._tmpdir)


class Mock_RCloneAmazon(Mock_CloudStorage, RCloneAmazon):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="amazon")
        super(RCloneAmazon, self).__init__(*args, **kwargs)


class Mock_RCloneGoogle(Mock_CloudStorage, RCloneGoogle):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="google")
        super(RCloneGoogle, self).__init__(*args, **kwargs)


class Mock_LocalStorage(Mock_CloudStorage):
    # Might as well also use Mock_CloudStorage for easy
    # local file system test file setup for convenience.
    def __init__(self, *args, **kwargs):
        super().__init__(subdir="local")
        self.create_files(*args, **kwargs)
    def create_files(self, *args, **kwargs):  # noqa
        super()._create_files_for_testing(*args, **kwargs)
    def create_file(self, *args, **kwargs):  # noqa
        super()._create_file_for_testing(*args, **kwargs)
    @property  # noqa
    def root(self):
        return super()._root()
    def path(self, path):  # noqa
        return os.path.join(self.root, path) if (path := normalize_path(path)) else None


class Mock_Portal(Portal):
    # Designed to handle calls to get_schemas, get_schema, get_schema_type, is_schema_type, is_schema_file_type.
    # which can all be done be simply overriding get_schemas which reads a static/snapshot (2024-05-18) copy
    # of the schemas as returned by the /profiles/ (trailing slash required there btw) endpoint.
    def __init__(self):  # noqa
        dummy_key = {"key": "dummy", "secret": "dummy"}
        super().__init__(dummy_key)
        self._schemas = None
    def get_schemas(self) -> dict:  # noqa
        if not self._schemas:
            self._schemas = load_test_data_json("profiles")
        return self._schemas


def load_test_data_json(file):
    this_directory = os.path.dirname(os.path.abspath(__file__))
    test_data_directory = os.path.join(this_directory, "data")
    test_data_file = os.path.join(test_data_directory, file if file.endswith(".json") else f"{file}.json")
    with open(test_data_file, "r") as f:
        return json.load(f)
