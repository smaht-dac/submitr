from __future__ import annotations
from contextlib import contextmanager
from enum import Enum
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


class Amazon:

    class CredentialsType(Enum):
        DEFAULT = "default"
        TEMPORARY = "temporary"
        TEMPORARY_KEY_SPECIFIC = "temporary-key-specific"

    CredentialTypes = [CredentialsType.DEFAULT, CredentialsType.TEMPORARY, CredentialsType.TEMPORARY_KEY_SPECIFIC]

    @classmethod
    @property
    def bucket(cls) -> str:
        global AMAZON_TEST_BUCKET_NAME
        return AMAZON_TEST_BUCKET_NAME

    @staticmethod
    def credentials(credentials_type: CredentialsType = CredentialsType.DEFAULT,
                    kms: bool = False,
                    path: Optional[str] = None) -> AmazonCredentials:
        assert credentials_type in Amazon.CredentialTypes
        assert kms in [False, True]
        assert path is None or isinstance(path, str)
        kms_key_id = None if not kms else AMAZON_KMS_KEY_ID
        if credentials_type == Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC:
            bucket, key = cloud_path.bucket_and_key(path)
            assert isinstance(bucket, str) and bucket
            assert isinstance(key, str) and key
            credentials = Amazon.s3.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=kms_key_id)
        elif credentials_type == Amazon.CredentialsType.TEMPORARY:
            bucket, key = cloud_path.bucket_and_key(path)
            credentials = Amazon.s3.generate_temporary_credentials(bucket=bucket, key=key,
                                                                   untargeted=True, kms_key_id=kms_key_id)
        elif credentials_type == Amazon.CredentialsType.DEFAULT:
            credentials = AmazonCredentials(amazon_credentials_file_path(), kms_key_id=kms_key_id)
        else:
            pytest.fail(f"Incorrect Amazon.CredentialsType specified.")
        if not kms:
            assert not credentials.kms_key_id
        else:
            assert isinstance(credentials.kms_key_id, str) and credentials.kms_key_id
        if credentials_type == Amazon.CredentialsType.DEFAULT:
            assert not credentials.session_token
        else:
            assert isinstance(credentials.session_token, str) and credentials.session_token
        return credentials

    @classmethod
    @property
    def s3(cls) -> AwsS3:
        # This is for non-rclone based access to S3 (with KMS).
        return AwsS3(cls.credentials(kms=False))

    @classmethod
    @property
    def s3_kms(cls) -> AwsS3:
        # This is for non-rclone based access to S3 (sans KMS).
        return AwsS3(cls.credentials(kms=True))

    @staticmethod
    def s3_with(credentials: Optional[AmazonCredentials] = None,
                credentials_type: Optional[CredentialsType] = CredentialsType.DEFAULT,
                kms: bool = False, path: Optional[str] = None) -> AwsS3:
        # This is for non-rclone based access to S3.
        if isinstance(credentials, AmazonCredentials):
            return AwsS3(credentials)
        assert credentials_type in Amazon.CredentialTypes
        assert kms in [False, True]
        assert path is None or isinstance(path, str)
        return AwsS3(Amazon.credentials(credentials_type=credentials_type, kms=kms, path=path))

    @staticmethod
    @contextmanager
    def temporary_cloud_file(kms: bool = False, subfolder: bool = True, size: Optional[int] = None) -> str:

        global TEST_FILE_PREFIX, TEST_FILE_SUFFIX, TEST_FILE_SIZE

        assert kms in [True, False]
        assert subfolder in [True, False]
        if size is None: size = TEST_FILE_SIZE  # noqa
        assert isinstance(size, int) and (size >= 0)

        key = f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}"
        if subfolder is True:
            subfolder = f"{TEST_FILE_PREFIX}{create_uuid()}"
            key = cloud_path.join(subfolder, key)

        s3 = Amazon.s3 if kms is False else Amazon.s3_kms
        try:
            with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=size) as tmp_file_path:
                assert s3.upload_file(tmp_file_path, Amazon.bucket, key) is True
                assert s3.file_exists(Amazon.bucket, key) is True
                assert s3.file_size(Amazon.bucket, key) == size
                if kms is True:
                    assert s3.file_kms_encrypted(Amazon.bucket, key, AMAZON_KMS_KEY_ID) is True
                yield cloud_path.join(Amazon.bucket, key)
        except Exception as e:
            pytest.fail(f"Error on Amazon temporary cloud file creation context! {str(e)}")
            return None
        finally:
            s3.delete_file(Amazon.bucket, key)

    @staticmethod
    @contextmanager
    def temporary_local_file() -> str:
        with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=TEST_FILE_SIZE) as file:
            yield file

    def create_temporary_cloud_file_path(bucket: Optional[str] = None, subfolder: bool = False) -> str:
        assert bucket is None or (bucket == Amazon.bucket)
        return cloud_path.join(f"{bucket}",
                               f"{TEST_FILE_PREFIX}{create_uuid()}" if subfolder is True else None,
                               f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}")


class Google:

    @classmethod
    @property
    def bucket(cls) -> str:
        global GOOGLE_TEST_BUCKET_NAME
        return GOOGLE_TEST_BUCKET_NAME

    @staticmethod
    def credentials() -> GoogleCredentials:
        return GoogleCredentials(google_service_account_file_path())

    @classmethod
    @property
    def gcs(cls) -> Gcs:
        # This is for non-rclone based access to GCS.
        return Gcs(cls.credentials())

    @staticmethod
    @contextmanager
    def temporary_cloud_file(subfolder: bool = True, size: Optional[int] = None) -> str:

        global TEST_FILE_PREFIX, TEST_FILE_SUFFIX, TEST_FILE_SIZE

        assert subfolder in [True, False]
        if size is None: size = TEST_FILE_SIZE  # noqa
        assert isinstance(size, int) and (size >= 0)

        key = f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}"
        if subfolder is True:
            subfolder = f"{TEST_FILE_PREFIX}{create_uuid()}"
            key = cloud_path.join(subfolder, key)

        gcs = Google.gcs
        try:
            with temporary_random_file(prefix=TEST_FILE_PREFIX, suffix=TEST_FILE_SUFFIX, nbytes=size) as tmp_file_path:
                assert gcs.upload_file(tmp_file_path, Google.bucket, key) is True
                assert gcs.file_exists(Google.bucket, key) is True
                assert gcs.file_size(Google.bucket, key) == size
                yield cloud_path.join(Google.bucket, key)
        except Exception as e:
            pytest.fail(f"Error on Google temporary cloud file creation context! {str(e)}")
            return None
        finally:
            gcs.delete_file(Google.bucket, key)

    @staticmethod
    @contextmanager
    def temporary_local_file() -> str:
        with Amazon.temporary_local_file() as file:
            yield file

    def create_temporary_cloud_file_path(bucket: str, subfolder: bool = False) -> str:
        assert bucket is None or (bucket == Google.bucket)
        return cloud_path.join(f"{bucket}",
                               f"{TEST_FILE_PREFIX}{create_uuid()}" if subfolder is True else None,
                               f"{TEST_FILE_PREFIX}{create_uuid()}{TEST_FILE_SUFFIX}")
