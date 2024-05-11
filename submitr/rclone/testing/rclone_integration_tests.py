from contextlib import contextmanager
import os
from typing import Callable, Optional, Tuple, Union
from dcicutils.file_utils import are_files_equal, compute_file_md5
from dcicutils.misc_utils import create_short_uuid
from dcicutils.tmpfile_utils import temporary_directory, temporary_file, temporary_random_file
from submitr.rclone.rclone import RClone
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_config_amazon import AmazonCredentials, RCloneConfigAmazon
from submitr.rclone.rclone_config_google import GoogleCredentials, RCloneConfigGoogle
from submitr.rclone.rclone_utils import cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials, AwsS3
from submitr.rclone.testing.rclone_utils_for_testing_google import Gcs

# Integration tests for RClone related functionality within smaht-submitr.
# Need valid AWS credentials for (currently) smaht-wolf.
# Need valid Google Cloud credentials for (currently) project smaht-dac.
# Wonder how to possibly test this as unit test within GA?


class TestEnv:

    test_file_prefix = "test-smaht-submitr-"
    test_file_suffix = ".txt"
    test_file_size = 2048

    def __init__(self, user_cloud_subfolder_key: bool = False):
        self.user_cloud_subfolder_key = True if (user_cloud_subfolder_key is True) else False
        self.bucket = None

    @staticmethod
    @contextmanager
    def temporary_test_file() -> Tuple[str, str]:
        with temporary_random_file(prefix=TestEnv.test_file_prefix,
                                   suffix=TestEnv.test_file_suffix,
                                   nbytes=TestEnv.test_file_size) as tmp_file_path:
            yield tmp_file_path, os.path.basename(tmp_file_path)

    def file_name_to_key_name(self, file_name: str) -> str:
        # Assumed that the given file name is just that, a file base name, not a path name.
        if not (self.user_cloud_subfolder_key is True):
            return file_name
        else:
            return cloud_path.join(f"{TestEnv.test_file_prefix}{create_short_uuid(length=8)}", file_name)


class TestEnvAmazon(TestEnv):

    def __init__(self, user_cloud_subfolder_key: bool = False):
        # Specifying the env name here (as smaht-wolf) will cause
        # AwsCredentials to read from: ~/.aws_test.smaht-wolf/credentials
        # In addition to the basic credentials (access_key_id, secret_access_key,
        # optional session_token), this is also assumed to also contain the region.
        # For the kms_key_id see ENCODED_S3_ENCRYPT_KEY_ID in AWS C4AppConfigSmahtWolf Secrets.
        super().__init__(user_cloud_subfolder_key=user_cloud_subfolder_key)
        self.env = "smaht-wolf"
        self.kms_key_id = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"
        self.bucket = "smaht-unit-testing-files"
        self.main_credentials = self.credentials()

    def credentials(self, nokms: bool = False) -> AmazonCredentials:
        kms_key_id = None if nokms is True else self.kms_key_id
        credentials = AwsCredentials.get_credentials_from_file(self.env, kms_key_id=kms_key_id)
        assert isinstance(credentials.region, str) and credentials.region
        assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
        assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key
        assert credentials.kms_key_id == (None if nokms is True else self.kms_key_id)
        return credentials

    def credentials_nokms(self) -> AmazonCredentials:
        return self.credentials(nokms=True)

    def temporary_credentials(self, nokms: bool = False,
                              bucket: Optional[str] = None, key: Optional[str] = None) -> AmazonCredentials:
        s3 = self.s3_non_rclone()
        kms_key_id = None if nokms else self.kms_key_id
        temporary_credentials = s3.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=kms_key_id)
        assert isinstance(temporary_credentials.session_token, str) and temporary_credentials.session_token
        pass
        assert temporary_credentials.kms_key_id == (None if nokms is True else self.kms_key_id)
        return temporary_credentials

    def temporary_credentials_nokms(self, bucket: Optional[str] = None, key: Optional[str] = None) -> AmazonCredentials:
        return self.temporary_credentials(nokms=True, bucket=bucket, key=key)

    def s3_non_rclone(self):
        return AwsS3(self.main_credentials)


class TestEnvGoogle(TestEnv):

    def __init__(self, user_cloud_subfolder_key: bool = False):
        # The Google test account project is: smaht-dac
        super().__init__(user_cloud_subfolder_key=user_cloud_subfolder_key)
        self.location = "us-east1"
        self.service_account_file = "/Users/dmichaels/.config/google-cloud/smaht-dac-617e0480d8e2.json"
        self.project_id = "smaht-dac"
        self.bucket = "smaht-submitr-rclone-testing"

    def credentials(self) -> GoogleCredentials:
        credentials = GoogleCredentials(location=self.location, service_account_file=self.service_account_file)
        assert credentials.location == self.location
        assert credentials.service_account_file == self.service_account_file
        assert os.path.isfile(credentials.service_account_file)
        return credentials


def initial_setup_and_sanity_checking(env_amazon: TestEnvAmazon, env_google: TestEnvGoogle) -> None:

    AwsCredentials.remove_credentials_from_environment_variables()
    assert os.environ.get("AWS_DEFAULT_REGION", None) is None
    assert os.environ.get("AWS_ACCESS_KEY_ID", None) is None
    assert os.environ.get("AWS_SECRET_ACCESS_KEY", None) is None
    assert os.environ.get("AWS_SESSION_TOKEN", None) is None

    s3 = env_amazon.s3_non_rclone()
    assert s3.bucket_exists(env_amazon.bucket) is True

    credentials_google = env_google.credentials()
    assert os.path.isfile(credentials_google.service_account_file)
    gcs = Gcs(credentials_google)
    assert gcs.bucket_exists(env_google.bucket) is True


def create_rclone_config_amazon(credentials: AmazonCredentials) -> RCloneConfig:
    config = RCloneConfigAmazon(credentials)
    assert config.credentials == credentials
    assert config.access_key_id == credentials.access_key_id
    assert config.secret_access_key == credentials.secret_access_key
    assert config.session_token == credentials.session_token
    assert config.kms_key_id == credentials.kms_key_id
    assert RCloneConfigAmazon(config) == config  # checking equals override
    assert RCloneConfigAmazon(config, bucket="mismatch") != config  # checking equals override
    return config


def create_rclone_config_google(credentials: GoogleCredentials, env_google: TestEnvGoogle) -> RCloneConfig:
    config = RCloneConfigGoogle(credentials)
    assert config.credentials == credentials
    assert config.location == credentials.location
    assert config.service_account_file == credentials.service_account_file
    assert RCloneConfigGoogle(config) == config  # checking equals override
    assert RCloneConfigGoogle(config, bucket="mismatch") != config  # checking equals override
    assert config.project == env_google.project_id
    return config


def create_rclone(source: Optional[RCloneConfig] = None, destination: Optional[RCloneConfig] = None) -> RClone:
    rclone = RClone(source=source, destination=destination)
    assert rclone.source == source
    assert rclone.destination == destination
    return rclone


def sanity_check_amazon_file(env_amazon: TestEnvAmazon,
                             credentials: AmazonCredentials, bucket: str, key: str, file: str) -> None:
    s3 = env_amazon.s3_non_rclone()
    assert s3.file_exists(bucket, key) is True
    assert s3.file_equals(bucket, key, file) is True
    if kms_key_id := credentials.kms_key_id:
        assert s3.file_kms_encrypted(bucket, key) is True
        assert s3.file_kms_encrypted(bucket, key, kms_key_id) is True


def sanity_check_google_file(env_google: TestEnvGoogle,
                             credentials: GoogleCredentials, bucket: str, key: str, file: str) -> None:
    gcs = Gcs(credentials)
    assert gcs.credentials == credentials
    assert gcs.file_exists(bucket, key) is True
    assert gcs.file_equals(bucket, key, file) is True


def cleanup_amazon_file(env_amazon: TestEnvAmazon, credentials: AmazonCredentials, bucket: str, key: str) -> None:
    s3 = env_amazon.s3_non_rclone()
    assert s3.delete_file(bucket, key) is True
    assert s3.file_exists(bucket, key) is False


def cleanup_google_file(credentials: GoogleCredentials, bucket: str, key: str) -> None:
    gcs = Gcs(credentials)
    assert gcs.credentials == credentials
    assert gcs.delete_file(bucket, key) is True
    assert gcs.file_exists(bucket, key) is False


def test_utils_for_testing(env_amazon: TestEnvAmazon) -> None:

    # First of all, test the test code, i.e. the Amazon/Google code which uploads,
    # downloads, verifies, et cetera - WITHOUT using RClone - in furtherance of the
    # testing of the various RClone features.

    credentials = env_amazon.credentials()
    _test_utils_for_testing_amazon(env_amazon=env_amazon, credentials=credentials)

    temporary_credentials = env_amazon.temporary_credentials()
    _test_utils_for_testing_amazon(env_amazon=env_amazon, credentials=temporary_credentials)


def _test_utils_for_testing_amazon(env_amazon: TestEnvAmazon, credentials: AmazonCredentials) -> None:

    assert isinstance(credentials, AmazonCredentials)
    assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
    assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key

    s3 = env_amazon.s3_non_rclone()

    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = env_amazon.file_name_to_key_name(tmp_test_file_name)
        if cloud_path.has_separator(key):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            assert s3.upload_file(tmp_test_file_path, env_amazon.bucket, key) is True
        else:
            assert s3.upload_file(tmp_test_file_path, env_amazon.bucket) is True
        assert s3.file_exists(env_amazon.bucket, key) is True
        assert s3.file_equals(env_amazon.bucket, key, tmp_test_file_path) is True
        assert s3.file_exists(env_amazon.bucket, key + "-junk-suffix") is False
        # assert len(s3_test_files := s3.list_files(env_amazon.bucket, prefix="test")) > 0
        assert len(s3_test_files := s3.list_files(env_amazon.bucket, prefix=TestEnv.test_file_prefix)) > 0
        # assert len(s3_test_files := s3.list_files(env_amazon.bucket, prefix="test")) > 0
        assert len(s3_test_files_found := [f for f in s3_test_files if f["key"] == key]) == 1
        assert s3_test_files_found[0]["key"] == key
        assert len(s3.list_files(env_amazon.bucket, prefix=key)) == 1
        with temporary_random_file() as some_random_file_path:
            assert s3.file_equals(env_amazon.bucket, key, some_random_file_path) is False
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(env_amazon.bucket, key, tmp_downloaded_file_path) is True
            assert s3.download_file(env_amazon.bucket, key, "/dev/null") is True
            assert are_files_equal(tmp_test_file_path, tmp_downloaded_file_path) is True
            assert are_files_equal(tmp_test_file_path, "/dev/null") is False
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(env_amazon.bucket, key, tmp_download_directory) is True
            assert are_files_equal(tmp_test_file_path, f"{tmp_download_directory}/{key}") is True
        assert s3.delete_file(env_amazon.bucket, key) is True
        assert s3.file_exists(env_amazon.bucket, key) is False
        assert s3.file_equals(env_amazon.bucket, key, "/dev/null") is False
        assert s3.download_file(env_amazon.bucket, key, "/dev/null") is False


def test_rclone_between_amazon_and_local(env_amazon: TestEnvAmazon) -> None:

    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.credentials)
    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.credentials_nokms)

    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.temporary_credentials,
                                          use_key_specific_credentials=False)
    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.temporary_credentials_nokms,
                                          use_key_specific_credentials=False)

    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.temporary_credentials,
                                          use_key_specific_credentials=True)
    _test_rclone_between_amazon_and_local(env_amazon=env_amazon,
                                          credentials=env_amazon.temporary_credentials_nokms,
                                          use_key_specific_credentials=True)


def _test_rclone_between_amazon_and_local(env_amazon: TestEnvAmazon,
                                          credentials: Union[Callable, AmazonCredentials],
                                          use_key_specific_credentials: bool = False) -> None:

    if isinstance(credentials, AmazonCredentials):
        credentials = lambda: credentials  # noqa
    elif not callable(credentials):
        assert False

    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to AWS S3.
        if use_key_specific_credentials is True:
            # Here we create (temporary) credentials with policies targetted to a specific bucket/key.
            credentials = credentials(bucket=env_amazon.bucket, key=key_amazon)
        else:
            credentials = credentials()
        config = create_rclone_config_amazon(credentials)
        # Upload the local test file to AWS S3 using RClone;
        # we upload tmp_test_file_path to the key (tmp_test_file_name) key in env_amazon.bucket.
        rclone = create_rclone(destination=config)
        if cloud_path.has_separator(key_amazon):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            assert rclone.copy(tmp_test_file_path, cloud_path.join(env_amazon.bucket, key_amazon)) is True
        else:
            assert rclone.copy(tmp_test_file_path, env_amazon.bucket, copyto=False) is True
        # Sanity check the uploaded file using non-RClone methods (via AwS3 which uses boto3).
        sanity_check_amazon_file(env_amazon, credentials, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Now try to download the test file (which was uploaded above to AWS S3 using RClone) to the local file system
        # using RClone; use the same RClone configuration as for upload, but as the source rather than the destination.
        rclone = create_rclone(source=config)
        with temporary_directory() as tmp_download_directory:
            rclone.copy(cloud_path.join(env_amazon.bucket, key_amazon), tmp_download_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_download_directory, cloud_path.to_file_path(key_amazon))) is True
        # Cleanup (delete) the test file in AWS S3.
        cleanup_amazon_file(env_amazon, credentials, env_amazon.bucket, key_amazon)


def test_rclone_between_google_and_local(env_google: TestEnvGoogle) -> None:
    credentials = env_google.credentials()
    config = create_rclone_config_google(credentials, env_google)
    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to Google Cloud Storage.
        rclone = create_rclone(destination=config)
        # Upload the local test file to Google Cloud Storage using RClone; we upload
        # tmp_test_file_path to the key (tmp_test_file_name) key in env_google.bucket.
        if cloud_path.has_separator(key_google):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rclone.copy(tmp_test_file_path, cloud_path.join(env_google.bucket, key_google))
        else:
            rclone.copy(tmp_test_file_path, env_google.bucket, copyto=False)
        # Sanity check the uploaded file using non-RClone methods (via Gcs which uses google.cloud.storage).
        sanity_check_google_file(env_google, credentials, env_google.bucket, key_google, tmp_test_file_path)
        # Now try to download the uploaded test file in Google Cloud Storage using RClone;
        # use the same RClone configuration as for upload but as the source rather than destination.
        rclone = create_rclone(source=config)
        with temporary_directory() as tmp_download_directory:
            rclone.copy(cloud_path.join(env_google.bucket, key_google), tmp_download_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_download_directory, cloud_path.to_file_path(key_google))) is True
        # Cleanup (delete) the test file in Google Cloud Storage.
        cleanup_google_file(credentials, env_google.bucket, key_google)


def test_rclone_google_to_amazon(env_amazon: TestEnvAmazon, env_google: TestEnvGoogle) -> None:
    credentials_google = env_google.credentials()
    credentials_amazon = env_amazon.credentials()
    rclone_config_google = create_rclone_config_google(credentials_google, env_google)
    rclone_config_amazon = create_rclone_config_amazon(credentials_amazon)
    # First upload a test file to Google Cloud Storage.
    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to Google Cloud Storage;
        # which we will then copy directly to AWS S3 via RClone.
        # So first upload our local test file to Google Cloud Storage (via RClone - why not).
        rclone = create_rclone(destination=rclone_config_google)
        if cloud_path.has_separator(key_google):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rclone.copy(tmp_test_file_path, cloud_path.join(env_google.bucket, key_google))
        else:
            rclone.copy(tmp_test_file_path, env_google.bucket, copyto=False)
        # Make sure it made it there.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Now try to copy directly from Google Cloud Storage to AWS S3 (THIS is really the MAIN event).
        rclone = create_rclone(source=rclone_config_google, destination=rclone_config_amazon)
        if cloud_path.has_separator(key_amazon):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rclone.copy(cloud_path.join(env_google.bucket, key_google),
                        cloud_path.join(env_amazon.bucket, key_amazon))
        else:
            rclone.copy(cloud_path.join(env_google.bucket, key_google), env_amazon.bucket, copyto=False)
        # Sanity check the file in AWS S3 which was copied directly from Google Cloud Storage.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Exercise the RCloneConfig rclone commands (path_exists, file_size, file_checksum) for Google file.
        path_google = cloud_path.join(env_google.bucket, key_google)
        assert rclone_config_google.file_size(path_google) == TestEnv.test_file_size
        assert rclone_config_google.path_exists(path_google) is True
        assert rclone_config_google.file_checksum(path_google) == compute_file_md5(tmp_test_file_path)
        assert rclone_config_google.ping() is True
        # Exercise the RCloneConfig rclone commands (path_exists, file_size, file_checksum) for Amazon file.
        amazon_path = cloud_path.join(env_amazon.bucket, key_amazon)
        assert rclone_config_amazon.file_size(amazon_path) == TestEnv.test_file_size
        assert rclone_config_amazon.path_exists(amazon_path) is True
        assert rclone_config_amazon.file_checksum(amazon_path) == compute_file_md5(tmp_test_file_path)
        assert rclone_config_amazon.ping() is True
        # Do the above copy again but this time with the destination
        # bucket specified within the RCloneConfigGoogle object (new: 2024-05-10).
        cleanup_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon)
        rclone_config_amazon.bucket = env_amazon.bucket
        if cloud_path.has_separator(key_amazon):
            # If we are uploading to a key which has a slash (i.e. a folder-like key) then we
            # will specify the key explicitly, otherwise it will use just the basename of the
            # file (i.e. tmp_test_file_name); we can do this also even if the key does not have
            # a slash, but good to test specifying no key at all, i.e. in the else clause below.
            rclone.copy(cloud_path.join(env_google.bucket, key_google), key_amazon)
        else:
            rclone.copy(cloud_path.join(env_google.bucket, key_google), None, copyto=False)
        # Sanity check the file in AWS S3 which was copied directly from Google Cloud Storage.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Re-exercise the RCloneConfig rclone commands (path_exists, file_size, file_checksum) for Amazon file.
        assert rclone_config_amazon.file_size(key_amazon) == TestEnv.test_file_size
        assert rclone_config_amazon.path_exists(key_amazon) is True
        assert rclone_config_amazon.file_checksum(key_amazon) == compute_file_md5(tmp_test_file_path)
        # Cleanup (delete) the test destination file in AWS S3.
        cleanup_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon)
        # Cleanup (delete) the test source file in Google Cloud Storage.
        cleanup_google_file(credentials_google, env_google.bucket, key_google)


def test_rclone_amazon_to_google(env_amazon: TestEnvAmazon, env_google: TestEnvGoogle) -> None:
    credentials_amazon = env_amazon.credentials()
    credentials_google = env_google.credentials()
    rclone_config_amazon = create_rclone_config_amazon(credentials_amazon)
    rclone_config_google = create_rclone_config_google(credentials_google, env_google)
    # First upload a test file to AWS S3.
    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key_amazon = env_amazon.file_name_to_key_name(tmp_test_file_name)
        key_google = env_google.file_name_to_key_name(tmp_test_file_name)
        # Here we have a local test file to upload to AWS S3;
        # which we will then copy directly to Google Cloud Storage via RClone.
        # So first upload our local test file to AWS S3 (via RClone - why not).
        rclone = create_rclone(destination=rclone_config_amazon)
        if cloud_path.has_separator(key_google):
            rclone.copy(tmp_test_file_path, cloud_path.join(env_amazon.bucket, key_amazon))
        else:
            rclone.copy(tmp_test_file_path, env_amazon.bucket, copyto=False)
        # Make sure it made it there.
        sanity_check_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon, tmp_test_file_path)
        # Now try to copy directly from AWS S3 to Google Cloud Storage.
        rclone = create_rclone(source=rclone_config_amazon, destination=rclone_config_google)
        if cloud_path.has_separator(key_google):
            rclone.copy(cloud_path.join(env_amazon.bucket, key_amazon),
                        cloud_path.join(env_google.bucket, key_google))
        else:
            rclone.copy(cloud_path.join(env_amazon.bucket, key_amazon), env_google.bucket, copyto=False)
        # Sanity check the file in Google Cloud Storage which was copied directly from AWS S3.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Cleanup (delete) the test destination file in Google Cloud Storage.
        # Do the above copy again but this time with the destination
        # bucket specified within the RCloneConfigGoogle object (new: 2024-05-10).
        cleanup_google_file(credentials_google, env_google.bucket, key_google)
        rclone_config_google.bucket = env_google.bucket
        rclone = create_rclone(source=rclone_config_amazon, destination=rclone_config_google)
        if cloud_path.has_separator(key_google):
            rclone.copy(cloud_path.join(env_amazon.bucket, key_amazon), key_google)
        else:
            rclone.copy(cloud_path.join(env_amazon.bucket, key_amazon), None, copyto=False)
        # Sanity check the file in Google Cloud Storage which was copied directly from AWS S3.
        sanity_check_google_file(env_google, credentials_google, env_google.bucket, key_google, tmp_test_file_path)
        # Cleanup (delete) the test destination file in Google Cloud Storage.
        cleanup_google_file(credentials_google, env_google.bucket, key_google)
        # Cleanup (delete) the test source file in AWS S3.
        cleanup_amazon_file(env_amazon, credentials_amazon, env_amazon.bucket, key_amazon)


def test_rclone_local_to_local() -> None:
    # Just for completeness, and pretty much falls out, we
    # support the degenerate case of local file to file copy via rclone.
    with TestEnv.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        with temporary_file() as tmp_destination_file:
            RClone().copy(tmp_test_file_path, tmp_destination_file)
            assert are_files_equal(tmp_test_file_path, tmp_destination_file)
        with temporary_directory() as tmp_destination_directory:
            RClone().copy(tmp_test_file_path, tmp_destination_directory, copyto=False)
            assert are_files_equal(tmp_test_file_path,
                                   os.path.join(tmp_destination_directory, os.path.basename(tmp_test_file_path)))


def test_cloud_variations(user_cloud_subfolder_key: bool = False):

    env_amazon = TestEnvAmazon(user_cloud_subfolder_key=user_cloud_subfolder_key)
    env_google = TestEnvGoogle(user_cloud_subfolder_key=user_cloud_subfolder_key)
    initial_setup_and_sanity_checking(env_amazon=env_amazon, env_google=env_google)
    test_utils_for_testing(env_amazon=env_amazon)
    test_rclone_between_amazon_and_local(env_amazon=env_amazon)
    test_rclone_between_google_and_local(env_google=env_google)
    test_rclone_google_to_amazon(env_amazon=env_amazon, env_google=env_google)
    test_rclone_amazon_to_google(env_amazon=env_amazon, env_google=env_google)


def test():
    test_cloud_variations(user_cloud_subfolder_key=True)
    test_cloud_variations(user_cloud_subfolder_key=False)
    test_rclone_local_to_local()


test()
