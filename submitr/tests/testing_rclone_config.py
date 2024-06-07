# Configuration parameters for rclone related integration testing.

import json
import os
import pytest
import tempfile
from dcicutils.file_utils import normalize_path
from dcicutils.tmpfile_utils import create_temporary_file_name, remove_temporary_directory, remove_temporary_file
from submitr.rclone.rclone_google import RCloneGoogle
from submitr.rclone.rclone_installation import RCloneInstallation


# If running from within GitHub actions these environment variables assumed to be
# setup; via .github/workflows/main-integration-tests.yml file and GitHub secrets.
#
# These are setup in GitHub as "secrets". The AWS access key values are currently,
# June 2024, for the special user test-integration-user in the smaht-wolf account;
# the access key was created on 2024-05-15. The Google value is the JSON from the
# service account file exported from the HMS Google account for the smaht-dac project;
# the service account email is ga4-service-account@smaht-dac.iam.gserviceaccount.com;
# its key ID is b488dd9cfde6b59b1aa347aabd9add86c7ff9057; it was created on 2024-04-28.
#
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON
#
# If NOT running from within GitHub actions (i.e. locally) these variables assumed to be setup,
# and from these we obtain the above.
#
# - AMAZON_CREDENTIALS_FILE_PATH
#   Full path to your AWS credentials file (e.g. ~/.aws_test.smaht-wolf/credentials).
# - GOOGLE_SERVICE_ACCOUNT_FILE_PATH
#   Full path to GCP credential "service account file" exported from Google account.

# Set from testing_rclone_helpers.setup_module() IFF running from within GitHub actions.
AMAZON_CREDENTIALS_FILE_PATH = "~/.aws_test.smaht-test/credentials"
GOOGLE_SERVICE_ACCOUNT_FILE_PATH = "~/.config/google-cloud/smaht-dac-617e0480d8e2.json"

# Credentials related values less likely to need updating and hard-coded here.
AMAZON_TEST_BUCKET_NAME = "smaht-unit-testing-files"
AMAZON_REGION = "us-east-1"
AMAZON_KMS_KEY_ID = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"  # fyi: not a secret
GOOGLE_TEST_BUCKET_NAME = "smaht-submitr-rclone-testing"
GOOGLE_LOCATION = "us-east1"

# Other rclone related test parameters.
TEST_FILE_PREFIX = "test-"
TEST_FILE_SUFFIX = ".txt"
TEST_FILE_SIZE = 2048

# Set from rclone_config_setup_module() which should run first via pytest setup_module.
RUNNING_FROM_WITHIN_GITHUB_ACTIONS = None
RUNNING_ON_GOOGLE_COMPUTE_INSTANCE = None
AMAZON_CREDENTIALS_ERROR = None
GOOGLE_CREDENTIALS_ERROR = None
TMPDIR = None


def is_github_actions_context():
    # Returns True iff we are running within GitHub Actions.
    return "GITHUB_ACTIONS" in os.environ


def rclone_config_setup_module():

    global TMPDIR
    TMPDIR = tempfile.mkdtemp()

    global RUNNING_FROM_WITHIN_GITHUB_ACTIONS
    global RUNNING_ON_GOOGLE_COMPUTE_INSTANCE

    global AMAZON_CREDENTIALS_ERROR
    global AMAZON_CREDENTIALS_FILE_PATH

    global GOOGLE_CREDENTIALS_ERROR
    global GOOGLE_SERVICE_ACCOUNT_FILE_PATH

    RUNNING_FROM_WITHIN_GITHUB_ACTIONS = is_github_actions_context()
    RUNNING_ON_GOOGLE_COMPUTE_INSTANCE = RCloneGoogle.is_google_compute_engine()

    def print_integation_testing_context():
        print(f"Running from within GitHub Actions:"
              f" {'YES' if RUNNING_FROM_WITHIN_GITHUB_ACTIONS else 'NO'}")
        print(f"Running on a Google Compute Engine (GCE) instance:"
              f" {'YES' if RUNNING_ON_GOOGLE_COMPUTE_INSTANCE else 'NO'}")

    print_integation_testing_context()

    assert RCloneInstallation.install() is not None
    assert RCloneInstallation.is_installed() is True

    if RUNNING_FROM_WITHIN_GITHUB_ACTIONS:
        access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        session_token = os.environ.get("AWS_SESSION_TOKEN", None)
        if not (access_key_id and secret_access_key):
            AMAZON_CREDENTIALS_ERROR = "AWS acesss keys not defined!"
            pytest.fail("Integration test setup error: AWS acesss keys not defined!")
        else:
            AMAZON_CREDENTIALS_FILE_PATH = create_temporary_file_name()
            with open(AMAZON_CREDENTIALS_FILE_PATH, "w") as f:
                f.write(f"[default]\n")
                f.write(f"aws_access_key_id={access_key_id}\n")
                f.write(f"aws_secret_access_key={secret_access_key}\n")
                f.write(f"aws_session_token={session_token}\n") if session_token else None
            os.chmod(AMAZON_CREDENTIALS_FILE_PATH, 0o600)  # for security
            print(f"Amazon Credentials:")
            print(f"- AWS_ACCESS_KEY_ID: {access_key_id[:2]}{(len(access_key_id) - 2) * '*'}")
            print(f"- AWS_SECRET_ACCESS_KEY: {len(secret_access_key) * '*'}")
            print(f"- AMAZON_CREDENTIALS_FILE_PATH: {AMAZON_CREDENTIALS_FILE_PATH}")
    else:
        if not (AMAZON_CREDENTIALS_FILE_PATH and
                os.path.isfile(normalize_path(AMAZON_CREDENTIALS_FILE_PATH, expand_home=True))):
            AMAZON_CREDENTIALS_ERROR = "No Amazon credentials file defined!"

    if RUNNING_FROM_WITHIN_GITHUB_ACTIONS:
        if not (service_account_json_string := os.environ.get("GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON")):
            pytest.fail("Integration test setup error: No Google credentials defined!")
        service_account_json = json.loads(service_account_json_string)
        google_service_account_file_path = create_temporary_file_name(suffix=".json")
        with open(google_service_account_file_path, "w") as f:
            json.dump(service_account_json, f)
        os.chmod(google_service_account_file_path, 0o600)  # for security
        GOOGLE_SERVICE_ACCOUNT_FILE_PATH = google_service_account_file_path
        print(f"Google Credentials:")
        print(f"- GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON: {len(service_account_json_string) * '*'}")
        print(f"- GOOGLE_SERVICE_ACCOUNT_FILE_PATH: {GOOGLE_SERVICE_ACCOUNT_FILE_PATH}")
    else:
        if not (GOOGLE_SERVICE_ACCOUNT_FILE_PATH and
                os.path.isfile(normalize_path(GOOGLE_SERVICE_ACCOUNT_FILE_PATH, expand_home=True))):
            if not RCloneGoogle.is_google_compute_engine():
                GOOGLE_CREDENTIALS_ERROR = "No Google credentials file defined!"
            else:
                # Google credentials can be None on a GCE instance; i.e. no service account file needed.
                GOOGLE_SERVICE_ACCOUNT_FILE_PATH = None

    # Just make sure no interference from credentials not explicitly setup for testing.
    os.environ.pop("AWS_DEFAULT_REGION", None)
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    os.environ.pop("AWS_SESSION_TOKEN", None)
    assert os.environ.get("AWS_DEFAULT_REGION", None) is None
    assert os.environ.get("AWS_ACCESS_KEY_ID", None) is None
    assert os.environ.get("AWS_SECRET_ACCESS_KEY", None) is None
    assert os.environ.get("AWS_SESSION_TOKEN", None) is None


def rclone_config_teardown_module():

    if is_github_actions_context():
        remove_temporary_file(AMAZON_CREDENTIALS_FILE_PATH)
        remove_temporary_file(GOOGLE_SERVICE_ACCOUNT_FILE_PATH)

    global TMPDIR
    remove_temporary_directory(TMPDIR)
