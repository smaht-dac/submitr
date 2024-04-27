import os
import time
from dcicutils.file_utils import are_files_equal
from dcicutils.tmpfile_utils import (
    temporary_directory,
    temporary_file,
    temporary_random_file
)
from submitr.rclone.rclone_utils_for_testing import AwsCredentials, AwsS3


class SmahtWolf:
    # Specifying the env name here (as smaht-wolf) will cause
    # AwsCredentials to read from: ~/.aws_test.smaht-wolf/credentials
    env = "smaht-wolf"
    kms_key_id = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"
    bucket = "smaht-unit-testing-files"
    credentials_with_kms = lambda: AwsCredentials(SmahtWolf.env, kms_key_id=SmahtWolf.kms_key_id)  # noqa
    credentials_sans_kms = lambda: AwsCredentials(SmahtWolf.env)  # noqa
    credentials = credentials_with_kms


Env = SmahtWolf


def test_rclone_utils_for_testing():

    credentials = Env.credentials()
    bucket = Env.bucket

    temporary_session_credentials = credentials.generate_temporary_credentials()
    temporary_session_credentials = credentials  # TODO - permission issue wrt kms
    s3 = AwsS3(temporary_session_credentials)

    with temporary_random_file(prefix="test-submitr-rclone-", suffix=".txt") as tmp_source_file_path:
        tmp_source_file_name = os.path.basename(tmp_source_file_path)  # key name within bucket 
        assert s3.upload_file(tmp_source_file_path, bucket) is True
        assert s3.file_exists(bucket, tmp_source_file_name) is True
        assert s3.file_equals(bucket, tmp_source_file_name, tmp_source_file_path) is True
        with temporary_file() as tmp_downloaded_file_path:
            assert s3.download_file(bucket, tmp_source_file_name, tmp_downloaded_file_path) is True
            assert s3.download_file(bucket, tmp_source_file_name, "/dev/null") is True
            assert are_files_equal(tmp_source_file_path, tmp_downloaded_file_path) is True
        with temporary_directory() as tmp_download_directory:
            assert s3.download_file(bucket, tmp_source_file_name, tmp_download_directory) is True
            assert are_files_equal(tmp_source_file_path, f"{tmp_download_directory}/{tmp_source_file_name}") is True
        assert s3.delete_file(bucket, tmp_source_file_name) is True
        assert s3.file_exists(bucket, tmp_source_file_name) is False
        assert s3.download_file(bucket, tmp_source_file_name, "/dev/null") is False


test_rclone_utils_for_testing()
