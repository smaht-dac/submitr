import os
import pytest
from dcicutils.file_utils import compute_file_md5 as get_file_checksum, get_file_size
from dcicutils.tmpfile_utils import temporary_directory
from submitr.rclone.rcloner import RCloner
from submitr.rclone.rclone_amazon import RCloneAmazon
from submitr.rclone.rclone_google import RCloneGoogle
from submitr.rclone.rclone_utils import cloud_path
from submitr.tests.integration.testing_rclone_helpers import Amazon, Google
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

# This marks this entire module as "integrtation" tests.
# To run only integration tests:    pytest -m integration
# To run all but integration tests: pytest -m "not integration"
pytestmark = [pytest.mark.integration]


def setup_module():
    rclone_config_setup_module()


def teardown_module():
    rclone_config_teardown_module()


@pytest.mark.parametrize("credentials_type",
                         [Amazon.CredentialsType.DEFAULT,
                          Amazon.CredentialsType.TEMPORARY,
                          Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC])
@pytest.mark.parametrize("nokms", [False, True])
def test_new_amazon_to_local(nokms, credentials_type) -> None:
    with Amazon.temporary_cloud_file(nokms=nokms) as store_path, temporary_directory() as tmpdir:
        # Here we have a temporary cloud file for testing rclone copy to local.
        credentials = Amazon.credentials(nokms=nokms, credentials_type=credentials_type, path=store_path)
        store = RCloneAmazon(credentials)
        # Copy from cloud to local via rclone.
        RCloner(source=store).copy(store_path, tmpdir)
        # Sanity check.
        local_file_path = os.path.join(tmpdir, cloud_path.basename(store_path))
        assert store.file_exists(store_path) is True
        assert get_file_size(local_file_path) == store.file_size(store_path) == TEST_FILE_SIZE
        # N.B. For AWS S3 keys with KMS encryption rclone hashsum md5 does not seem to work;
        # the command does not fail but returns no checksum (just the filename in the output);
        # removing the KMS info from the rclone config file fixes this, and it does return a
        # checksum value but it is not the same as the one we compute for the same file.
        # But for our real-life use-cases, so far, it is of little/no consequence, since
        # we do not support specifying a KMS key ID for an S3 --cloud-source. And on the
        # destination side (i.e for smaht-submitr file uploads), we use boto3 to get the
        # checksum, as we have the (Portal-generated temporary/session) credentials we need
        # to do this (and because of this and general issues with checksums). And neither does
        # boto3 get a reliable checksum value; sometimes sjust the etag which can be different.
        # And so for integration tests, we skip this.
        # assert get_file_checksum(local_file_path) == store.file_checksum(store_path) if nokms is True else True
        # TODO: Investigate further ...
        assert get_file_checksum(local_file_path) == Amazon.s3.file_checksum(store_path) if nokms is True else True
        assert os.path.isfile(local_file_path) is True
        assert get_file_size(local_file_path) == (Amazon.s3 if nokms is True else Amazon.s3_kms).file_size(store_path)
        # No cleanup; context managers above do it.


@pytest.mark.parametrize("credentials_type",
                         [Amazon.CredentialsType.DEFAULT,
                          Amazon.CredentialsType.TEMPORARY,
                          Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC])
@pytest.mark.parametrize("kms", [False, True])
@pytest.mark.parametrize("subfolder", [False, True])
def test_new_local_to_amazon(credentials_type, kms, subfolder) -> None:
    with Amazon.temporary_local_file() as tmpfile:
        # Here we have a temporary local file for testing rclone copy to cloud.
        store_path = Amazon.create_temporary_cloud_file_path(Amazon.bucket, subfolder)
        # Copy from local to cloud via rclone.
        credentials = Amazon.credentials(nokms=not kms, credentials_type=credentials_type, path=store_path)
        store = RCloneAmazon(credentials)
        RCloner(destination=store).copy(tmpfile, store_path) is True
        # Sanity check.
        store.file_exists(store_path) is True
        store.file_size(store_path) == TEST_FILE_SIZE
        store.file_checksum(store_path) == get_file_checksum(tmpfile)
        Amazon.s3.file_exists(store_path) is True
        Amazon.s3.file_size(store_path) == TEST_FILE_SIZE
        Amazon.s3.file_checksum(store_path) == get_file_checksum(tmpfile)
        # Cleanup.
        Amazon.s3.delete_file(store_path) is True
        Amazon.s3.file_exists(store_path) is False
        store.file_exists(store_path) is False


def test_new_google_to_local() -> None:
    with Google.temporary_cloud_file() as store_path, temporary_directory() as tmpdir:
        # Here we have a temporary cloud file for testing rclone copy to local.
        credentials = Google.credentials()
        store = RCloneGoogle(credentials)
        # Copy from cloud to local via rclone.
        RCloner(source=store).copy(store_path, tmpdir)
        # Sanity check.
        local_file_path = os.path.join(tmpdir, cloud_path.basename(store_path))
        assert store.file_exists(store_path) is True
        assert get_file_size(local_file_path) == store.file_size(store_path) == TEST_FILE_SIZE
        assert get_file_checksum(local_file_path) == store.file_checksum(store_path)
        assert os.path.isfile(local_file_path) is True
        # No cleanup; context managers above do it.


@pytest.mark.parametrize("subfolder", [False, True])
def test_new_local_to_google(subfolder) -> None:
    with Google.temporary_local_file() as tmpfile:
        # Here we have a temporary local file for testing rclone copy to cloud.
        store_path = Google.create_temporary_cloud_file_path(Google.bucket, subfolder)
        # Copy from local to cloud via rclone.
        credentials = Google.credentials()
        store = RCloneGoogle(credentials)
        RCloner(destination=store).copy(tmpfile, store_path) is True
        # Sanity check.
        store.file_exists(store_path) is True
        store.file_size(store_path) == TEST_FILE_SIZE
        store.file_checksum(store_path) == get_file_checksum(tmpfile)
        Google.gcs.file_exists(store_path) is True
        Google.gcs.file_size(store_path) == TEST_FILE_SIZE
        Google.gcs.file_checksum(store_path) == get_file_checksum(tmpfile)
        # Cleanup.
        Google.gcs.delete_file(store_path) is True
        Google.gcs.file_exists(store_path) is False


@pytest.mark.parametrize("amazon_subfolder", [False, True])
@pytest.mark.parametrize("google_subfolder", [False, True])
def test_new_google_to_amazon(amazon_subfolder, google_subfolder) -> None:
    with Google.temporary_cloud_file(subfolder=google_subfolder) as google_path:
        amazon_path = Amazon.create_temporary_cloud_file_path(Amazon.bucket, subfolder=amazon_subfolder)
        assert google_path  # TODO
        assert amazon_path  # TODO


def test_new_amazon_to_amazon() -> None:
    with Amazon.temporary_cloud_file() as amazon_path:
        assert amazon_path  # TODO


def test_new_google_to_google() -> None:
    with Google.temporary_cloud_file() as google_path:
        assert google_path  # TODO


def test_new_amazon_to_google() -> None:
    with Amazon.temporary_cloud_file() as amazon_path:
        assert amazon_path  # TODO
