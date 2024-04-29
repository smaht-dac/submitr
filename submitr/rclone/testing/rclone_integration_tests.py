from contextlib import contextmanager
import os
from typing import Tuple
from dcicutils.file_utils import are_files_equal
from dcicutils.tmpfile_utils import temporary_directory, temporary_file, temporary_random_file
from submitr.rclone.rclone import RClone
from submitr.rclone.rclone_config_amazon import AmazonCredentials, RCloneConfigAmazon
from submitr.rclone.rclone_config_google import GoogleCredentials, RCloneConfigGoogle
from submitr.rclone.testing.rclone_utils_amazon_for_testing import AwsCredentials, AwsS3
from submitr.rclone.testing.rclone_utils_google_for_testing import Gcs

# Integration tests for rclone related functionality within smaht-submitr.
# Need valid AWS credentials for (currently) smaht-wolf.
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
    def credentials() -> AmazonCredentials:
        credentials = AwsCredentials.get_credentials_from_file(AmazonTestEnv.env, kms_key_id=AmazonTestEnv.kms_key_id)
        assert credentials.region
        return credentials


class GoogleTestEnv:

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


@contextmanager
def temporary_test_file() -> Tuple[str, str]:
    with temporary_random_file(prefix=TEMPORARY_TEST_FILE_PREFIX, suffix=TEMPORARY_TEST_FILE_SUFFIX) as tmp_file_path:
        yield tmp_file_path, os.path.basename(tmp_file_path)


def test_utils_for_testing() -> None:

    credentials = AmazonTestEnv.credentials()
    _test_utils_for_testing(credentials)

    temporary_credentials = AwsS3(credentials).generate_temporary_credentials()
    assert isinstance(temporary_credentials.session_token, str) and temporary_credentials.session_token
    _test_utils_for_testing(temporary_credentials)


def _test_utils_for_testing(credentials: AmazonCredentials) -> None:

    assert isinstance(credentials, AmazonCredentials)
    assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
    assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key

    s3 = AwsS3(credentials)
    assert s3.credentials == credentials

    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        assert s3.upload_file(tmp_test_file_path, AmazonTestEnv.bucket) is True
        assert s3.file_exists(AmazonTestEnv.bucket, tmp_test_file_name) is True
        assert s3.file_equals(AmazonTestEnv.bucket, tmp_test_file_name, tmp_test_file_path) is True
        assert s3.file_exists(AmazonTestEnv.bucket, tmp_test_file_name + "-junk-suffix") is False
        assert len(s3_test_files := s3.list_files(AmazonTestEnv.bucket, prefix=TEMPORARY_TEST_FILE_PREFIX)) > 0
        assert len(s3_test_files_found := [f for f in s3_test_files if f["key"] == tmp_test_file_name]) == 1
        assert s3_test_files_found[0]["key"] == tmp_test_file_name
        assert len(s3.list_files(AmazonTestEnv.bucket, prefix=tmp_test_file_name)) == 1
        with temporary_random_file() as some_random_file_path:
            assert s3.file_equals(AmazonTestEnv.bucket, tmp_test_file_name, some_random_file_path) is False
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(AmazonTestEnv.bucket, tmp_test_file_name, tmp_downloaded_file_path) is True
            assert s3.download_file(AmazonTestEnv.bucket, tmp_test_file_name, "/dev/null") is True
            assert are_files_equal(tmp_test_file_path, tmp_downloaded_file_path) is True
            assert are_files_equal(tmp_test_file_path, "/dev/null") is False
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(AmazonTestEnv.bucket, tmp_test_file_name, tmp_download_directory) is True
            assert are_files_equal(tmp_test_file_path, f"{tmp_download_directory}/{tmp_test_file_name}") is True
        assert s3.delete_file(AmazonTestEnv.bucket, tmp_test_file_name) is True
        assert s3.file_exists(AmazonTestEnv.bucket, tmp_test_file_name) is False
        assert s3.file_equals(AmazonTestEnv.bucket, tmp_test_file_name, "/dev/null") is False
        assert s3.download_file(AmazonTestEnv.bucket, tmp_test_file_name, "/dev/null") is False


def test_between_amazon_and_local() -> None:

    _test_between_amazon_and_local(AmazonTestEnv.credentials())
    _test_between_amazon_and_local(AmazonTestEnv.credentials(), nokms=True)

    _test_between_amazon_and_local(AmazonTestEnv.credentials(), use_temporary_credentials=True)
    _test_between_amazon_and_local(AmazonTestEnv.credentials(), use_temporary_credentials=True, nokms=True)

    _test_between_amazon_and_local(AmazonTestEnv.credentials(), use_temporary_credentials_key_specific=True)
    _test_between_amazon_and_local(AmazonTestEnv.credentials(), use_temporary_credentials_key_specific=True, nokms=True)


def _test_between_amazon_and_local(credentials: AmazonCredentials,
                                   use_temporary_credentials: bool = False,
                                   use_temporary_credentials_key_specific: bool = False,
                                   nokms: bool = False) -> None:

    if nokms is True:
        credentials = AmazonCredentials(credentials)
        credentials.kms_key_id = None
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        # Here we have a local test file to upload to AWS S3.
        if use_temporary_credentials_key_specific is True:
            credentials = AwsS3(credentials).generate_temporary_credentials(bucket=AmazonTestEnv.bucket,
                                                                            key=tmp_test_file_name)
            assert isinstance(credentials.session_token, str) and credentials.session_token
        elif use_temporary_credentials is True:
            credentials = AwsS3(credentials).generate_temporary_credentials()
            assert isinstance(credentials.session_token, str) and credentials.session_token
        config = RCloneConfigAmazon(credentials)
        assert config.credentials == credentials
        assert config.access_key_id == credentials.access_key_id
        assert config.secret_access_key == credentials.secret_access_key
        assert config.session_token == credentials.session_token
        assert config.kms_key_id == credentials.kms_key_id
        # Upload the local test file to AWS S3 using RClone;
        # we upload tmp_test_file_path to the tmp_test_file_name key in AmazonTestEnv.bucket.
        rclone = RClone(destination=config)
        assert rclone.destination == config
        assert rclone.copy(tmp_test_file_path, AmazonTestEnv.bucket) is True  # TODO: maybe also to specify key?
        # Sanity check uploaded file using non-RClone methods (via Aws3 which uses boto3).
        s3 = AwsS3(credentials)
        assert s3.file_exists(AmazonTestEnv.bucket, tmp_test_file_name) is True
        assert s3.file_equals(AmazonTestEnv.bucket, tmp_test_file_name, tmp_test_file_path) is True
        if config.kms_key_id:
            assert s3.file_kms_encrypted(AmazonTestEnv.bucket, tmp_test_file_name) is True
            assert s3.file_kms_encrypted(AmazonTestEnv.bucket, tmp_test_file_name, config.kms_key_id) is True
        # Now try to download the uploaded test file in AWS S3 using RClone;
        # use the same RClone configuration as for upload but as the source rather than destination.
        # TODO
        rclone = RClone(source=config)
        assert rclone.source == config
        with temporary_directory() as tmp_download_directory:
            assert tmp_download_directory is not None  # TODO/placeholder
            # TODO TODO
            # import pdb
            # pdb.set_trace()
            # rclone.copy(AmazonTestEnv.bucket, tmp_test_file_name, tmp_download_directory)
            pass
        # Cleanup (delete) the test file in AWS S3.
        assert s3.delete_file(AmazonTestEnv.bucket, tmp_test_file_name) is True
        assert s3.file_exists(AmazonTestEnv.bucket, tmp_test_file_name) is False


def test_between_google_and_local() -> None:
    credentials = GoogleTestEnv.credentials()
    config = RCloneConfigGoogle(credentials)
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        # Here we have a local test file to upload to Google Cloud Storage.
        rclone = RClone(destination=config)
        # Upload the local test file to Google Cloud Storage using rclone;
        # we upload tmp_test_file_path to the tmp_test_file_name key in GoogleTestEnv.bucket.
        rclone.copy(tmp_test_file_path, GoogleTestEnv.bucket)
        # Sanity check uploaded file using non-RClone methods (via Gcs which uses google.cloud.storage).
        gcs = Gcs(credentials)
        assert gcs.file_exists(GoogleTestEnv.bucket, tmp_test_file_name) is True
        assert gcs.file_equals(GoogleTestEnv.bucket, tmp_test_file_name, tmp_test_file_path) is True
        # Now try to download the uploaded test file in Google Cloud Storage using RClone;
        # use the same RClone configuration as for upload but as the source rather than destination.
        rclone = RClone(source=config)
        assert rclone.source == config
        with temporary_directory() as tmp_download_directory:
            assert tmp_download_directory  # TODO/placeholder
            # TODO
            # import pdb ; pdb.set_trace()
            # rclone.copy(GoogleTestEnv.bucket, tmp_test_file_name, tmp_download_directory)
            pass
        # Cleanup (delete) the test file in Google Cloud Storage.
        assert gcs.delete_file(GoogleTestEnv.bucket, tmp_test_file_name) is True
        assert gcs.file_exists(GoogleTestEnv.bucket, tmp_test_file_name) is False


def test_google_to_amazon() -> None:
    google_credentials = GoogleTestEnv.credentials()
    amazon_credentials = AmazonTestEnv.credentials()
    google_config = RCloneConfigGoogle(google_credentials)
    amazon_config = RCloneConfigAmazon(amazon_credentials)
    # First upload a test file to Google Cloud Storage.
    with temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        # Here we have a local test file to upload to Google Cloud Storage.
        rclone = RClone(destination=google_config)
        rclone.copy(tmp_test_file_path, GoogleTestEnv.bucket)
        # Make sure it made it there.
        gcs = Gcs(google_credentials)
        assert gcs.file_exists(GoogleTestEnv.bucket, tmp_test_file_name) is True
        assert gcs.file_equals(GoogleTestEnv.bucket, tmp_test_file_name, tmp_test_file_path) is True
        # Now try to copy directly from Google Cloud Storage to AWS S3 (THIS is really the MAIN event).
        rclone = RClone(source=google_config, destination=amazon_config)
        rclone.copy(rclone.join_cloud_path(GoogleTestEnv.bucket, tmp_test_file_name), AmazonTestEnv.bucket)
        # TODO
        # Cleanup (delete) the test file in Google Cloud Storage.
        assert gcs.delete_file(GoogleTestEnv.bucket, tmp_test_file_name) is True
        assert gcs.file_exists(GoogleTestEnv.bucket, tmp_test_file_name) is False
        # Cleanup (delete) the test file in AWS S3.
        s3 = AwsS3(amazon_credentials)
        assert s3.delete_file(AmazonTestEnv.bucket, tmp_test_file_name) is True


def test_amazon_to_google() -> None:
    pass  # TODO


def test():
    AwsCredentials.remove_credentials_from_environment_variables()
    test_utils_for_testing()
    test_between_amazon_and_local()
    test_between_google_and_local()
    test_google_to_amazon()


test()
