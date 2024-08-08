from contextlib import contextmanager
from enum import Enum
import os
import pytest
from typing import Optional, Tuple
from unittest.mock import patch as mock_patch
from dcicutils.file_utils import are_files_equal, compute_file_md5 as get_file_checksum, normalize_path
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import temporary_directory, temporary_file, temporary_random_file
from submitr.file_for_upload import FilesForUpload
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.rcloner import RCloner
from submitr.rclone.rclone_store import RCloneStore
from submitr.rclone.rclone_amazon import RCloneAmazon
from submitr.rclone.rclone_google import GoogleCredentials, RCloneGoogle
from submitr.rclone.rclone_utils import cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsS3
from submitr.rclone.testing.rclone_utils_for_testing_google import Gcs
from submitr.s3_upload import upload_file_to_aws_s3
from submitr.s3_utils import get_s3_key_metadata
import submitr.submission_uploads  # noqa
from submitr.submission_uploads import do_any_uploads
from submitr.tests.testing_cloud_helpers import Mock_LocalStorage, Mock_Portal
from submitr.tests.testing_helpers import load_json_test_data
from submitr.tests.integration.testing_rclone_setup import (

    rclone_setup_module,
    rclone_teardown_module,

    amazon_credentials_file_path,
    google_service_account_file_path,

    AMAZON_TEST_BUCKET_NAME,
    AMAZON_REGION,
    AMAZON_KMS_KEY_ID,

    GOOGLE_TEST_BUCKET_NAME,
    GOOGLE_LOCATION,

    TEST_FILE_PREFIX,
    TEST_FILE_SUFFIX,
    TEST_FILE_SIZE
)

# This marks this entire module as "integrtation" tests.
# To run only integration tests:    pytest -m integration
# To run all but integration tests: pytest -m "not integration"
pytestmark = [pytest.mark.integration]


def setup_module():
    rclone_setup_module()


def teardown_module():
    rclone_teardown_module()

# TODO: FYI RCloneAmazon.file_checksum never gets called by tests (though RCloneGoogle.file_checksum does).
# And it appears the rlcone hashsum md5 on a key which has KMS encryption does not work if we specify
# the KMS ID in the rclone config file, but if we leave it out of the config file it does work, hmmm.


class Env:

    test_file_prefix = TEST_FILE_PREFIX
    test_file_suffix = TEST_FILE_SUFFIX
    test_file_size = TEST_FILE_SIZE

    def __init__(self, use_cloud_subfolder_key: bool = False):
        self.use_cloud_subfolder_key = True if (use_cloud_subfolder_key is True) else False
        self.bucket = None

    @staticmethod
    @contextmanager
    def temporary_test_file() -> Tuple[str, str]:
        with temporary_random_file(prefix=Env.test_file_prefix,
                                   suffix=Env.test_file_suffix,
                                   nbytes=Env.test_file_size) as tmp_file_path:
            yield tmp_file_path, os.path.basename(tmp_file_path)

    def file_name_to_key_name(self, file_name: str) -> str:
        # Assumed that the given file name is just that, a file base name, not a path name.
        if not (self.use_cloud_subfolder_key is True):
            return file_name
        else:
            return cloud_path.join(f"{Env.test_file_prefix}{create_uuid()}", file_name)


class EnvAmazon(Env):

    class CredentialsType(Enum):
        TEMPORARY = "temporary"
        TEMPORARY_KEY_SPECIFIC = "temporary-key-specific"

    def __init__(self, use_cloud_subfolder_key: bool = False):
        super().__init__(use_cloud_subfolder_key=use_cloud_subfolder_key)
        self.credentials_file = amazon_credentials_file_path()
        self.bucket = AMAZON_TEST_BUCKET_NAME
        self.region = AMAZON_REGION
        self.kms_key_id = AMAZON_KMS_KEY_ID
        self._main_credentials = None

    @property
    def main_credentials(self) -> AmazonCredentials:
        if not self._main_credentials:
            self._main_credentials = self.credentials()
        return self._main_credentials

    def credentials(self, nokms: bool = False) -> AmazonCredentials:
        credentials = AmazonCredentials.obtain(self.credentials_file,
                                               region=self.region,
                                               kms_key_id=None if nokms is True else self.kms_key_id)
        assert credentials is not None
        assert isinstance(credentials.region, str) and credentials.region
        assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
        assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key
        return credentials

    def temporary_credentials(self,
                              bucket: Optional[str] = None, key: Optional[str] = None,
                              nokms: bool = False) -> AmazonCredentials:
        s3 = self.non_rclone()
        kms_key_id = None if nokms else self.kms_key_id
        temporary_credentials = s3.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=kms_key_id)
        assert isinstance(temporary_credentials.session_token, str) and temporary_credentials.session_token
        assert temporary_credentials.kms_key_id == (None if nokms is True else self.kms_key_id)
        return temporary_credentials

    def non_rclone(self) -> AwsS3:
        return AwsS3(self.main_credentials)


class EnvGoogle(Env):

    def __init__(self, use_cloud_subfolder_key: bool = False):
        super().__init__(use_cloud_subfolder_key=use_cloud_subfolder_key)
        self.service_account_file = google_service_account_file_path()
        self.bucket = GOOGLE_TEST_BUCKET_NAME
        self.location = GOOGLE_LOCATION
        self._main_credentials = None

    @property
    def main_credentials(self) -> AmazonCredentials:
        if not self._main_credentials:
            self._main_credentials = self.credentials()
        return self._main_credentials

    def credentials(self) -> GoogleCredentials:
        credentials = GoogleCredentials.obtain(self.service_account_file, location=self.location)
        assert (credentials is not None) or RCloneGoogle.is_google_compute_engine()
        if credentials is not None:
            assert credentials.location == self.location
            assert credentials.service_account_file == normalize_path(self.service_account_file, expand_home=True)
            assert os.path.isfile(credentials.service_account_file)
        return credentials

    def non_rclone(self):
        return Gcs(self.main_credentials)


def test_all():
    # TODO
    # Split the _test function into separate real test_ functions;
    # originally developed as non-pytest module.
    _test_cloud_variations(use_cloud_subfolder_key=True)
    _test_cloud_variations(use_cloud_subfolder_key=False)
    _test_rclone_local_to_local()


def _test_cloud_variations(use_cloud_subfolder_key: bool = False):

    env_amazon = EnvAmazon(use_cloud_subfolder_key=use_cloud_subfolder_key)
    env_google = EnvGoogle(use_cloud_subfolder_key=use_cloud_subfolder_key)
    _test_utils_for_testing(env_amazon=env_amazon)
    _test_rclone_between_amazon_and_local(env_amazon=env_amazon)
    _test_rclone_between_google_and_local(env_google=env_google)
    _test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google)
    _test_rclone_amazon_to_google(env_amazon=env_amazon, env_google=env_google)


def create_rclone_target_amazon(credentials: AmazonCredentials, bucket: Optional[str] = None) -> RCloneStore:
    target_amazon = RCloneAmazon(credentials, bucket=bucket)
    assert target_amazon.credentials == credentials
    assert target_amazon.access_key_id == credentials.access_key_id
    assert target_amazon.secret_access_key == credentials.secret_access_key
    assert target_amazon.session_token == credentials.session_token
    assert target_amazon.kms_key_id == credentials.kms_key_id
    assert target_amazon == target_amazon
    assert not (target_amazon != target_amazon)
    assert RCloneAmazon(credentials, bucket="mismatch") != target_amazon  # checking equals override
    # assert RCloneAmazon(target_amazon, bucket="mismatch") != target_amazon  # checking equals override
    return target_amazon


def create_rclone_target_google(credentials: GoogleCredentials, bucket: Optional[str] = None) -> RCloneStore:
    target_google = RCloneGoogle(credentials, bucket=bucket)
    # Google credentials can be None on a GCE instance.
    assert target_google.credentials == credentials
    if credentials:
        # Google credentials can be None on a GCE instance.
        assert target_google.location == credentials.location
        assert target_google.service_account_file == credentials.service_account_file
    assert target_google == target_google
    assert not (target_google != target_google)
    assert RCloneGoogle(credentials, bucket="mismatch") != target_google  # checking equals override
    # assert RCloneGoogle(target_google, bucket="mismatch") != target_google  # checking equals override
    return target_google


def create_rcloner(source: Optional[RCloneStore] = None, destination: Optional[RCloneStore] = None) -> RCloner:
    rcloner = RCloner(source=source, destination=destination)
    assert rcloner.source == source
    assert rcloner.destination == destination
    return rcloner


def sanity_check_amazon_file(env_amazon: EnvAmazon,
                             credentials: AmazonCredentials, bucket: str, key: str, file: str) -> None:
    s3 = env_amazon.non_rclone()
    assert s3.file_exists(bucket, key) is True
    assert s3.file_equals(file, bucket, key) is True
    if kms_key_id := credentials.kms_key_id:
        assert s3.file_kms_encrypted(bucket, key) is True
        assert s3.file_kms_encrypted(bucket, key, kms_key_id) is True


def sanity_check_google_file(env_google: EnvGoogle,
                             credentials: GoogleCredentials, bucket: str, key: str, file: str) -> None:
    gcs = env_google.non_rclone()
    assert gcs.file_exists(bucket, key) is True
    assert gcs.file_equals(file, bucket, key) is True


def cleanup_amazon_file(env_amazon: EnvAmazon, bucket: str, key: str) -> None:
    s3 = env_amazon.non_rclone()
    assert s3.delete_file(bucket, key) is True
    assert s3.file_exists(bucket, key) is False


def cleanup_google_file(env_google: EnvGoogle, bucket: str, key: str) -> None:
    gcs = env_google.non_rclone()
    assert gcs.delete_file(bucket, key) is True
    assert gcs.file_exists(bucket, key) is False


def _test_utils_for_testing(env_amazon: EnvAmazon) -> None:

    # First of all, test the test code, i.e. the Amazon/Google code which uploads,
    # downloads, verifies, et cetera - WITHOUT using RCloner - in furtherance of the
    # testing of the various RCloner features.

    credentials = env_amazon.credentials()
    _test_utils_for_testing_amazon(env_amazon=env_amazon, credentials=credentials)

    temporary_credentials = env_amazon.temporary_credentials()
    _test_utils_for_testing_amazon(env_amazon=env_amazon, credentials=temporary_credentials)


def _test_utils_for_testing_amazon(env_amazon: EnvAmazon, credentials: AmazonCredentials) -> None:

    assert isinstance(credentials, AmazonCredentials)
    assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
    assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key

    s3 = env_amazon.non_rclone()

    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = env_amazon.file_name_to_key_name(tmp_test_file_name)
        if cloud_path.separator in key:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            assert s3.upload_file(tmp_test_file_path, env_amazon.bucket, key) is True
        else:
            assert s3.upload_file(tmp_test_file_path, env_amazon.bucket) is True
        assert s3.file_exists(env_amazon.bucket, key) is True
        assert s3.file_equals(tmp_test_file_path, env_amazon.bucket, key) is True
        assert s3.file_exists(env_amazon.bucket, key + "-junk-suffix") is False
        assert len(s3_test_files := s3.list_files(env_amazon.bucket, prefix=Env.test_file_prefix)) > 0
        assert len(s3_test_files_found := [f for f in s3_test_files if f["key"] == key]) == 1
        assert s3_test_files_found[0]["key"] == key
        assert len(s3.list_files(env_amazon.bucket, prefix=key)) == 1
        with temporary_random_file() as some_random_file_path:
            assert s3.file_equals(some_random_file_path, env_amazon.bucket, key) is False
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(tmp_downloaded_file_path, env_amazon.bucket, key) is True
            assert s3.download_file("/dev/null", env_amazon.bucket, key) is True
            assert are_files_equal(tmp_test_file_path, tmp_downloaded_file_path) is True
            assert are_files_equal(tmp_test_file_path, "/dev/null") is False
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(tmp_download_directory, env_amazon.bucket, key) is True
            assert are_files_equal(tmp_test_file_path, f"{tmp_download_directory}/{cloud_path.basename(key)}") is True
        assert s3.delete_file(env_amazon.bucket, key) is True
        assert s3.file_exists(env_amazon.bucket, key) is False
        assert s3.file_equals("/dev/null", env_amazon.bucket, key) is False
        assert s3.download_file("/dev/null", env_amazon.bucket, key) is False


def _test_rclone_between_amazon_and_local(env_amazon: EnvAmazon) -> None:

    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=None,
                                           nokms=False)
    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=None,
                                           nokms=True)

    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY,
                                           nokms=False)
    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY,
                                           nokms=True)

    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC,
                                           nokms=False)
    __test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                           credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC,
                                           nokms=True)


def __test_rclone_between_amazon_and_local(env_amazon: EnvAmazon,
                                           credentials_type_amazon: Optional[EnvAmazon.CredentialsType] = None,
                                           nokms: bool = False) -> None:

    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        if credentials_type_amazon == EnvAmazon.CredentialsType.TEMPORARY:
            credentials_amazon = env_amazon.temporary_credentials(nokms=nokms)
        elif credentials_type_amazon == EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC:
            credentials_amazon = env_amazon.temporary_credentials(bucket=env_amazon.bucket, key=key_amazon, nokms=nokms)
        else:
            credentials_amazon = env_amazon.credentials(nokms=nokms)
        target_amazon = create_rclone_target_amazon(credentials_amazon)
        # Upload the local test file to AWS S3 using RCloner;
        # we upload tmp_test_file_path to the key (tmp_test_file_name) key in env_amazon.bucket.
        rcloner = create_rcloner(destination=target_amazon)
        if cloud_path.separator in key_amazon:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            assert rcloner.copy(tmp_test_file_path, cloud_path.join(env_amazon.bucket, key_amazon)) is True
        else:
            assert rcloner.copy(tmp_test_file_path, env_amazon.bucket, copyto=False) is True
        # Sanity check the uploaded file using non-rclone methods (via AwS3 which uses boto3).
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Now try to download the test file (which was uploaded above to AWS S3 using RCloner)
        # to the local file system using RCloner; use the same RCloner configuration as for
        # upload, but as the source rather than the destination.
        rcloner = create_rcloner(source=target_amazon)
        with temporary_directory() as tmp_download_directory:
            rcloner.copy(cloud_path.join(env_amazon.bucket, key_amazon), tmp_download_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_download_directory, cloud_path.basename(key_amazon))) is True
        # Cleanup (delete) the test file in AWS S3.
        cleanup_amazon_file(env_amazon, env_amazon.bucket, key_amazon)


def _test_rclone_between_google_and_local(env_google: EnvGoogle) -> None:
    credentials = env_google.credentials()
    target_google = create_rclone_target_google(credentials)
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to Google Cloud Storage.
        rcloner = create_rcloner(destination=target_google)
        # Upload the local test file to Google Cloud Storage using RCloner; we upload
        # tmp_test_file_path to the key (tmp_test_file_name) key in env_google.bucket.
        if cloud_path.separator in key_google:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rcloner.copy(tmp_test_file_path, cloud_path.join(env_google.bucket, key_google))
        else:
            rcloner.copy(tmp_test_file_path, env_google.bucket, copyto=False)
        # Sanity check the uploaded file using non-rclone methods (via Gcs which uses google.cloud.storage).
        sanity_check_google_file(env_google, credentials, env_google.bucket, key_google, tmp_test_file_path)
        # Now try to download the uploaded test file in Google Cloud Storage using RCloner;
        # use the same RCloner configuration as for upload but as the source rather than destination.
        rcloner = create_rcloner(source=target_google)
        with temporary_directory() as tmp_download_directory:
            rcloner.copy(cloud_path.join(env_google.bucket, key_google), tmp_download_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_download_directory, cloud_path.basename(key_google))) is True
        # Cleanup (delete) the test file in Google Cloud Storage.
        cleanup_google_file(env_google, env_google.bucket, key_google)


def _test_rclone_google_to_amazon(env_amazon: EnvAmazon, env_google: EnvGoogle) -> None:

    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=None,
                                   nokms=False)
    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=None,
                                   nokms=True)

    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY,
                                   nokms=False)
    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY,
                                   nokms=True)

    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC,
                                   nokms=False)
    __test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google,
                                   credentials_type_amazon=EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC,
                                   nokms=True)


def __test_rclone_google_to_amazon(env_amazon: EnvAmazon,
                                   env_google: EnvGoogle,
                                   credentials_type_amazon: Optional[EnvAmazon.CredentialsType] = None,
                                   nokms: bool = False) -> None:

    credentials_google = env_google.credentials()
    rclone_google = create_rclone_target_google(credentials_google)
    # First upload a test file to Google Cloud Storage.
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        if credentials_type_amazon == EnvAmazon.CredentialsType.TEMPORARY:
            credentials_amazon = env_amazon.temporary_credentials(nokms=nokms)
        elif credentials_type_amazon == EnvAmazon.CredentialsType.TEMPORARY_KEY_SPECIFIC:
            credentials_amazon = env_amazon.temporary_credentials(bucket=env_amazon.bucket, key=key_amazon, nokms=nokms)
        else:
            credentials_amazon = env_amazon.credentials(nokms=nokms)
        rclone_amazon = create_rclone_target_amazon(credentials_amazon)
        # Here we have a local test file to upload to Google Cloud Storage;
        # which we will then copy directly to AWS S3 via RCloner.
        # So first upload our local test file to Google Cloud Storage (via RCloner - why not).
        rcloner = create_rcloner(destination=rclone_google)
        if cloud_path.separator in key_google:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rcloner.copy(tmp_test_file_path, cloud_path.join(env_google.bucket, key_google))
        else:
            rcloner.copy(tmp_test_file_path, env_google.bucket, copyto=False)
        # Make sure it made it there.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Now try to copy directly from Google Cloud Storage to AWS S3 (THIS is really the MAIN event).
        rcloner = create_rcloner(source=rclone_google, destination=rclone_amazon)
        if cloud_path.separator in key_amazon:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rcloner.copy(cloud_path.join(env_google.bucket, key_google),
                         cloud_path.join(env_amazon.bucket, key_amazon))
        else:
            rcloner.copy(cloud_path.join(env_google.bucket, key_google), env_amazon.bucket, copyto=False)
        # Sanity check the file in AWS S3 which was copied directly from Google Cloud Storage.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Exercise the RCloneStore rclone commands (path_exists, file_size, file_checksum) for Google file.
        path_cloud = cloud_path.join(env_google.bucket, key_google)
        assert rclone_google.file_size(path_cloud) == Env.test_file_size
        assert rclone_google.path_exists(path_cloud) is True
        assert rclone_google.file_checksum(path_cloud) == get_file_checksum(tmp_test_file_path)
        assert rclone_google.ping() is True
        # Exercise the RCloneStore rclone commands (path_exists, file_size, file_checksum) for Amazon file.
        assert env_amazon.non_rclone().file_size(env_amazon.bucket, key_amazon) == Env.test_file_size
        assert env_amazon.non_rclone().file_exists(env_amazon.bucket, key_amazon) is True
        assert (env_amazon.non_rclone().file_checksum(env_amazon.bucket, key_amazon) ==
                get_file_checksum(tmp_test_file_path))
        # Do the above copy again but this time with the destination
        # bucket specified within the RCloneGoogle object (new: 2024-05-10).
        cleanup_amazon_file(env_amazon, env_amazon.bucket, key_amazon)
        rclone_amazon = create_rclone_target_amazon(credentials_amazon, bucket=env_amazon.bucket)
        rcloner = create_rcloner(source=rclone_google, destination=rclone_amazon)
        assert rclone_amazon.bucket == env_amazon.bucket
        assert rclone_amazon.path("testing-path-function") == f"{env_amazon.bucket}/testing-path-function"
        assert rclone_amazon.path_exists(key_amazon) is False
        if cloud_path.separator in key_amazon:
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rcloner.copy(cloud_path.join(env_google.bucket, key_google), key_amazon)
        else:
            rcloner.copy(cloud_path.join(env_google.bucket, key_google), None, copyto=False)
        # Sanity check the file in AWS S3 which was copied directly from Google Cloud Storage.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Re-exercise the RCloneStore rclone commands (path_exists, file_size, file_checksum) for Amazon file.
        assert env_amazon.non_rclone().file_size(env_amazon.bucket, key_amazon) == Env.test_file_size
        assert env_amazon.non_rclone().file_exists(env_amazon.bucket, key_amazon) is True
        assert (env_amazon.non_rclone().file_checksum(env_amazon.bucket, key_amazon) ==
                get_file_checksum(tmp_test_file_path))
        # Cleanup (delete) the test destination file in AWS S3.
        cleanup_amazon_file(env_amazon, env_amazon.bucket, key_amazon)
        # Cleanup (delete) the test source file in Google Cloud Storage.
        cleanup_google_file(env_google, env_google.bucket, key_google)


def _test_rclone_amazon_to_google(env_amazon: EnvAmazon, env_google: EnvGoogle) -> None:
    credentials_amazon = env_amazon.credentials()
    credentials_google = env_google.credentials()
    rclone_amazon = create_rclone_target_amazon(credentials_amazon)
    rclone_google = create_rclone_target_google(credentials_google)
    # First upload a test file to AWS S3.
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to AWS S3;
        # which we will then copy directly to Google Cloud Storage via RCloner.
        # So first upload our local test file to AWS S3 (via RCloner - why not).
        rcloner = create_rcloner(destination=rclone_amazon)
        if cloud_path.separator in key_google:
            rcloner.copy(tmp_test_file_path, cloud_path.join(env_amazon.bucket, key_amazon))
        else:
            rcloner.copy(tmp_test_file_path, env_amazon.bucket, copyto=False)
        # Make sure it made it there.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Now try to copy directly from AWS S3 to Google Cloud Storage.
        rcloner = create_rcloner(source=rclone_amazon, destination=rclone_google)
        if cloud_path.separator in key_google:
            rcloner.copy(cloud_path.join(env_amazon.bucket, key_amazon),
                         cloud_path.join(env_google.bucket, key_google))
        else:
            rcloner.copy(cloud_path.join(env_amazon.bucket, key_amazon), env_google.bucket, copyto=False)
        # Sanity check the file in Google Cloud Storage which was copied directly from AWS S3.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Cleanup (delete) the test destination file in Google Cloud Storage.
        # Do the above copy again but this time with the destination
        # bucket specified within the RCloneGoogle object (new: 2024-05-10).
        cleanup_google_file(env_google, env_google.bucket, key_google)
        rclone_google = create_rclone_target_google(credentials_google, bucket=env_google.bucket)
        rcloner = create_rcloner(source=rclone_amazon, destination=rclone_google)
        if cloud_path.separator in key_google:
            rcloner.copy(cloud_path.join(env_amazon.bucket, key_amazon), key_google)
        else:
            rcloner.copy(cloud_path.join(env_amazon.bucket, key_amazon), None, copyto=False)
        # Sanity check the file in Google Cloud Storage which was copied directly from AWS S3.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Cleanup (delete) the test destination file in Google Cloud Storage.
        cleanup_google_file(env_google, env_google.bucket, key_google)
        # Cleanup (delete) the test source file in AWS S3.
        cleanup_amazon_file(env_amazon, env_amazon.bucket, key_amazon)


def _test_rclone_local_to_local() -> None:
    # Just for completeness, and pretty much falls out, we
    # support the degenerate case of local file to file copy via rclone.
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        with temporary_file() as tmp_destination_file:
            RCloner().copy(tmp_test_file_path, tmp_destination_file)
            assert are_files_equal(tmp_test_file_path, tmp_destination_file)
        with temporary_directory() as tmp_destination_directory:
            RCloner().copy(tmp_test_file_path, tmp_destination_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_destination_directory, os.path.basename(tmp_test_file_path)))


def test_rclone_local_to_google_copy_to_bucket() -> None:
    # Just an aside (ran across while testing); make sure copyto=False works for sub-folder.
    filesize = 1234
    env_google = EnvGoogle()
    filesystem = Mock_LocalStorage()
    filesystem.create_files(file_one := "subdir/test_file_one.fastq", nbytes=filesize)
    # Bucket is really "bucket" - bucket plus optional sub-folder, which RCloneStore is designed to handle.
    subfolder = f"test-{create_uuid()}"
    bucket_google = cloud_path.join(env_google.bucket, subfolder)
    credentials_google = env_google.credentials()
    rclone_google = RCloneGoogle(credentials_google, bucket=bucket_google)
    rcloner = RCloner(destination=rclone_google)
    assert rcloner.copy_to_bucket(os.path.join(filesystem.root, file_one)) is True
    assert env_google.non_rclone().file_exists(cloud_path.join(bucket_google, os.path.basename(file_one))) is True
    assert env_google.non_rclone().file_exists(bucket_google, os.path.basename(file_one)) is True
    assert env_google.non_rclone().file_size(cloud_path.join(bucket_google, os.path.basename(file_one))) == filesize
    assert env_google.non_rclone().file_size(bucket_google, os.path.basename(file_one)) == filesize
    assert (env_google.non_rclone().file_checksum(cloud_path.join(bucket_google, os.path.basename(file_one))) ==
            get_file_checksum(os.path.join(filesystem.root, file_one)))
    assert env_google.non_rclone().delete_file(rclone_google.bucket, os.path.basename(file_one)) is True
    assert env_google.non_rclone().file_exists(rclone_google.bucket, os.path.basename(file_one)) is False


def testrclone_local_to_amazon_copy_to_bucket() -> None:
    # Just an aside (ran across while testing); make sure copyto=False works for sub-folder.
    filesize = 1236
    env_amazon = EnvAmazon()
    filesystem = Mock_LocalStorage()
    filesystem.create_files(file_one := "subdir/test_file_one.fastq", nbytes=filesize)
    # Bucket is really "bucket" - bucket plus optional sub-folder, which RCloneStore is designed to handle.
    subfolder = f"test-{create_uuid()}"
    bucket_amazon = cloud_path.join(env_amazon.bucket, subfolder)
    credentials_amazon = env_amazon.credentials()
    rclone_amazon = RCloneAmazon(credentials_amazon, bucket=bucket_amazon)
    rcloner = RCloner(destination=rclone_amazon)
    assert rcloner.copy_to_bucket(os.path.join(filesystem.root, file_one)) is True
    assert env_amazon.non_rclone().file_exists(cloud_path.join(bucket_amazon, os.path.basename(file_one))) is True
    assert env_amazon.non_rclone().file_exists(bucket_amazon, os.path.basename(file_one)) is True
    assert env_amazon.non_rclone().file_size(cloud_path.join(bucket_amazon, os.path.basename(file_one))) == filesize
    assert env_amazon.non_rclone().file_size(bucket_amazon, os.path.basename(file_one)) == filesize
    assert (env_amazon.non_rclone().file_checksum(cloud_path.join(bucket_amazon, os.path.basename(file_one))) ==
            get_file_checksum(os.path.join(filesystem.root, file_one)))
    assert env_amazon.non_rclone().delete_file(bucket_amazon, os.path.basename(file_one)) is True
    assert env_amazon.non_rclone().file_exists(bucket_amazon, os.path.basename(file_one)) is False


def test_rclone_amazon_to_amazon() -> None:
    env_amazon = EnvAmazon(use_cloud_subfolder_key=True)
    credentials_amazon = env_amazon.credentials()
    rclone_target_amazon = create_rclone_target_amazon(credentials_amazon)
    bucket_amazon = env_amazon.bucket
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        source_bucket_amazon = bucket_amazon
        source_key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        rcloner = create_rcloner(destination=rclone_target_amazon)
        rcloner.copy(tmp_test_file_path, cloud_path.join(source_bucket_amazon, source_key_amazon))
        source_checksum = get_file_checksum(tmp_test_file_path)
    source_amazon = cloud_path.join(source_bucket_amazon, source_key_amazon)
    destination_bucket_amazon = bucket_amazon
    destination_subfolder_amazon = f"test-{create_uuid()}"
    destination_key_amazon = cloud_path.join(destination_subfolder_amazon, f"test-{create_uuid()}.txt")
    destination_amazon = cloud_path.join(destination_bucket_amazon, destination_key_amazon)
    destination_metadata_amazon = {"some-metadata-key": "some-metadata-value"}
    source_target_amazon = create_rclone_target_amazon(credentials_amazon)
    destination_target_amazon = create_rclone_target_amazon(credentials_amazon)
    rcloner = create_rcloner(source=source_target_amazon, destination=destination_target_amazon)
    rcloner.copy(source_amazon, destination_amazon, metadata=destination_metadata_amazon)
    assert env_amazon.non_rclone().file_size(destination_bucket_amazon,
                                             destination_key_amazon) == TEST_FILE_SIZE
    assert env_amazon.non_rclone().file_exists(destination_bucket_amazon, destination_key_amazon) is True
    assert env_amazon.non_rclone().file_checksum(destination_bucket_amazon,
                                                 destination_key_amazon) == source_checksum
    metadata = env_amazon.non_rclone().file_metadata(destination_bucket_amazon, destination_key_amazon)
    assert isinstance(metadata, dict) is True
    assert metadata["some-metadata-key"] == "some-metadata-value"
    # assert env_amazon.non_rclone().directory_exists(destination_bucket_amazon,
    #                                                    destination_subfolder_amazon) is True  # TODO IMPLEMENT MAYBE
    # assert destination_target_amazon.directory_exists(cloud_path.join(destination_bucket_amazon,
    #                                                                   destination_subfolder_amazon)) is True
    assert env_amazon.non_rclone().delete_file(source_amazon) is True
    assert env_amazon.non_rclone().delete_file(destination_amazon) is True


def test_rclone_amazon_to_amazon_using_temporary_credentials() -> None:
    env_amazon = EnvAmazon(use_cloud_subfolder_key=True)
    credentials_amazon = env_amazon.credentials(nokms=True)
    rclone_target_amazon = create_rclone_target_amazon(credentials_amazon)
    bucket_amazon = env_amazon.bucket
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        source_bucket_amazon = bucket_amazon
        source_key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        rcloner = create_rcloner(destination=rclone_target_amazon)
        rcloner.copy(tmp_test_file_path, cloud_path.join(source_bucket_amazon, source_key_amazon))
        source_checksum = get_file_checksum(tmp_test_file_path)
    source_amazon = cloud_path.join(source_bucket_amazon, source_key_amazon)
    destination_bucket_amazon = bucket_amazon
    destination_subfolder_amazon = f"test-{create_uuid()}"
    destination_key_amazon = cloud_path.join(destination_subfolder_amazon, f"test-{create_uuid()}.txt")
    destination_amazon = cloud_path.join(destination_bucket_amazon, destination_key_amazon)
    destination_metadata_amazon = {"some-metadata-key": "some-metadata-value"}
    # Now use temporary/session credentials to copy from s3 to s3 (ran into permission problems with rclone here).
    temporary_credentials_amazon = env_amazon.temporary_credentials(destination_bucket_amazon,
                                                                    destination_key_amazon, nokms=True)
    source_target_amazon = create_rclone_target_amazon(credentials_amazon)
    destination_target_amazon = create_rclone_target_amazon(temporary_credentials_amazon)
    rcloner = create_rcloner(source=source_target_amazon, destination=destination_target_amazon)
    rcloner.copy(source_amazon, destination_amazon, metadata=destination_metadata_amazon)
    assert env_amazon.non_rclone().file_size(destination_bucket_amazon,
                                             destination_key_amazon) == TEST_FILE_SIZE
    assert env_amazon.non_rclone().file_exists(destination_bucket_amazon, destination_key_amazon) is True
    assert env_amazon.non_rclone().file_checksum(destination_bucket_amazon,
                                                 destination_key_amazon) == source_checksum
    metadata = env_amazon.non_rclone().file_metadata(destination_bucket_amazon, destination_key_amazon)
    assert isinstance(metadata, dict) is True
    assert metadata["some-metadata-key"] == "some-metadata-value"
    #
    # Note that this will not work because although the temporary credentials policy for the destination
    # has a s3:ListBucket, which we need (for some reason) for S3-to-S3 copy, it is, for security reasons,
    # limited to just keys with a prefix which is exactly the destination key; so we (rclone) cannot do a
    # s3:ListBucket (which it evidently wants to do) on just the destination subfolder without the key.
    #
    # assert destination_target_amazon.directory_exists(cloud_path.join(destination_bucket_amazon,
    #                                                                   destination_subfolder_amazon)) is True
    #
    # But we can do it with the main (non-temporary) credentials which we do just as an extra check.
    # destination_target_with_main_credentials_amazon = create_rclone_target_amazon(credentials_amazon)
    # assert destination_target_with_main_credentials_amazon.directory_exists(
    #     cloud_path.join(destination_bucket_amazon, destination_subfolder_amazon)) is True
    #
    assert env_amazon.non_rclone().delete_file(source_amazon) is True
    assert env_amazon.non_rclone().delete_file(destination_amazon) is True


def test_rclone_upload_file_to_aws_s3() -> None:

    filesystem = Mock_LocalStorage(file_one := "subdir/test_file_one.fastq",
                                   file_two := "test_file_two.fastq",
                                   nbytes=(filesize := 1235))
    env_google = EnvGoogle()
    bucket_google = f"{env_google.bucket}/test-{create_uuid()}"
    rclone_google = RCloneGoogle(env_google.credentials(), bucket=bucket_google)
    rcloner = RCloner(destination=rclone_google)
    # Note that the second destination argument to RCloner.copy can be
    # unspecified meaning that it will be the *bucket* ("bucket" - can be
    assert rcloner.copy_to_bucket(os.path.join(filesystem.root, file_one)) is True
    assert env_google.non_rclone().file_size(cloud_path.join(bucket_google, os.path.basename(file_one))) == filesize
    assert env_google.non_rclone().file_size(bucket_google, os.path.basename(file_one)) == filesize
    files = [{"filename": file_one}, {"filename": file_two}]
    files_for_upload = FilesForUpload.assemble(files,
                                               main_search_directory=filesystem.root,
                                               main_search_directory_recursively=True,
                                               cloud_store=rclone_google)
    assert len(files_for_upload) == 2
    assert files_for_upload[0].found is True
    assert files_for_upload[0].found_local is True
    assert files_for_upload[0].found_cloud is True
    assert files_for_upload[0].path_local == os.path.join(filesystem.root, file_one)
    assert files_for_upload[0].size_local == filesize
    assert files_for_upload[0].checksum_local == get_file_checksum(os.path.join(filesystem.root, file_one))
    assert files_for_upload[0].path_cloud == cloud_path.join(bucket_google, files_for_upload[0].name)
    assert files_for_upload[0].size_cloud == filesize
    assert files_for_upload[0].checksum_cloud == get_file_checksum(os.path.join(filesystem.root, file_one))
    # Found both locally and in Google; ambiguous, as favor_local starts as None;
    # so these return False/None; favor_local normally gets resolved in review function.
    assert files_for_upload[0].favor_local is None
    assert files_for_upload[0].from_local is False
    assert files_for_upload[0].from_cloud is False
    assert files_for_upload[0].path is None
    assert files_for_upload[0].size is None
    assert files_for_upload[0].checksum is None
    files_for_upload[0]._favor_local = True  # normally resolved by FileForUpload.review
    assert files_for_upload[0].favor_local is True
    assert files_for_upload[0].from_local is True
    assert files_for_upload[0].from_cloud is False
    assert files_for_upload[0].path == os.path.join(filesystem.root, file_one)
    assert files_for_upload[0].size == filesize
    assert len(files_for_upload[0].checksum) > 0
    files_for_upload[0]._favor_local = False  # normally resolved by FileForUpload.review
    assert files_for_upload[0].favor_local is False
    assert files_for_upload[0].from_local is False
    assert files_for_upload[0].from_cloud is True
    assert files_for_upload[0].path == cloud_path.join(rclone_google.bucket, files_for_upload[0].name)
    assert files_for_upload[0].size == filesize
    assert files_for_upload[0].checksum == get_file_checksum(os.path.join(filesystem.root, file_one))
    assert files_for_upload[1].found is True
    assert files_for_upload[1].found_local is True
    assert files_for_upload[1].found_cloud is False
    assert files_for_upload[1].favor_local is True
    assert files_for_upload[1].from_local is True
    assert files_for_upload[1].from_cloud is False
    assert files_for_upload[1].path == os.path.join(filesystem.root, file_two)
    assert files_for_upload[1].size == filesize
    assert files_for_upload[1].checksum == get_file_checksum(os.path.join(filesystem.root, file_two))

    env_amazon = EnvAmazon()
    s3_key = f"test-{create_uuid()}/SMAFIPIGC8NG.fastq"
    s3_uri = f"s3://{env_amazon.bucket}/{s3_key}"
    credentials_amazon = env_amazon.temporary_credentials(env_amazon.bucket, s3_key)
    # FYI the output of this looks something like this (but not specifically checking for now):
    # ▶ Upload: test_file_one.fastq (1.21 KB) ...
    #   - From: gs://smaht-submitr-rclone-testing/test_file_one.fastq
    #   -   To: s3://smaht-unit-testing-files/test-9eFJ8iZHG5ayrTEuSvz7G4upKVJdtpJ/SMAFIPIGC8NG.fastq
    # ▶ Upload progress ✓ 100% ◀|###########| 1234/1235 | 1.16 MB/s | 00:00 | ETA: 00:00
    # ▶ Upload progress ✓ 100% ◀|###########| 1235/1235 | 3.53 KB/s | 00:00 | ETA: 00:00
    # Verifying upload: test_file_one.fastq ... OK
    upload_file_to_aws_s3(file=files_for_upload[0],
                          s3_uri=s3_uri,
                          aws_credentials=credentials_amazon.to_dictionary(environment_names=True))
    assert env_amazon.non_rclone().file_exists(env_amazon.bucket, s3_key) is True
    assert env_amazon.non_rclone().file_size(env_amazon.bucket, s3_key) == filesize
    assert (env_amazon.non_rclone().file_checksum(env_amazon.bucket, s3_key) ==
            get_file_checksum(os.path.join(filesystem.root, file_one)))
    s3_key_metadata = get_s3_key_metadata(credentials_amazon.to_dictionary(environment_names=False),
                                          env_amazon.bucket, s3_key)
    assert isinstance(s3_key_metadata, dict)
    assert s3_key_metadata["size"] == filesize
    assert s3_key_metadata["size"] == filesize
    assert s3_key_metadata["md5"] == get_file_checksum(os.path.join(filesystem.root, file_one))
    assert s3_key_metadata["md5-source"] == "google-cloud-storage"
    assert env_amazon.non_rclone().delete_file(env_amazon.bucket, s3_key) is True
    assert env_amazon.non_rclone().file_exists(env_amazon.bucket, s3_key) is False
    assert env_google.non_rclone().delete_file(rclone_google.bucket, files_for_upload[0].name) is True
    assert env_google.non_rclone().file_exists(rclone_google.bucket, files_for_upload[0].name) is False


def test_rclone_do_any_uploads() -> None:
    filesystem = Mock_LocalStorage()
    metadata_file = "metadata_file.xlsx"
    test_file_subdirectory = "subdir"
    test_file_one = "test_file_one.fastq"
    test_file_two = "test_file_two.fastq"
    filesystem.create_files(file_one := os.path.join(test_file_subdirectory, test_file_one), metadata_file)
    env_google = EnvGoogle()
    env_amazon = EnvAmazon()
    rclone_google = RCloneGoogle(env_google.credentials(), bucket=f"{env_google.bucket}/test-{create_uuid()}")
    rcloner = RCloner(destination=rclone_google)
    assert rcloner.copy_to_key(filesystem.path(file_one), key_google := test_file_two) is True
    assert env_google.non_rclone().file_exists(rclone_google.bucket, key_google) is True
    assert env_google.non_rclone().file_size(rclone_google.bucket, key_google) == TEST_FILE_SIZE

    uploaded_uris_amazon = []

    def mocked_generate_credentials_for_upload(file, uuid, portal):
        nonlocal env_amazon, uploaded_uris_amazon
        bucket_amazon = f"{env_amazon.bucket}/test-{create_uuid()}"
        key_amazon = f"SMA-{create_uuid()}.fastq"
        aws_s3_uri = f"s3://{bucket_amazon}/{key_amazon}"
        uploaded_uris_amazon.append(aws_s3_uri)
        aws_credentials = env_amazon.temporary_credentials(bucket_amazon,
                                                           key_amazon).to_dictionary(environment_names=True)
        aws_kms_key_id = AMAZON_KMS_KEY_ID
        return aws_s3_uri, aws_credentials, aws_kms_key_id

    # TODO
    # To call do_any_uploads we need a Portal object which needs mock its get_schema_type, is_schema_type,
    # is_schema_file_type functions; no need to mock get_metadata, patch_metadata, get_health, which are also
    # called from submission_uploads module, so long as we don't pass a IngestionSubmission UUID to do_any_uploads,
    # but rather pass files dictionary; and also need to mock submission_uploads.generate_credentials_for_upload.
    # Alternatively, easier, is just provide a StructuredDataSet with a simple upload_files property which is an
    # list of dictionary with file names.
    with mock_patch("submitr.submission_uploads.generate_credentials_for_upload") as \
            mock_generate_credentials_for_upload, \
            mock_patch("submitr.submission_uploads.yes_or_no", return_value="yes"):
        ingestion_submission_object = load_json_test_data("ingestion_submission")  # noqa
        mock_generate_credentials_for_upload.side_effect = mocked_generate_credentials_for_upload
        do_any_uploads(ingestion_submission_object,
                       metadata_file=metadata_file,
                       main_search_directory=os.path.join(filesystem.root, test_file_subdirectory),
                       main_search_directory_recursively=True,
                       cloud_store=rclone_google,
                       portal=Mock_Portal(),
                       review_only=False,
                       verbose=False)

    for uploaded_uri_amazon in uploaded_uris_amazon:
        bucket_amazon, key_amazon = cloud_path.bucket_and_key(uploaded_uri_amazon)
        assert env_amazon.non_rclone().file_exists(bucket_amazon, key_amazon) is True
        assert env_amazon.non_rclone().delete_file(bucket_amazon, key_amazon) is True
        assert env_amazon.non_rclone().file_exists(bucket_amazon, key_amazon) is False

    # Cleanup.
    assert env_google.non_rclone().delete_file(rclone_google.bucket, key_google) is True
    assert env_google.non_rclone().file_exists(rclone_google.bucket, key_google) is False


def test_rclone_store_bucket_exists_amazon() -> None:
    env_amazon = EnvAmazon()
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        base_subfolder_name = f"test-{create_uuid()}"
        bucket_and_folder = cloud_path.join(env_amazon.bucket, base_subfolder_name, "test-abc", "test-def")
        assert env_amazon.non_rclone().create_folder(bucket_and_folder) is True
        amazon_store = RCloneAmazon(env_amazon.credentials(), bucket=bucket_and_folder)
        # This returns False because (as described in the RCloneStore.bucket_exists doc),
        # the sub-folder does not contain a key.
        assert amazon_store.bucket_exists() is False
        # Now copy an actual file to that sub-folder.
        assert env_amazon.non_rclone().upload_file(tmp_test_file_path, bucket_and_folder + cloud_path.separator) is True
        cloud_file_path = cloud_path.join(bucket_and_folder, tmp_test_file_name)
        assert env_amazon.non_rclone().file_exists(cloud_file_path) is True
        # And now this returns True.
        assert amazon_store.bucket_exists() is True
        assert env_amazon.non_rclone().delete_file(cloud_file_path) is True
        assert env_amazon.non_rclone().delete_folders(env_amazon.bucket, base_subfolder_name) is True


def test_rclone_store_bucket_exists_google() -> None:
    env_google = EnvGoogle()
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        base_subfolder_name = f"test-{create_uuid()}"
        bucket_and_folder = cloud_path.join(env_google.bucket, base_subfolder_name, "test-abc", "test-def")
        assert env_google.non_rclone().create_folder(bucket_and_folder) is True
        google_store = RCloneGoogle(env_google.credentials(), bucket=bucket_and_folder)
        # This returns False because (as described in the RCloneStore.bucket_exists doc),
        # the sub-folder does not contain a key.
        assert google_store.bucket_exists() is False
        # Now copy an actual file to that sub-folder.
        assert env_google.non_rclone().upload_file(tmp_test_file_path, bucket_and_folder + cloud_path.separator) is True
        cloud_file_path = cloud_path.join(bucket_and_folder, tmp_test_file_name)
        assert env_google.non_rclone().file_exists(cloud_file_path) is True
        # And now this returns True.
        assert google_store.bucket_exists() is True
        assert env_google.non_rclone().delete_file(cloud_file_path) is True
        assert env_google.non_rclone().delete_folders(env_google.bucket, base_subfolder_name) is True


def test_rclone_copy_to_folder() -> None:
    env_amazon = EnvAmazon()
    with Env.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        amazon_base_subfolder = f"test-{create_uuid()}"
        amazon_subfolder = cloud_path.join(f"{amazon_base_subfolder}",
                                           "test-abc", "test-def", "/", preserve_suffix=True)
        amazon_bucket_and_folder = cloud_path.join(env_amazon.bucket, amazon_subfolder)
        amazon_store = RCloneAmazon(env_amazon.credentials(), bucket=amazon_bucket_and_folder)
        rcloner = RCloner(destination=amazon_store)
        rcloner.copy(tmp_test_file_path, cloud_path.separator)
        assert env_amazon.non_rclone().file_exists(cloud_path.join(amazon_bucket_and_folder,
                                                                   tmp_test_file_name)) is True
        assert env_amazon.non_rclone().delete_folders(env_amazon.bucket, amazon_base_subfolder) is True
