# Configuration parameters for rclone related integration testing.

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
