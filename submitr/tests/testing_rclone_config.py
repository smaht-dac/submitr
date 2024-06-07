# Configuration parameters for rclone related integration testing.

import json
import os
import pytest
import tempfile
from dcicutils.file_utils import create_random_file, compute_file_md5, get_file_size, normalize_path
from dcicutils.structured_data import Portal
from dcicutils.tmpfile_utils import (
    is_temporary_directory, create_temporary_file_name, remove_temporary_directory, remove_temporary_file)
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.google_credentials import GoogleCredentials
from submitr.rclone.rclone_amazon import RCloneAmazon
from submitr.rclone.rclone_google import RCloneGoogle
from submitr.rclone.rclone_store import RCloneStore
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
# If NOT running from within GitHub actions (i.e. locally) these variables assumed
# to be setup here/below, and from these we obtain the above.
#
# - _AMAZON_CREDENTIALS_FILE_PATH
#   Path to AWS credentials file; e.g. ~/.aws_test.smaht-test/credentials.
# - _GOOGLE_SERVICE_ACCOUNT_FILE_PATH
#   Path to GCP service account file exported from Google account; e.g. ~/.config/google/smaht-dac.json.

# Amazon/Google credentials files are setup in rclone_config_setup_module iff
# we are running from within GitHub actions; otherwise these are the values;
# this the rclone_config_setup_module() function should be called from the
# setup_module() function of any test module doing rclone related integration
# testing. NOTE: These two values must be accessed via the functions
# amazon_credentials_file_path() and google_service_account_file_path().
_AMAZON_CREDENTIALS_FILE_PATH = "~/.aws_test.smaht-test/credentials"
_GOOGLE_SERVICE_ACCOUNT_FILE_PATH = "~/.config/google-cloud/smaht-dac.json"

# Credential related values less likely to need updating and hard-coded here.
AMAZON_TEST_BUCKET_NAME = "smaht-unit-testing-files"
AMAZON_REGION = "us-east-1"
AMAZON_KMS_KEY_ID = "27d040a3-ead1-4f5a-94ce-0fa6e7f84a95"  # fyi: not a secret
GOOGLE_TEST_BUCKET_NAME = "smaht-submitr-rclone-testing"
GOOGLE_LOCATION = "us-east1"

# Other rclone related test parameters.
TEST_FILE_PREFIX = "test-"
TEST_FILE_SUFFIX = ".txt"
TEST_FILE_SIZE = 4096

# Set from the rclone_config_setup_module function below, which should be called from
# the setup_module function of any test module doing rclone related integration testing.
_TMPDIR = None


def is_running_from_github_actions():
    # Returns True iff we are running within GitHub Actions.
    return "GITHUB_ACTIONS" in os.environ


def is_running_from_google_compute_engine():
    return RCloneGoogle.is_google_compute_engine()


def amazon_credentials_file_path():
    global _AMAZON_CREDENTIALS_FILE_PATH
    return _AMAZON_CREDENTIALS_FILE_PATH


def google_service_account_file_path():
    global _GOOGLE_SERVICE_ACCOUNT_FILE_PATH
    return _GOOGLE_SERVICE_ACCOUNT_FILE_PATH


def rclone_config_setup_module():

    global _TMPDIR
    global _AMAZON_CREDENTIALS_FILE_PATH
    global _GOOGLE_SERVICE_ACCOUNT_FILE_PATH

    _TMPDIR = tempfile.mkdtemp()

    print(f"Running from within GitHub Actions:"
          f" {'YES' if is_running_from_github_actions() else 'NO'}")
    print(f"Running on a Google Compute Engine (GCE) instance:"
          f" {'YES' if is_running_from_google_compute_engine() else 'NO'}")

    # Make sure rclone is installed.

    assert RCloneInstallation.install() is not None
    assert RCloneInstallation.is_installed() is True

    # Obtain Amazon credentials for testing.

    if is_running_from_github_actions():
        access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        session_token = os.environ.get("AWS_SESSION_TOKEN", None)
        if not (access_key_id and secret_access_key):
            pytest.fail(f"Test setup ERROR: AWS acesss keys not defined!"
                        f" GitHub secrets should be defined for AWS credentials.")
        else:
            _AMAZON_CREDENTIALS_FILE_PATH = create_temporary_file_name()
            with open(_AMAZON_CREDENTIALS_FILE_PATH, "w") as f:
                f.write(f"[default]\n")
                f.write(f"aws_access_key_id={access_key_id}\n")
                f.write(f"aws_secret_access_key={secret_access_key}\n")
                f.write(f"aws_session_token={session_token}\n") if session_token else None
            os.chmod(_AMAZON_CREDENTIALS_FILE_PATH, 0o600)  # for security
            print(f"Amazon Credentials:")
            print(f"- AWS access key ID: {access_key_id[:2]}******")
            print(f"- AWS secret access key: ********")
            if session_token:
                print(f"- AWS session token: {session_token[:2]}******")
            print(f"- AWS credentials file: {_AMAZON_CREDENTIALS_FILE_PATH}")
    else:
        if not (_AMAZON_CREDENTIALS_FILE_PATH and
                os.path.isfile(normalize_path(_AMAZON_CREDENTIALS_FILE_PATH, expand_home=True))):
            pytest.fail(f"Test setup ERROR: No Amazon credentials file defined!"
                        f" The testing_clone_config._AMAZON_CREDENTIALS_FILE_PATH variable"
                        f" should be set to the path of an AWS credentials file.")

    # Obtain Google credentials for testing.

    if is_running_from_github_actions():
        if not (service_account_json_string := os.environ.get("GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON")):
            pytest.fail("Test setup ERROR:"
                        f"No Google credentials defined!"
                        f" GitHub secret GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON"
                        f" should be set to the path of a GCS service account JSON file.")
        service_account_json = json.loads(service_account_json_string)
        google_service_account_file_path = create_temporary_file_name(suffix=".json")
        with open(google_service_account_file_path, "w") as f:
            json.dump(service_account_json, f)
        os.chmod(google_service_account_file_path, 0o600)  # for security
        _GOOGLE_SERVICE_ACCOUNT_FILE_PATH = google_service_account_file_path
        print(f"Google Credentials:")
        print(f"- GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON: {len(service_account_json_string) * '*'}")
        print(f"- _GOOGLE_SERVICE_ACCOUNT_FILE_PATH: {_GOOGLE_SERVICE_ACCOUNT_FILE_PATH}")
    else:
        if not (_GOOGLE_SERVICE_ACCOUNT_FILE_PATH and
                os.path.isfile(normalize_path(_GOOGLE_SERVICE_ACCOUNT_FILE_PATH, expand_home=True))):
            if not RCloneGoogle.is_google_compute_engine():
                pytest.fail(f"Test setup ERROR: No Google credentials file defined!"
                            f" The testing_rclone_config._GOOGLE_SERVICE_ACCOUNT_FILE_PATH variable"
                            f" should be set to the path of a GCS service account JSON file.")
            else:
                # Google credentials can be None on a GCE instance; i.e. no service account file needed.
                _GOOGLE_SERVICE_ACCOUNT_FILE_PATH = None

    # Actually test the Amazon credentials.
    amazon_credentials = AmazonCredentials(_AMAZON_CREDENTIALS_FILE_PATH)
    if not amazon_credentials.ping():
        pytest.fail("Test setup ERROR: Amazon credentials do not appear to work!")

    # Actually test the Google credentials.
    google_credentials = GoogleCredentials(_GOOGLE_SERVICE_ACCOUNT_FILE_PATH)
    if not google_credentials.ping():
        pytest.fail("Test setup ERROR: Google credentials do not appear to work!")

    # TODO: check existence of buckets.

    # Just make sure no interference from credentials not explicitly setup for testing.

    _remove_environment_variables_which_might_interfere_with_testing()


def rclone_config_teardown_module():

    global _TMPDIR

    _restore_environment_variables_which_might_interfere_with_testing()

    if is_running_from_github_actions():
        remove_temporary_file(_AMAZON_CREDENTIALS_FILE_PATH)
        remove_temporary_file(_GOOGLE_SERVICE_ACCOUNT_FILE_PATH)

    remove_temporary_directory(_TMPDIR)


_environment_variables_which_might_interfere_with_testing = {
    "AWS_DEFAULT_REGION": None,
    "AWS_ACCESS_KEY_ID": None,
    "AWS_SECRET_ACCESS_KEY": None,
    "AWS_SESSION_TOKEN": None,
    "AWS_SHARED_CREDENTIALS_FILE": None,
    "AWS_CONFIG_FILE": None,
    "GOOGLE_APPLICATION_CREDENTIALS": None
}


def _remove_environment_variables_which_might_interfere_with_testing():
    return
    for key in _environment_variables_which_might_interfere_with_testing:
        _environment_variables_which_might_interfere_with_testing[key] = os.environ.pop(key, None)


def _restore_environment_variables_which_might_interfere_with_testing():
    return
    for key in _environment_variables_which_might_interfere_with_testing:
        if (value := _environment_variables_which_might_interfere_with_testing[key]) is not None:
            os.environ[key] = value


class Mock_CloudStorage:
    # We simply use the file system, within a temporary directory, via global
    # _TMPDIR (above), to simulate/mock AWS S3 and Google Cloud Storage (GCS).
    def __init__(self, subdir):  # noqa
        global _TMPDIR
        assert isinstance(_TMPDIR, str) and _TMPDIR and is_temporary_directory(_TMPDIR)
        assert isinstance(subdir, str) and subdir
        self._tmpdir = os.path.join(_TMPDIR, subdir)
        os.makedirs(self._tmpdir, exist_ok=True)
        assert is_temporary_directory(self._tmpdir)
    def path_exists(self, path):  # noqa
        return os.path.isfile(path) if (path := self._realpath(path)) else None
    def file_size(self, file):  # noqa
        return get_file_size(file) if (self.path_exists(file) and (file := self._realpath(file))) else None
    def file_checksum(self, file):  # noqa
        return compute_file_md5(file) if (self.path_exists(file) and (file := self._realpath(file))) else None
    def _realpath(self, path):  # noqa
        if isinstance(self, RCloneStore):
            return os.path.join(self._tmpdir, path) if (path := super().path(path)) else None
        return os.path.join(self._tmpdir, path) if (path := normalize_path(path)) else None
    def _root(self):  # noqa
        return self._tmpdir
    def _create_files_for_testing(self, *args, **kwargs):  # noqa
        for arg in args:
            if isinstance(arg, str):
                self._create_file_for_testing(arg, nbytes=kwargs.get("nbytes"))
            elif isinstance(arg, (list, tuple)):
                for file in arg:
                    if isinstance(file, str):
                        self._create_files_for_testing(file, nbytes=kwargs.get("nbytes"))
    def _create_file_for_testing(self, file, nbytes=None):  # noqa
        if not isinstance(nbytes, int) or nbytes < 0:
            nbytes = TEST_FILE_SIZE
        if (file := normalize_path(file)) and (not file.startswith(os.path.sep) or (file := file[1:])):
            if file := self._realpath(file):
                if file_directory := os.path.dirname(file):
                    os.makedirs(file_directory, exist_ok=True)
                create_random_file(file, nbytes=nbytes)
    def _clear_files(self):  # noqa
        assert is_temporary_directory(self._tmpdir)
        remove_temporary_directory(self._tmpdir)
        os.makedirs(self._tmpdir, exist_ok=True)
        assert is_temporary_directory(self._tmpdir)


class Mock_RCloneAmazon(Mock_CloudStorage, RCloneAmazon):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="amazon")
        super(RCloneAmazon, self).__init__(*args, **kwargs)


class Mock_RCloneGoogle(Mock_CloudStorage, RCloneGoogle):

    def __init__(self, *args, **kwargs):
        super().__init__(subdir="google")
        super(RCloneGoogle, self).__init__(*args, **kwargs)


class Mock_LocalStorage(Mock_CloudStorage):
    # Might as well also use Mock_CloudStorage for easy
    # local file system test file setup for convenience.
    def __init__(self, *args, **kwargs):
        super().__init__(subdir="local")
        self.create_files(*args, **kwargs)
    def create_files(self, *args, **kwargs):  # noqa
        super()._create_files_for_testing(*args, **kwargs)
    def create_file(self, *args, **kwargs):  # noqa
        super()._create_file_for_testing(*args, **kwargs)
    @property  # noqa
    def root(self):
        return super()._root()
    def path(self, path):  # noqa
        return os.path.join(self.root, path) if (path := normalize_path(path)) else None


class Mock_Portal(Portal):
    # Designed to handle calls to get_schemas, get_schema, get_schema_type, is_schema_type, is_schema_file_type.
    # which can all be done be simply overriding get_schemas which reads a static/snapshot (2024-05-18) copy
    # of the schemas as returned by the /profiles/ (trailing slash required there btw) endpoint.
    def __init__(self):  # noqa
        dummy_key = {"key": "dummy", "secret": "dummy"}
        super().__init__(dummy_key)
        self._schemas = None
    def get_schemas(self) -> dict:  # noqa
        if not self._schemas:
            self._schemas = load_test_data_json("profiles")
        return self._schemas


def load_test_data_json(file):
    this_directory = os.path.dirname(os.path.abspath(__file__))
    test_data_directory = os.path.join(this_directory, "data")
    test_data_file = os.path.join(test_data_directory, file if file.endswith(".json") else f"{file}.json")
    with open(test_data_file, "r") as f:
        return json.load(f)
