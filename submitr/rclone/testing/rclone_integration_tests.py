from contextlib import contextmanager
import os
from typing import Callable, Optional, Tuple, Union
from dcicutils.file_utils import are_files_equal
from dcicutils.tmpfile_utils import temporary_directory, temporary_file, temporary_random_file
from submitr.rclone.rclone import RClone
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_config_amazon import AmazonCredentials, RCloneConfigAmazon
from submitr.rclone.rclone_config_google import GoogleCredentials, RCloneConfigGoogle
from submitr.rclone.testing.rclone_utils_amazon_for_testing import AwsCredentials, AwsS3
from submitr.rclone.testing.rclone_utils_google_for_testing import Gcs

# Integration tests for RClone related functionality within smaht-submitr.
# Need valid AWS credentials for (currently) smaht-wolf.
# Need valid Google Cloud credentials for (currently) project smaht-dac.
# Wonder how to possibly test this as unit test within GA?


class AmazonTestEnv:

    # Specifying the env name here (as smaht-wolf) will cause
    # AwsCredentials to read from: ~/.aws_test.smaht-wolf/credentials
    # In addition to the basic credentials (access_key_id, secret_access_key,
    # optional session_token), this is also assumed to also contain the region.
    # For the kms_key_id see ENCODED_S3_ENCRYPT_KEY_ID in AWS C4AppConfigSmahtWolf Secrets.
    env = "smaht-wolf"
    kms_key_id = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"
    bucket = "smaht-unit-testing-files"

    @staticmethod
    def credentials(nokms: bool = False) -> AmazonCredentials:
        kms_key_id = None if nokms is True else AmazonTestEnv.kms_key_id
        credentials = AwsCredentials.get_credentials_from_file(AmazonTestEnv.env, kms_key_id=kms_key_id)
        assert isinstance(credentials.region, str) and credentials.region
        assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
        assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key
        assert credentials.kms_key_id == (None if nokms is True else AmazonTestEnv.kms_key_id)
        return credentials

    @staticmethod
    def credentials_nokms() -> AmazonCredentials:
        return AmazonTestEnv.credentials(nokms=True)

    @staticmethod
    def temporary_credentials(nokms: bool = False,
                              bucket: Optional[str] = None, key: Optional[str] = None) -> AmazonCredentials:
        credentials = AmazonTestEnv.credentials(nokms=nokms)
        s3 = AwsS3(credentials)
        temporary_credentials = s3.generate_temporary_credentials(bucket=bucket, key=key)
        assert isinstance(temporary_credentials.session_token, str) and temporary_credentials.session_token
        assert temporary_credentials.kms_key_id == (None if nokms is True else AmazonTestEnv.kms_key_id)
        return temporary_credentials

    @staticmethod
    def temporary_credentials_nokms(bucket: Optional[str] = None, key: Optional[str] = None) -> AmazonCredentials:
        return AmazonTestEnv.temporary_credentials(nokms=True, bucket=bucket, key=key)


class GoogleTestEnv:

    # The Google test account project is: smaht-dac
    location = "us-east1"
    service_account_file = "/Users/dmichaels/.config/google-cloud/smaht-dac-617e0480d8e2.json"
    bucket = "smaht-submitr-rclone-testing"

    @staticmethod
    def credentials() -> GoogleCredentials:
        credentials = GoogleCredentials(location=GoogleTestEnv.location,
                                        service_account_file=GoogleTestEnv.service_account_file)
        assert credentials.location == GoogleTestEnv.location
        assert credentials.service_account_file == GoogleTestEnv.service_account_file
        assert os.path.isfile(credentials.service_account_file)
        return credentials


TEMPORARY_TEST_FILE_PREFIX = "test-submitr-rclone-"
TEMPORARY_TEST_FILE_SUFFIX = ".txt"


def initial_setup_and_sanity_checking() -> None:

    AwsCredentials.remove_credentials_from_environment_variables()
    assert os.environ.get("AWS_DEFAULT_REGION", None) is None
    assert os.environ.get("AWS_ACCESS_KEY_ID", None) is None
    assert os.environ.get("AWS_SECRET_ACCESS_KEY", None) is None
    assert os.environ.get("AWS_SESSION_TOKEN", None) is None

    credentials_amazon = AmazonTestEnv.credentials()
    s3 = AwsS3(credentials_amazon)
    assert s3.bucket_exists(AmazonTestEnv.bucket) is True

    credentials_google = GoogleTestEnv.credentials()
    assert os.path.isfile(credentials_google.service_account_file)
    gcs = Gcs(credentials_google)
    assert gcs.bucket_exists(GoogleTestEnv.bucket) is True


def create_rclone_config_amazon(credentials: AmazonCredentials) -> RCloneConfig:
    config = RCloneConfigAmazon(credentials)
    assert config.credentials == credentials
    assert config.access_key_id == credentials.access_key_id
    assert config.secret_access_key == credentials.secret_access_key
    assert config.session_token == credentials.session_token
    assert config.kms_key_id == credentials.kms_key_id
    return config


def create_rclone_config_google(credentials: AmazonCredentials) -> RCloneConfig:
    config = RCloneConfigGoogle(credentials)
    assert config.credentials == credentials
    assert config.location == credentials.location
    assert config.service_account_file == credentials.service_account_file
    return config


def create_rclone(source: Optional[RCloneConfig] = None, destination: Optional[RCloneConfig] = None) -> RClone:
    rclone = RClone(source=source, destination=destination)
    assert rclone.source == source
    assert rclone.destination == destination
    return rclone


def sanity_check_amazon_file(credentials: AmazonCredentials, bucket: str, key: str, file: str) -> None:
    s3 = AwsS3(credentials)
    assert s3.credentials == credentials
    assert s3.file_exists(bucket, key) is True
    assert s3.file_equals(bucket, key, file) is True
    if kms_key_id := s3.credentials.kms_key_id:
        assert s3.file_kms_encrypted(bucket, key) is True
        assert s3.file_kms_encrypted(bucket, key, kms_key_id) is True


def sanity_check_google_file(credentials: GoogleCredentials, bucket: str, key: str, file: str) -> None:
    gcs = Gcs(credentials)
    assert gcs.credentials == credentials
    assert gcs.file_exists(bucket, key) is True
    assert gcs.file_equals(bucket, key, file) is True


def cleanup_amazon_file(credentials: AmazonCredentials, bucket: str, key: str) -> None:
    s3 = AwsS3(credentials)
    assert s3.credentials == credentials
    assert s3.delete_file(bucket, key) is True
    assert s3.file_exists(bucket, key) is False


def cleanup_google_file(credentials: GoogleCredentials, bucket: str, key: str) -> None:
    gcs = Gcs(credentials)
    assert gcs.credentials == credentials
    assert gcs.delete_file(bucket, key) is True
    assert gcs.file_exists(bucket, key) is False


@contextmanager
def temporary_test_file() -> Tuple[str, str]:
    with temporary_random_file(prefix=TEMPORARY_TEST_FILE_PREFIX, suffix=TEMPORARY_TEST_FILE_SUFFIX) as tmp_file_path:
        yield tmp_file_path, os.path.basename(tmp_file_path)


def test_utils_for_testing() -> None:

    # First of all, test the test code, i.e. the Amazon/Google code which uploads,
    # downloads, verifies, et cetera - WITHOUT using RClone - in furtherance of the
    # testing of the various RClone features.

    credentials = AmazonTestEnv.credentials()
    _test_utils_for_testing(credentials)

    temporary_credentials = AmazonTestEnv.temporary_credentials()
    _test_utils_for_testing(temporary_credentials)


def _test_utils_for_testing(credentials: AmazonCredentials) -> None:

    assert isinstance(credentials, AmazonCredentials)
    assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
    assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key

    s3 = AwsS3(credentials)
    assert s3.credentials == credentials

    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = tmp_test_file_name
        assert s3.upload_file(tmp_test_file_path, AmazonTestEnv.bucket) is True
        assert s3.file_exists(AmazonTestEnv.bucket, key) is True
        assert s3.file_equals(AmazonTestEnv.bucket, key, tmp_test_file_path) is True
        assert s3.file_exists(AmazonTestEnv.bucket, key + "-junk-suffix") is False
        assert len(s3_test_files := s3.list_files(AmazonTestEnv.bucket, prefix=TEMPORARY_TEST_FILE_PREFIX)) > 0
        assert len(s3_test_files_found := [f for f in s3_test_files if f["key"] == key]) == 1
        assert s3_test_files_found[0]["key"] == key
        assert len(s3.list_files(AmazonTestEnv.bucket, prefix=key)) == 1
        with temporary_random_file() as some_random_file_path:
            assert s3.file_equals(AmazonTestEnv.bucket, key, some_random_file_path) is False
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(AmazonTestEnv.bucket, key, tmp_downloaded_file_path) is True
            assert s3.download_file(AmazonTestEnv.bucket, key, "/dev/null") is True
            assert are_files_equal(tmp_test_file_path, tmp_downloaded_file_path) is True
            assert are_files_equal(tmp_test_file_path, "/dev/null") is False
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(AmazonTestEnv.bucket, key, tmp_download_directory) is True
            assert are_files_equal(tmp_test_file_path, f"{tmp_download_directory}/{key}") is True
        assert s3.delete_file(AmazonTestEnv.bucket, key) is True
        assert s3.file_exists(AmazonTestEnv.bucket, key) is False
        assert s3.file_equals(AmazonTestEnv.bucket, key, "/dev/null") is False
        assert s3.download_file(AmazonTestEnv.bucket, key, "/dev/null") is False


def test_rclone_between_amazon_and_local() -> None:

    _test_rclone_between_amazon_and_local(AmazonTestEnv.credentials)
    _test_rclone_between_amazon_and_local(AmazonTestEnv.credentials_nokms)

    _test_rclone_between_amazon_and_local(AmazonTestEnv.temporary_credentials)
    _test_rclone_between_amazon_and_local(AmazonTestEnv.temporary_credentials_nokms)

    _test_rclone_between_amazon_and_local(AmazonTestEnv.temporary_credentials, use_key_specific_credentials=True)
    _test_rclone_between_amazon_and_local(AmazonTestEnv.temporary_credentials_nokms, use_key_specific_credentials=True)


def _test_rclone_between_amazon_and_local(credentials: Union[Callable, AmazonCredentials],
                                          use_key_specific_credentials: bool = False) -> None:

    if isinstance(credentials, AmazonCredentials):
        credentials = lambda: credentials  # noqa
    elif not callable(credentials):
        assert False

    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = tmp_test_file_name
        # Here we have a local test file to upload to AWS S3.
        if use_key_specific_credentials is True:
            credentials = credentials(bucket=AmazonTestEnv.bucket, key=key)
        else:
            credentials = credentials()
        config = create_rclone_config_amazon(credentials)
        # Upload the local test file to AWS S3 using RClone;
        # we upload tmp_test_file_path to the key (tmp_test_file_name) key in AmazonTestEnv.bucket.
        rclone = create_rclone(destination=config)
        assert rclone.copy(tmp_test_file_path, AmazonTestEnv.bucket) is True  # TODO: maybe also to specify key?
        # Sanity check the uploaded file using non-RClone methods (via AwS3 which uses boto3).
        sanity_check_amazon_file(credentials, AmazonTestEnv.bucket, key, tmp_test_file_path)
        # Now try to download the test file (which was uploaded above to AWS S3 using RClone) to the local
        # file system; use the same RClone configuration as for upload but as the source rather than destination.
        # TODO
        rclone = create_rclone(source=config)
        with temporary_directory() as tmp_download_directory:
            assert tmp_download_directory is not None  # TODO/placeholder
            # TODO TODO
            # import pdb ; pdb.set_trace()
            # rclone.copy(AmazonTestEnv.bucket, key, tmp_download_directory)
            pass
        # Cleanup (delete) the test file in AWS S3.
        cleanup_amazon_file(credentials, AmazonTestEnv.bucket, key)


def test_rclone_between_google_and_local() -> None:
    credentials = GoogleTestEnv.credentials()
    config = create_rclone_config_google(credentials)
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = tmp_test_file_name
        # Here we have a local test file to upload to Google Cloud Storage.
        rclone = create_rclone(destination=config)
        # Upload the local test file to Google Cloud Storage using RClone; we upload
        # tmp_test_file_path to the key (tmp_test_file_name) key in GoogleTestEnv.bucket.
        rclone.copy(tmp_test_file_path, GoogleTestEnv.bucket)
        # Sanity check the uploaded file using non-RClone methods (via Gcs which uses google.cloud.storage).
        sanity_check_google_file(credentials, GoogleTestEnv.bucket, key, tmp_test_file_path)
        # Now try to download the uploaded test file in Google Cloud Storage using RClone;
        # use the same RClone configuration as for upload but as the source rather than destination.
        rclone = create_rclone(source=config)
        with temporary_directory() as tmp_download_directory:
            assert tmp_download_directory  # TODO/placeholder
            # TODO
            # import pdb ; pdb.set_trace()
            # rclone.copy(GoogleTestEnv.bucket, key, tmp_download_directory)
            pass
        # Cleanup (delete) the test file in Google Cloud Storage.
        cleanup_google_file(credentials, GoogleTestEnv.bucket, key)


def test_rclone_google_to_amazon() -> None:
    credentials_google = GoogleTestEnv.credentials()
    credentials_amazon = AmazonTestEnv.credentials()
    rclone_config_google = create_rclone_config_google(credentials_google)
    rclone_config_amazon = create_rclone_config_amazon(credentials_amazon)
    # First upload a test file to Google Cloud Storage.
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = tmp_test_file_name
        # Here we have a local test file to upload to Google Cloud Storage;
        # which we will then copy directly to AWS S3 via RClone.
        # So first upload our local test file to Google Cloud Storage (via RClone - why not).
        rclone = create_rclone(destination=rclone_config_google)
        rclone.copy(tmp_test_file_path, GoogleTestEnv.bucket)
        # Make sure it made it there.
        sanity_check_google_file(credentials_google, GoogleTestEnv.bucket, key, tmp_test_file_path)
        # Now try to copy directly from Google Cloud Storage to AWS S3 (THIS is really the MAIN event).
        rclone = create_rclone(source=rclone_config_google, destination=rclone_config_amazon)
        rclone.copy(rclone.join_cloud_path(GoogleTestEnv.bucket, key), AmazonTestEnv.bucket)
        # Sanity check the file in AWS S3 which was copied directly from Google Cloud Storage.
        sanity_check_amazon_file(credentials_amazon, AmazonTestEnv.bucket, key, tmp_test_file_path)
        # Cleanup (delete) the test file in Google Cloud Storage.
        cleanup_google_file(credentials_google, GoogleTestEnv.bucket, key)
        # Cleanup (delete) the test file in AWS S3.
        cleanup_amazon_file(credentials_amazon, AmazonTestEnv.bucket, key)


def test_rclone_amazon_to_google() -> None:
    credentials_amazon = AmazonTestEnv.credentials()
    credentials_google = GoogleTestEnv.credentials()
    rclone_config_amazon = create_rclone_config_amazon(credentials_amazon)
    rclone_config_google = create_rclone_config_google(credentials_google)
    pass  # TODO
    # First upload a test file to AWS S3.
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        key = tmp_test_file_name
        # Here we have a local test file to upload to AWS S3;
        # which we will then copy directly to Google Cloud Storage via RClone.
        # So first upload our local test file to AWS S3 (via RClone - why not).
        rclone = create_rclone(destination=rclone_config_amazon)
        rclone.copy(tmp_test_file_path, AmazonTestEnv.bucket)
        # Make sure it made it there.
        sanity_check_amazon_file(credentials_amazon, AmazonTestEnv.bucket, key, tmp_test_file_path)
        # Now try to copy directly from AWS S3 to Google Cloud Storage.
        # import pdb ; pdb.set_trace()
        rclone = create_rclone(source=rclone_config_amazon, destination=rclone_config_google)
        rclone.copy(rclone.join_cloud_path(AmazonTestEnv.bucket, key), GoogleTestEnv.bucket)
        # Sanity check the file in Google Cloud Storage which was copied directly from AWS S3.
        sanity_check_google_file(credentials_google, GoogleTestEnv.bucket, key, tmp_test_file_path)
        # Cleanup (delete) the test file in AWS S3.
        cleanup_amazon_file(credentials_amazon, AmazonTestEnv.bucket, key)
        # Cleanup (delete) the test file in Google Cloud Storage.
        cleanup_google_file(credentials_google, GoogleTestEnv.bucket, key)


def test():
    initial_setup_and_sanity_checking()
    test_utils_for_testing()
    test_rclone_between_amazon_and_local()
    test_rclone_between_google_and_local()
    test_rclone_google_to_amazon()
    test_rclone_amazon_to_google()


test()
