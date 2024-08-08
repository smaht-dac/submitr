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


@pytest.mark.parametrize("amazon_source_credentials_type", Amazon.CredentialTypes)
@pytest.mark.parametrize("amazon_source_kms", [False, True])
def test_amazon_to_local(amazon_source_credentials_type, amazon_source_kms) -> None:
    with Amazon.temporary_cloud_file(kms=amazon_source_kms) as amazon_source_path, \
            temporary_directory() as destination_directory:
        # Here we have a temporary Amazon cloud file for testing rclone copy to local.
        amazon_source_credentials = Amazon.credentials(credentials_type=amazon_source_credentials_type,
                                                       kms=amazon_source_kms, path=amazon_source_path)
        amazon_source_store = RCloneAmazon(amazon_source_credentials)
        # Copy from Amazon cloud to local via rclone.
        rclone = RCloner(source=amazon_source_store)
        assert rclone.copy(amazon_source_path, destination_directory) is True
        # Sanity check.
        local_destination_path = os.path.join(destination_directory, cloud_path.basename(amazon_source_path))
        assert amazon_source_store.file_exists(amazon_source_path) is True
        assert (get_file_size(local_destination_path) ==
                amazon_source_store.file_size(amazon_source_path) == TEST_FILE_SIZE)
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
        # And so for integration tests, we skip the amazon_source_store.file_checksum call.
        if not amazon_source_kms:
            assert get_file_checksum(local_destination_path) == Amazon.s3.file_checksum(amazon_source_path)
        assert os.path.isfile(local_destination_path) is True
        assert (get_file_size(local_destination_path) ==
                Amazon.s3_with(kms=amazon_source_kms).file_size(amazon_source_path) == TEST_FILE_SIZE)
        # No cleanup; context managers above do it.


@pytest.mark.parametrize("amazon_destination_credentials_type", Amazon.CredentialTypes)
@pytest.mark.parametrize("amazon_destination_kms", [False, True])
@pytest.mark.parametrize("amazon_destination_subfolder", [False, True])
def test_local_to_amazon(amazon_destination_credentials_type,
                         amazon_destination_kms, amazon_destination_subfolder) -> None:
    with Amazon.temporary_local_file() as local_source_path:
        # Here we have a temporary local file for testing rclone copy to Amazon cloud.
        amazon_destination_path = Amazon.create_temporary_cloud_file_path(Amazon.bucket,
                                                                          subfolder=amazon_destination_subfolder)
        # Copy from local to Amazon cloud via rclone.
        amazon_destination_credentials = Amazon.credentials(credentials_type=amazon_destination_credentials_type,
                                                            kms=amazon_destination_kms, path=amazon_destination_path)
        amazon_destination_store = RCloneAmazon(amazon_destination_credentials)
        rclone = RCloner(destination=amazon_destination_store)
        assert rclone.copy(local_source_path, amazon_destination_path) is True
        # Sanity check.
        assert amazon_destination_store.file_exists(amazon_destination_path) is True
        assert (amazon_destination_store.file_size(amazon_destination_path) ==
                get_file_size(local_source_path) == TEST_FILE_SIZE)
        if amazon_destination_credentials_type != Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC:
            # N.B. As noted elsewhere, with bucket/key targeted temporary AWS credentials,
            # with a Portal-like policy (i.e. encoded-core/../types/file.py/external_creds,
            # which we implement for testing via AwsS3.generate_temporary_credentials in
            # rclone_utils_for_testing_amazon) rclone hashsum md5 does not work. But via
            # boto3 is does work (test below) so it is OK for our actual use-case in s3_upload.
            assert (amazon_destination_store.file_checksum(amazon_destination_path) ==
                    get_file_checksum(local_source_path))
        assert Amazon.s3.file_exists(amazon_destination_path) is True
        assert Amazon.s3.file_size(amazon_destination_path) == get_file_size(local_source_path) == TEST_FILE_SIZE
        assert Amazon.s3.file_checksum(amazon_destination_path) == get_file_checksum(local_source_path)
        # Cleanup.
        assert Amazon.s3.delete_file(amazon_destination_path) is True
        assert Amazon.s3.file_exists(amazon_destination_path) is False
        assert amazon_destination_store.file_exists(amazon_destination_path) is False


def test_google_to_local() -> None:
    with Google.temporary_cloud_file() as google_source_path, temporary_directory() as destination_directory:
        # Here we have a temporary Google cloud file for testing rclone copy to local.
        google_source_credentials = Google.credentials()
        google_source_store = RCloneGoogle(google_source_credentials)
        # Copy from Google cloud to local via rclone.
        rclone = RCloner(source=google_source_store)
        assert rclone.copy(google_source_path, destination_directory) is True
        # Sanity check.
        local_destination_path = os.path.join(destination_directory, cloud_path.basename(google_source_path))
        assert google_source_store.file_exists(google_source_path) is True
        assert (get_file_size(local_destination_path) ==
                google_source_store.file_size(google_source_path) == TEST_FILE_SIZE)
        assert get_file_checksum(local_destination_path) == google_source_store.file_checksum(google_source_path)
        assert os.path.isfile(local_destination_path) is True
        # No cleanup; context managers above do it.


@pytest.mark.parametrize("google_destination_subfolder", [False, True])
def test_local_to_google(google_destination_subfolder) -> None:
    with Google.temporary_local_file() as local_source_path:
        # Here we have a temporary local file for testing rclone copy to Google cloud.
        google_destination_path = Google.create_temporary_cloud_file_path(Google.bucket,
                                                                          subfolder=google_destination_subfolder)
        # Copy from local to Google cloud via rclone.
        google_destination_credentials = Google.credentials()
        google_destination_store = RCloneGoogle(google_destination_credentials)
        rclone = RCloner(destination=google_destination_store)
        assert rclone.copy(local_source_path, google_destination_path) is True
        # Sanity check.
        assert google_destination_store.file_exists(google_destination_path) is True
        assert google_destination_store.file_size(google_destination_path) == TEST_FILE_SIZE
        assert google_destination_store.file_checksum(google_destination_path) == get_file_checksum(local_source_path)
        assert Google.gcs.file_exists(google_destination_path) is True
        assert Google.gcs.file_size(google_destination_path) == TEST_FILE_SIZE
        assert Google.gcs.file_checksum(google_destination_path) == get_file_checksum(local_source_path)
        # Cleanup.
        assert Google.gcs.delete_file(google_destination_path) is True
        assert Google.gcs.file_exists(google_destination_path) is False


@pytest.mark.parametrize("amazon_destination_credentials_type", Amazon.CredentialTypes)
@pytest.mark.parametrize("amazon_destination_kms", [False, True])
@pytest.mark.parametrize("amazon_destination_subfolder", [False, True])
@pytest.mark.parametrize("google_source_subfolder", [False, True])
def test_google_to_amazon(amazon_destination_credentials_type,
                          amazon_destination_kms, amazon_destination_subfolder, google_source_subfolder) -> None:
    # This is the most important test case (with Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC).
    with Google.temporary_cloud_file(subfolder=google_source_subfolder) as google_source_path:
        # Here we have a temporary Google cloud file for testing rclone copy to Amazon cloud.
        google_source_credentials = Google.credentials()
        google_source_store = RCloneGoogle(google_source_credentials)
        amazon_destination_path = Amazon.create_temporary_cloud_file_path(Amazon.bucket,
                                                                          subfolder=amazon_destination_subfolder)
        amazon_destination_credentials = Amazon.credentials(credentials_type=amazon_destination_credentials_type,
                                                            kms=amazon_destination_kms, path=amazon_destination_path)
        amazon_destination_store = RCloneAmazon(amazon_destination_credentials)
        # Copy from Google cloud to Amazon cloud via rclone.
        rclone = RCloner(source=google_source_store, destination=amazon_destination_store)
        assert rclone.copy(google_source_path, amazon_destination_path) is True
        # Sanity check.
        assert amazon_destination_store.file_exists(amazon_destination_path) is True
        assert amazon_destination_store.file_size(amazon_destination_path) == TEST_FILE_SIZE
        if amazon_destination_credentials_type != Amazon.CredentialsType.TEMPORARY_KEY_SPECIFIC:
            # This amazon_destination_store.file_checksum does not work for temporary credentials due
            # to an oddity of rclone hashsum md5 where it seems to need s3:ListBucket on the ENTIRE
            # bucket; which is not acceptable security-wise for the Portal to do; and so we do
            # not do this in our test code AwsS3.generate_temporary_credentials; and so we
            # need to use boto3 only to obtain the checksum for sanity checking, below.
            assert (amazon_destination_store.file_checksum(amazon_destination_path) ==
                    Google.gcs.file_checksum(google_source_path))
        assert Amazon.s3.file_exists(amazon_destination_path) is True
        assert Amazon.s3.file_size(amazon_destination_path) == TEST_FILE_SIZE
        assert Amazon.s3.file_checksum(amazon_destination_path) == Google.gcs.file_checksum(google_source_path)
        # Cleanup.
        assert Amazon.s3.delete_file(amazon_destination_path) is True
        assert amazon_destination_store.file_exists(amazon_destination_path) is False
        assert Amazon.s3.file_exists(amazon_destination_path) is False


@pytest.mark.parametrize("amazon_destination_credentials_type", Amazon.CredentialTypes)
@pytest.mark.parametrize("amazon_destination_kms", [False, True])
@pytest.mark.parametrize("amazon_destination_subfolder", [False, True])
def test_amazon_to_amazon(amazon_destination_credentials_type,
                          amazon_destination_kms,
                          amazon_destination_subfolder) -> None:
    amazon_source_credentials_type = Amazon.CredentialsType.DEFAULT
    amazon_source_kms = False
    amazon_source_subfolder = True
    with Amazon.temporary_cloud_file(kms=amazon_source_kms, subfolder=amazon_source_subfolder) as amazon_source_path:
        # Here we have a temporary Amazon cloud file for testing rclone copy to Amazon cloud.
        amazon_source_credentials = Amazon.credentials(credentials_type=amazon_source_credentials_type,
                                                       kms=amazon_source_kms,
                                                       path=amazon_source_path)
        amazon_source_store = RCloneAmazon(amazon_source_credentials)
        amazon_destination_path = Amazon.create_temporary_cloud_file_path(Amazon.bucket,
                                                                          subfolder=amazon_destination_subfolder)
        amazon_destination_credentials = Amazon.credentials(credentials_type=amazon_destination_credentials_type,
                                                            kms=amazon_destination_kms,
                                                            path=amazon_destination_path)
        amazon_destination_store = RCloneAmazon(amazon_destination_credentials)
        # Copy from Amazon cloud to Amazon cloud via rclone.
        rclone = RCloner(source=amazon_source_store, destination=amazon_destination_store)
        assert rclone.copy(amazon_source_path, amazon_destination_path) is True
        assert amazon_destination_store.file_exists(amazon_destination_path) is True
        assert amazon_destination_store.file_size(amazon_destination_path) == TEST_FILE_SIZE
        assert (Amazon.s3.file_checksum(amazon_destination_path) ==
                amazon_source_store.file_checksum(amazon_source_path))
        assert Amazon.s3.file_exists(amazon_destination_path) is True
        assert Amazon.s3.file_size(amazon_destination_path) == TEST_FILE_SIZE
        assert Amazon.s3.file_checksum(amazon_destination_path) == Amazon.s3.file_checksum(amazon_source_path)
        # Cleanup.
        assert Amazon.s3.delete_file(amazon_destination_path) is True
        assert amazon_destination_store.file_exists(amazon_destination_path) is False
        assert Amazon.s3.file_exists(amazon_destination_path) is False


@pytest.mark.parametrize("google_destination_subfolder", [False, True])
def test_google_to_google(google_destination_subfolder) -> None:
    google_source_subfolder = True
    # No real need for this as not a real use-case; just for completeness; mostly fell out.
    with Google.temporary_cloud_file(subfolder=google_source_subfolder) as google_source_path:
        # Here we have a temporary Google cloud file for testing rclone copy to Google cloud.
        google_source_credentials = Google.credentials()
        google_source_store = RCloneGoogle(google_source_credentials)
        # Copy from Google cloud to Google cloud via rclone.
        google_destination_path = Google.create_temporary_cloud_file_path(Google.bucket,
                                                                          subfolder=google_destination_subfolder)
        google_destination_credentials = Google.credentials()
        google_destination_store = RCloneGoogle(google_destination_credentials)
        rclone = RCloner(source=google_source_store, destination=google_destination_store)
        assert rclone.copy(google_source_path, google_destination_path) is True
        # Sanity check.
        assert google_destination_store.file_exists(google_destination_path) is True
        assert google_destination_store.file_size(google_destination_path) == TEST_FILE_SIZE
        assert (google_destination_store.file_checksum(google_destination_path) ==
                google_source_store.file_checksum(google_source_path))
        assert Google.gcs.file_exists(google_destination_path) is True
        assert Google.gcs.file_size(google_destination_path) == TEST_FILE_SIZE
        assert Google.gcs.file_checksum(google_destination_path) == Google.gcs.file_checksum(google_source_path)
        # Cleanup.
        assert Google.gcs.delete_file(google_destination_path) is True
        assert google_destination_store.file_exists(google_destination_path) is False
        assert Google.gcs.file_exists(google_destination_path) is False


@pytest.mark.parametrize("amazon_source_kms", [False, True])
@pytest.mark.parametrize("amazon_source_subfolder", [False, True])
def test_amazon_to_google(amazon_source_kms, amazon_source_subfolder) -> None:
    # No real need for this as not a real use-case; just for completeness; mostly fell out.
    with Amazon.temporary_cloud_file(kms=amazon_source_kms) as amazon_source_path:
        # Here we have a temporary Amazon cloud file for testing rclone copy to Google cloud.
        amazon_source_credentials = Amazon.credentials(kms=amazon_source_kms)
        amazon_source_store = RCloneAmazon(amazon_source_credentials)
        # Copy from Amazon cloud to Google cloud via rclone.
        google_destination_path = Google.create_temporary_cloud_file_path(Google.bucket,
                                                                          subfolder=amazon_source_subfolder)
        google_destination_credentials = Google.credentials()
        google_destination_store = RCloneGoogle(google_destination_credentials)
        rclone = RCloner(source=amazon_source_store, destination=google_destination_store)
        assert rclone.copy(amazon_source_path, google_destination_path) is True
        # Sanity check.
        assert google_destination_store.file_exists(google_destination_path) is True
        assert google_destination_store.file_size(google_destination_path) == TEST_FILE_SIZE
        if not amazon_source_kms:
            # Again issues with checksum for Amazon with KMS.
            assert (google_destination_store.file_checksum(google_destination_path) ==
                    amazon_source_store.file_checksum(amazon_source_path))
        assert Google.gcs.file_exists(google_destination_path) is True
        assert Google.gcs.file_size(google_destination_path) == TEST_FILE_SIZE
        if not amazon_source_kms:
            # Again issues with checksum for Amazon with KMS.
            assert (Google.gcs.file_checksum(google_destination_path) ==
                    Amazon.s3_with(kms=amazon_source_kms).file_checksum(amazon_source_path))
        # Cleanup.
        assert Google.gcs.delete_file(google_destination_path) is True
        assert google_destination_store.file_exists(google_destination_path) is False
        assert Google.gcs.file_exists(google_destination_path) is False
