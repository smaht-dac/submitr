"""
Unit tests (i.e. no cloud access required) for the Amazon credentials guard in the rclone
integration test harness; see submitr/tests/integration/testing_rclone_helpers.py

The rclone integration tests mint scoped, short-lived S3 credentials via sts:GetFederationToken,
which AWS only permits an IAM user (or the account root user) to call; credentials obtained via
AssumeRoleWithWebIdentity -- what GitHub OIDC gives us -- explicitly cannot call it. So the harness
requires that its DEFAULT credentials be an IAM user's long-term keys, i.e. carry no session token.
These tests pin that requirement, since violating it fails the integration suite wholesale and in a
way whose real cause is not obvious from the failure output.
"""

import os

from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.tests.integration import testing_rclone_helpers
from submitr.tests.integration.testing_rclone_helpers import Amazon
from submitr.tests.integration import testing_rclone_setup

import pytest


def _write_credentials_file(directory, session_token=None) -> str:
    credentials_file = os.path.join(directory, "credentials")
    with open(credentials_file, "w") as f:
        f.write("[default]\n")
        f.write("aws_default_region=us-east-1\n")
        f.write("aws_access_key_id=AKIAIOSFODNN7EXAMPLE\n")
        f.write("aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYzEXAMPLEKEY\n")
        if session_token:
            f.write(f"aws_session_token={session_token}\n")
    return credentials_file


@pytest.fixture
def amazon_credentials_file(tmp_path, monkeypatch):
    # Amazon.credentials reads the credentials file path via
    # testing_rclone_setup.amazon_credentials_file_path, which returns this module global.
    def _setup(session_token=None):
        credentials_file = _write_credentials_file(str(tmp_path), session_token=session_token)
        monkeypatch.setattr(testing_rclone_setup, "_AMAZON_CREDENTIALS_FILE_PATH", credentials_file)
        return credentials_file
    return _setup


def test_default_credentials_accepted_for_iam_user_keys(amazon_credentials_file) -> None:
    # Long-term IAM user keys have no session token; this is what the harness requires.
    amazon_credentials_file()
    credentials = Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)
    assert credentials.access_key_id == "AKIAIOSFODNN7EXAMPLE"
    assert not credentials.session_token
    assert not credentials.kms_key_id


def test_default_credentials_rejected_for_assumed_role_session(amazon_credentials_file) -> None:
    # This is the shape aws-actions/configure-aws-credentials produces from GitHub OIDC: temporary
    # credentials carrying a session token. These cannot call sts:GetFederationToken, so the harness
    # must reject them up front rather than failing obscurely deeper in the suite.
    amazon_credentials_file(session_token="IQoJb3JpZ2luX2VjEXAMPLESESSIONTOKEN")
    with pytest.raises(AssertionError) as exception_info:
        Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)
    message = str(exception_info.value)
    # The message must name the actual cause, otherwise this failure mode is a mystery in CI.
    assert "session token" in message
    assert "GetFederationToken" in message
    assert "OIDC" in message


def test_default_credentials_kms_key_id_still_honored(amazon_credentials_file) -> None:
    amazon_credentials_file()
    credentials = Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT, kms=True)
    assert credentials.kms_key_id == testing_rclone_helpers.AMAZON_KMS_KEY_ID
    assert not credentials.session_token


def test_ping_reports_why_it_failed(amazon_credentials_file, mocker) -> None:
    # A ping failure used to be reported as a bare False, which left the integration test setup
    # saying only "Amazon credentials do not appear to work!" -- no help at all in distinguishing
    # an invalid access key from, say, a bad region. Callers can now ask for the reason.
    amazon_credentials_file()
    credentials = AmazonCredentials(testing_rclone_setup.amazon_credentials_file_path())
    mocker.patch("submitr.rclone.amazon_credentials.BotoClient",
                 side_effect=Exception("The security token included in the request is invalid"))
    assert credentials.ping() is False
    with pytest.raises(Exception, match="security token"):
        credentials.ping(raise_exception=True)
