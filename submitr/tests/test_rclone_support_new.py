from contextlib import contextmanager
import os
import pytest
from typing import Optional
from dcicutils.file_utils import compute_file_md5 as get_file_checksum, get_file_size
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import (
    temporary_directory, temporary_random_file)
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.rcloner import RCloner
from submitr.rclone.rclone_amazon import RCloneAmazon
from submitr.rclone.rclone_utils import cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsS3


# This integration test actually talks to AWS S3 and Google Cloud Storage (GCS);
# both directly (via Python boto3 and google.cloud.storage) and via rclone.
# The access credentials are defined by the variables as described below.
# See testing_rclone_config for configuration parameters and comments.

from submitr.tests.testing_rclone_config import (  # noqa

    rclone_config_setup_module,
    rclone_config_teardown_module,

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
    rclone_config_setup_module()


def teardown_module():
    rclone_config_teardown_module()


class Amazon:

    @staticmethod
    def credentials(nokms: bool = False) -> AmazonCredentials:
        return AmazonCredentials(amazon_credentials_file_path(),
                                 kms_key_id=None if nokms is True else AMAZON_KMS_KEY_ID)

    @staticmethod
    def s3(nokms: bool = False) -> AmazonCredentials:
        return AwsS3(Amazon.credentials(nokms=nokms))

    @staticmethod
    @contextmanager
    def temporary_cloud_file(nosubfolder: bool = False, nokms: bool = False, size: Optional[int] = None) -> str:

        global AMAZON_TEST_BUCKET_NAME, TEST_FILE_PREFIX, TEST_FILE_SUFFIX, TEST_FILE_SIZE

        assert nosubfolder in (True, False)
        assert nokms in (True, False)
        assert isinstance(bucket := AMAZON_TEST_BUCKET_NAME, str) and bucket
        if size is None: size = TEST_FILE_SIZE  # noqa
        assert isinstance(size, int) and (size >= 0)

        key = f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}"
        if nosubfolder is False:
            subfolder = f"{TEST_FILE_PREFIX}{create_uuid()}"
            key = cloud_path.join(subfolder, key)

        s3 = Amazon.s3(nokms=nokms)
        try:
            with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=size) as tmp_file_path:
                assert s3.upload_file(tmp_file_path, bucket, key) is True
                assert s3.file_exists(bucket, key) is True
                assert s3.file_size(bucket, key) == size
                if nokms is False:
                    assert s3.file_kms_encrypted(bucket, key, AMAZON_KMS_KEY_ID) is True
                yield cloud_path.join(bucket, key)
        except Exception:
            pytest.fail("Cannot create (non-rclone) AWS S3 object!")
            return None
        finally:
            s3.delete_file(bucket, key)


def test_new() -> None:
    nokms = True
    with Amazon.temporary_cloud_file(nokms=nokms) as amazon_cloud_path:
        with temporary_directory() as tmpdir:
            amazon_credentials = Amazon.credentials(nokms=nokms)
            amazon = RCloneAmazon(amazon_credentials)
            RCloner(source=amazon).copy(amazon_cloud_path, tmpdir)
            local_file_path = os.path.join(tmpdir, cloud_path.basename(amazon_cloud_path))
            assert os.path.isfile(local_file_path)
            assert get_file_size(local_file_path) == amazon.file_size(amazon_cloud_path)
            assert get_file_checksum(local_file_path) == amazon.file_checksum(amazon_cloud_path)
        pass
    pass
