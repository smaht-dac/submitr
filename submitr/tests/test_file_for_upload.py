import os
import pytest
import tempfile
from dcicutils.file_utils import create_random_file, compute_file_md5, get_file_size, normalize_path
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import (
    is_temporary_directory, remove_temporary_directory, temporary_directory, temporary_file)
from submitr.file_for_upload import FilesForUpload
from submitr.rclone import AmazonCredentials, GoogleCredentials, RCloneConfigAmazon, RCloneConfigGoogle

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
        if isinstance(self, (RCloneConfigAmazon, RCloneConfigGoogle)):
            return os.path.join(self._tmpdir, path) if (path := super().path(path)) else None
        return os.path.join(self._tmpdir, path) if (path := normalize_path(path)) else None
    def _root(self):  # noqa
        return self._tmpdir
    def _create_files_for_testing(self, *args):  # noqa
        for arg in args:
            if isinstance(arg, str):
                self._create_file_for_testing(arg)
            elif isinstance(arg, (list, tuple)):
                for file in arg:
                    if isinstance(file, str):
                        self._create_files_for_testing(file)
    def _create_file_for_testing(self, file):  # noqa
        if (file := normalize_path(file)) and (not file.startswith(os.path.sep) or (file := file[1:])):
            if file := self._realpath(file):
                if file_directory := os.path.dirname(file):
                    os.makedirs(file_directory, exist_ok=True)
                create_random_file(file, nbytes=RANDOM_TMPFILE_SIZE)
    def _clear_files(self):  # noqa
        assert is_temporary_directory(self._tmpdir)
        remove_temporary_directory(self._tmpdir)
        os.makedirs(self._tmpdir, exist_ok=True)
        assert is_temporary_directory(self._tmpdir)


class Mock_RCloneConfigAmazon(Mock_CloudStorage, RCloneConfigAmazon):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="amazon")
        super(RCloneConfigAmazon, self).__init__(*args, **kwargs)


class Mock_RCloneConfigGoogle(Mock_CloudStorage, RCloneConfigGoogle):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="google")
        super(RCloneConfigGoogle, self).__init__(*args, **kwargs)


class Mock_LocalStorage(Mock_CloudStorage):

    # Might as well use it also for easy local file system test file setup for convenience.
    def __init__(self, *args, **kwargs):
        super().__init__(subdir="local")


def test_file_for_upload_a():

    with temporary_directory() as tmpdir:
        upload_file_a = os.path.join(tmpdir, "some_file_a.fastq")
        upload_file_b = os.path.join(tmpdir, "some_file_b.fastq")
        upload_file_a_uuid = create_uuid()
        upload_file_b_uuid = create_uuid()
        files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                 {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
        ffu = FilesForUpload.assemble(files,
                                      main_search_directory=tmpdir,
                                      main_search_directory_recursively=True)
        assert ffu[0].found is False
        assert ffu[1].found is False

    with temporary_directory() as tmpdir:
        upload_file_a_size = 1024
        upload_file_a_dup_size = 1024
        upload_file_b_size = 2048
        dir_a = tmpdir
        os.makedirs(dir_b := os.path.join(tmpdir, "some_subdir"))
        upload_file_a = create_random_file(os.path.join(dir_a, "some_file_a.fastq"), nbytes=upload_file_a_size)
        upload_file_b = create_random_file(os.path.join(dir_a, "some_file_b.fastq"), nbytes=upload_file_b_size)
        upload_file_a_dup = create_random_file(os.path.join(dir_b, "some_file_a.fastq"), nbytes=upload_file_a_dup_size)
        upload_file_a_uuid = create_uuid()
        upload_file_b_uuid = create_uuid()
        assert os.path.isfile(upload_file_a)
        assert os.path.isfile(upload_file_b)
        files = [{"filename": upload_file_a, "uuid": upload_file_a_uuid},
                 {"filename": upload_file_b, "uuid": upload_file_b_uuid}]
        ffu = FilesForUpload.assemble(files,
                                      main_search_directory=tmpdir,
                                      main_search_directory_recursively=True)
        assert ffu[0].found is True
        assert ffu[0].path == upload_file_a
        assert ffu[0].size == upload_file_a_size
        assert ffu[0].found_local is True
        assert ffu[0].found_local_multiple is True
        assert ffu[0].path_local == upload_file_a
        assert ffu[0].path_local_multiple == [upload_file_a, upload_file_a_dup]
        assert ffu[0].size_local == upload_file_a_size
        assert ffu[0].found_google is False
        assert ffu[0].path_google is None
        assert ffu[0].ignore is False
        assert ffu[0].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_a_uuid}"

        assert ffu[1].found is True
        assert ffu[1].path == upload_file_b
        assert ffu[1].size == upload_file_b_size
        assert ffu[1].found_local is True
        assert ffu[1].found_local_multiple is False
        assert ffu[1].path_local == upload_file_b
        assert ffu[1].path_local_multiple is None
        assert ffu[1].size_local == upload_file_b_size
        assert ffu[1].found_google is False
        assert ffu[1].path_google is None
        assert ffu[1].ignore is False
        assert ffu[1].resume_upload_command(env="some_env") == f"resume-uploads --env some_env {upload_file_b_uuid}"


def test_file_for_upload_b():

    filesystem = Mock_LocalStorage()
    filesystem._create_files_for_testing(file_a := "some_file_for_upload_one.fastq",
                                         file_b := "abc/some_file_for_upload_two.bam")
    files = [{"filename": file_a, "uuid": create_uuid()},
             {"filename": file_b, "uuid": create_uuid()}]

    ffu = FilesForUpload.assemble(files,
                                  main_search_directory=filesystem._root(),
                                  main_search_directory_recursively=True)
    for ffui, ff in enumerate(ffu):
        assert ff.name == os.path.basename(files[ffui]["filename"])
        assert ff.found is True
        assert ff.path == os.path.join(filesystem._root(), files[ffui]["filename"])
        assert ff.display_path == os.path.join(filesystem._root(), files[ffui]["filename"])
        assert ff.uuid == files[ffui]["uuid"]
        assert ff.size == RANDOM_TMPFILE_SIZE
        assert ff.checksum == compute_file_md5(ff.path)
        assert ff.found_local is True
        assert ff.found_local_multiple is False
        assert ff.from_local is True
        assert ff.favor_local is True
        assert ff.ignore is False
        assert ff.path_local == os.path.join(filesystem._root(), files[ffui]["filename"])
        assert ff.path_local_multiple is None
        assert ff.size_local == RANDOM_TMPFILE_SIZE
        assert ff.checksum_local == compute_file_md5(ff.path)
        assert ff.found_google is False
        assert ff.from_google is False
        assert ff.path_google is None
        assert ff.display_path_google is None
        assert ff.size_google is None
        assert ff.checksum_google is None

    ffunr = FilesForUpload.assemble(files,
                                    main_search_directory=filesystem._root(),
                                    main_search_directory_recursively=False)
    assert ffunr[0].found is True
    assert ffunr[1].found is False


def test_file_for_upload_c():
    pass


@pytest.mark.parametrize("cloud_storage_args", [(Mock_RCloneConfigAmazon, AmazonCredentials),
                                                (Mock_RCloneConfigGoogle, GoogleCredentials)])
def test_mock_cloud_storage(cloud_storage_args):
    cloud_storage_class = cloud_storage_args[0]
    credentials_class = cloud_storage_args[1]
    def internal_test(bucket):  # noqa
        nonlocal cloud_storage_class, credentials_class
        amazon = cloud_storage_class(credentials_class(), bucket=bucket)
        amazon._create_files_for_testing(["abc.fastq", "def/ghi.json"])
        assert amazon.path("some-file") == f"{bucket}/some-file" if bucket else "some-file"
        assert amazon.path_exists("abc.fastq") is True
        assert amazon.file_size("abc.fastq") == RANDOM_TMPFILE_SIZE
        assert amazon.file_checksum("abc.fastq") == compute_file_md5(amazon._realpath("abc.fastq"))
        assert amazon.path_exists("def/ghi.json") is True
        assert amazon.file_size("def/ghi.json") == RANDOM_TMPFILE_SIZE
        assert amazon.file_checksum("def/ghi.json") == compute_file_md5(amazon._realpath("def/ghi.json"))
        assert amazon.path_exists("does-not-exists.json") is False
        amazon._clear_files()
        assert amazon.path_exists("abc.fastq") is False
        assert amazon.path_exists("def/ghi.json") is False
        amazon._create_file_for_testing("xyzzy/foobar/does-exist.json")
        assert amazon.path_exists("xyzzy/foobar/does-exist.json") is True
    internal_test(bucket="some-bucket")
    internal_test(bucket=None)


def test_amazon_credentials_object():
    region = "some-region"
    access_key_id = "some-access-key-id"
    secret_access_key = "some-secret-access-key"
    session_token = "some-session-token"
    kms_key_id = "some-kms-key-id"
    credentials = AmazonCredentials(
        region=region,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        kms_key_id=kms_key_id)
    assert credentials.region == region
    assert credentials.access_key_id == access_key_id
    assert credentials.secret_access_key == secret_access_key
    assert credentials.session_token == session_token
    assert credentials.kms_key_id == kms_key_id


def test_google_credentials_object():
    location = "some-location"
    service_account_file = "some-service-account-file-does-not-exist.json"
    with pytest.raises(Exception):
        # No service account file found.
        GoogleCredentials(service_account_file=service_account_file, location=location)
    with temporary_file(suffix=".json") as service_account_file:
        credentials = GoogleCredentials(service_account_file=service_account_file, location=location)
        assert credentials.location == location
        assert credentials.service_account_file == service_account_file
