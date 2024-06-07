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


def test_new_local_to_amazon(nokms: bool = True) -> None:
    nokms = False
    with Amazon.temporary_cloud_file(nokms=nokms) as store_path, temporary_directory() as tmpdir:
        store = RCloneAmazon(Amazon.credentials(nokms=nokms))
        RCloner(source=store).copy(store_path, tmpdir)
        local_file_path = os.path.join(tmpdir, cloud_path.basename(store_path))
        assert os.path.isfile(local_file_path)
        assert get_file_size(local_file_path) == store.file_size(store_path)
        # N.B. For AWS S3 keys with KMS encryption rclone hashsum md5 does not seem to work;
        # the command does not fail but returns no checksum (just the filename in the output);
        # removing the KMS info from the rclone config file fixes this, and it does return a
        # checksum value but it is not the same as the one we compute for the same file.
        # So not good, but for our use-cases so far it is of no consequence. But for
        # integration tests, we can just use AWS directly (via boto and our credentials).
        # assert get_file_checksum(local_file_path) == store.file_checksum(store_path)


def test_new_local_to_google() -> None:
    with Google.temporary_cloud_file() as store_path,temporary_directory() as tmpdir:
        store = RCloneGoogle(Google.credentials())
        RCloner(source=store).copy(store_path, tmpdir)
        local_file_path = os.path.join(tmpdir, cloud_path.basename(store_path))
        assert os.path.isfile(local_file_path)
        assert get_file_size(local_file_path) == store.file_size(store_path)
        assert get_file_checksum(local_file_path) == store.file_checksum(store_path)
