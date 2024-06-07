from contextlib import contextmanager
import pytest
from typing import Optional
from dcicutils.misc_utils import create_uuid
from dcicutils.tmpfile_utils import temporary_random_file
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.google_credentials import GoogleCredentials
from submitr.rclone.rclone_utils import cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsS3
from submitr.rclone.testing.rclone_utils_for_testing_google import Gcs
from submitr.tests.integration.testing_rclone_setup import (  # noqa

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


class Amazon:

    @classmethod
    @property
    def bucket(cls) -> str:
        global AMAZON_TEST_BUCKET_NAME
        return AMAZON_TEST_BUCKET_NAME

    @staticmethod
    def credentials(nokms: bool = False) -> AmazonCredentials:
        return AmazonCredentials(amazon_credentials_file_path(),
                                 kms_key_id=None if nokms is True else AMAZON_KMS_KEY_ID)

    @staticmethod
    def cloud(nokms: bool = False) -> AwsS3:
        return AwsS3(Amazon.credentials(nokms=nokms))

    @staticmethod
    @contextmanager
    def temporary_cloud_file(nosubfolder: bool = False, nokms: bool = False, size: Optional[int] = None) -> str:

        global TEST_FILE_PREFIX, TEST_FILE_SUFFIX, TEST_FILE_SIZE

        assert nosubfolder in (True, False)
        assert nokms in (True, False)
        if size is None: size = TEST_FILE_SIZE  # noqa
        assert isinstance(size, int) and (size >= 0)

        key = f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}"
        if nosubfolder is False:
            subfolder = f"{TEST_FILE_PREFIX}{create_uuid()}"
            key = cloud_path.join(subfolder, key)

        cloud = Amazon.cloud(nokms=nokms)
        try:
            with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=size) as tmp_file_path:
                assert cloud.upload_file(tmp_file_path, Amazon.bucket, key) is True
                assert cloud.file_exists(Amazon.bucket, key) is True
                assert cloud.file_size(Amazon.bucket, key) == size
                if nokms is False:
                    assert cloud.file_kms_encrypted(Amazon.bucket, key, AMAZON_KMS_KEY_ID) is True
                yield cloud_path.join(Amazon.bucket, key)
        except Exception as e:
            pytest.fail("Cannot create (non-rclone) Amazon S3 object!")
            return None
        finally:
            cloud.delete_file(Amazon.bucket, key)


class Google:

    @classmethod
    @property
    def bucket(cls) -> str:
        global GOOGLE_TEST_BUCKET_NAME
        return GOOGLE_TEST_BUCKET_NAME

    @staticmethod
    def credentials() -> GoogleCredentials:
        return GoogleCredentials(google_service_account_file_path())

    @staticmethod
    def cloud() -> Gcs:
        return Gcs(Google.credentials())

    @staticmethod
    @contextmanager
    def temporary_cloud_file(nosubfolder: bool = False, size: Optional[int] = None) -> str:

        global TEST_FILE_PREFIX, TEST_FILE_SUFFIX, TEST_FILE_SIZE

        assert nosubfolder in (True, False)
        if size is None: size = TEST_FILE_SIZE  # noqa
        assert isinstance(size, int) and (size >= 0)

        key = f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}"
        if nosubfolder is False:
            subfolder = f"{TEST_FILE_PREFIX}{create_uuid()}"
            key = cloud_path.join(subfolder, key)

        cloud = Google.cloud()
        try:
            with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=size) as tmp_file_path:
                assert cloud.upload_file(tmp_file_path, Google.bucket, key) is True
                assert cloud.file_exists(Google.bucket, key) is True
                assert cloud.file_size(Google.bucket, key) == size
                yield cloud_path.join(Google.bucket, key)
        except Exception:
            pytest.fail("Cannot create (non-rclone) Google GCS object!")
            return None
        finally:
            cloud.delete_file(Google.bucket, key)
