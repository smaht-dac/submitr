from contextlib import contextmanager
import os
from dcicutils.file_utils import are_files_equal
from dcicutils.tmpfile_utils import (
    temporary_directory,
    temporary_file,
    temporary_random_file
)
from submitr.rclone.rclone import RClone
from submitr.rclone.rclone_config_amazon import AmazonCredentials, RCloneConfigAmazon
from submitr.rclone.tests.rclone_utils_for_testing import AwsCredentials, AwsS3

# Integration tests for rclone related functionality within smaht-submitr.
# Need valid AWS credentials for (currently) smaht-wolf.
# Wonder how to possibly test this as unit test within GA?


class SmahtWolf:
    # Specifying the env name here (as smaht-wolf) will cause
    # AwsCredentials to read from: ~/.aws_test.smaht-wolf/credentials
    env = "smaht-wolf"
    # See ENCODED_S3_ENCRYPT_KEY_ID in SecretsManager for C4AppConfigSmahtWolf.
    kms_key_id = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"
    bucket = "smaht-unit-testing-files"
    temporary_test_file_prefix = "test-submitr-rclone-"
    temporary_test_file_suffix = ".txt"

    @staticmethod
    def credentials_with_kms():
        return AwsCredentials(SmahtWolf.env, kms_key_id=SmahtWolf.kms_key_id)

    @staticmethod
    def credentials_sans_kms():
        return AwsCredentials(SmahtWolf.env)

    @staticmethod
    def credentials():
        return SmahtWolf.credentials_with_kms()

    @staticmethod
    @contextmanager
    def temporary_test_file():
        with temporary_random_file(prefix=ENV.temporary_test_file_prefix,
                                   suffix=ENV.temporary_test_file_suffix) as tmp_file_path:
            yield tmp_file_path, os.path.basename(tmp_file_path)


ENV = SmahtWolf


def test_rclone_utils_for_testing():

    credentials = ENV.credentials()
    _test_rclone_utils_for_testing(credentials)

    temporary_credentials = AwsS3(credentials).generate_temporary_credentials()
    assert isinstance(temporary_credentials.session_token, str) and temporary_credentials.session_token
    _test_rclone_utils_for_testing(temporary_credentials)


def _test_rclone_utils_for_testing(credentials):

    assert isinstance(credentials, AwsCredentials)
    assert isinstance(credentials.access_key_id, str) and credentials.access_key_id
    assert isinstance(credentials.secret_access_key, str) and credentials.secret_access_key

    s3 = AwsS3(credentials)
    assert s3.credentials == credentials

    with ENV.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        assert s3.upload_file(tmp_test_file_path, ENV.bucket) is True
        assert s3.file_exists(ENV.bucket, tmp_test_file_name) is True
        assert s3.file_equals(ENV.bucket, tmp_test_file_name, tmp_test_file_path) is True
        assert s3.file_exists(ENV.bucket, tmp_test_file_name + "-junk-suffix") is False
        assert len(s3_test_files := s3.list_files(ENV.bucket, prefix=ENV.temporary_test_file_prefix)) > 0
        assert len(s3_test_files_found := [f for f in s3_test_files if f["key"] == tmp_test_file_name]) == 1
        assert s3_test_files_found[0]["key"] == tmp_test_file_name
        assert len(s3.list_files(ENV.bucket, prefix=tmp_test_file_name)) == 1
        with temporary_random_file() as some_random_file_path:
            assert s3.file_equals(ENV.bucket, tmp_test_file_name, some_random_file_path) is False
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(ENV.bucket, tmp_test_file_name, tmp_downloaded_file_path) is True
            assert s3.download_file(ENV.bucket, tmp_test_file_name, "/dev/null") is True
            assert are_files_equal(tmp_test_file_path, tmp_downloaded_file_path) is True
            assert are_files_equal(tmp_test_file_path, "/dev/null") is False
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(ENV.bucket, tmp_test_file_name, tmp_download_directory) is True
            assert are_files_equal(tmp_test_file_path, f"{tmp_download_directory}/{tmp_test_file_name}") is True
        assert s3.delete_file(ENV.bucket, tmp_test_file_name) is True
        assert s3.file_exists(ENV.bucket, tmp_test_file_name) is False
        assert s3.file_equals(ENV.bucket, tmp_test_file_name, "/dev/null") is False
        assert s3.download_file(ENV.bucket, tmp_test_file_name, "/dev/null") is False


def test_rclone_local_to_amazon():

    _test_rclone_local_to_amazon(ENV.credentials())
    _test_rclone_local_to_amazon(ENV.credentials(), nokms=True)

    _test_rclone_local_to_amazon(ENV.credentials(), use_temporary_credentials=True)
    _test_rclone_local_to_amazon(ENV.credentials(), use_temporary_credentials=True, nokms=True)

    _test_rclone_local_to_amazon(ENV.credentials(), use_temporary_credentials_key_specific=True)
    _test_rclone_local_to_amazon(ENV.credentials(), use_temporary_credentials_key_specific=True, nokms=True)


def _test_rclone_local_to_amazon(credentials: AmazonCredentials,
                                 use_temporary_credentials: bool = False,
                                 use_temporary_credentials_key_specific: bool = False,
                                 nokms: bool = False) -> None:

    if nokms is True:
        credentials = AmazonCredentials(credentials, nokms=True)
    with ENV.temporary_test_file() as (tmp_test_file_path, tmp_test_file_name):
        if use_temporary_credentials_key_specific is True:
            credentials = AwsS3(credentials).generate_temporary_credentials(bucket=ENV.bucket,
                                                                            key=tmp_test_file_name, nokms=nokms)
            assert isinstance(credentials.session_token, str) and credentials.session_token
        elif use_temporary_credentials is True:
            credentials = AwsS3(credentials).generate_temporary_credentials(nokms=nokms)
            assert isinstance(credentials.session_token, str) and credentials.session_token
        config = RCloneConfigAmazon(credentials, nokms=nokms)
        assert config.credentials == credentials
        assert config.access_key_id == credentials.access_key_id
        assert config.secret_access_key == credentials.secret_access_key
        assert config.session_token == credentials.session_token
        assert config.kms_key_id == credentials.kms_key_id
        rclone = RClone(destination=config)
        assert rclone.copy(tmp_test_file_path, ENV.bucket) is True
        s3 = AwsS3(credentials)
        assert s3.file_exists(ENV.bucket, tmp_test_file_name) is True
        assert s3.file_equals(ENV.bucket, tmp_test_file_name, tmp_test_file_path) is True
        if config.kms_key_id:
            assert s3.file_kms_encrypted(ENV.bucket, tmp_test_file_name) is True
            assert s3.file_kms_encrypted(ENV.bucket, tmp_test_file_name, config.kms_key_id) is True
        assert s3.delete_file(ENV.bucket, tmp_test_file_name) is True
        assert s3.file_exists(ENV.bucket, tmp_test_file_name) is False


# Manually run ...
test_rclone_utils_for_testing()
test_rclone_local_to_amazon()
