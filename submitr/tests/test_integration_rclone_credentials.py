"""
Unit tests (i.e. no cloud access required) for how the rclone integration test harness obtains
Amazon credentials; see submitr/tests/integration/testing_rclone_helpers.py and
submitr/rclone/testing/rclone_utils_for_testing_amazon.py

The interesting part is how scoped, short-lived credentials for a specific bucket/key are minted.
Historically that was always sts:GetFederationToken, which AWS only permits an IAM user (or the
account root user) to call. That makes it unusable when we are authenticated via web identity
federation (GitHub OIDC), because we are then a role session. sts:AssumeRoleWithWebIdentity takes
the same kind of inline session policy, has the same intersection semantics, and needs no caller
credentials, so it is used instead whenever web identity federation is available. Command-line use
with an IAM user's long-term keys keeps the GetFederationToken path.
"""

import os

from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsS3
from submitr.tests.integration import testing_rclone_helpers
from submitr.tests.integration.testing_rclone_helpers import Amazon
from submitr.tests.integration import testing_rclone_setup

import pytest

ROLE_ARN = "arn:aws:iam::537626822796:role/some-github-actions-role"
SESSION_TOKEN = "IQoJb3JpZ2luX2VjEXAMPLESESSIONTOKEN"

# Every environment variable which makes us think web identity federation is available; tests
# clear all of them so the outcome cannot depend on where the test suite happens to be running.
WEB_IDENTITY_ENVIRONMENT_VARIABLES = ["ACTIONS_ID_TOKEN_REQUEST_URL",
                                      "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
                                      "AWS_WEB_IDENTITY_TOKEN_FILE",
                                      "AWS_OIDC_ROLE_ARN"]


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


@pytest.fixture(autouse=True)
def no_ambient_web_identity(monkeypatch):
    for name in WEB_IDENTITY_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def amazon_credentials_file(tmp_path, monkeypatch):
    # Amazon.credentials reads the credentials file path via
    # testing_rclone_setup.amazon_credentials_file_path, which returns this module global.
    def _setup(session_token=None):
        credentials_file = _write_credentials_file(str(tmp_path), session_token=session_token)
        monkeypatch.setattr(testing_rclone_setup, "_AMAZON_CREDENTIALS_FILE_PATH", credentials_file)
        return credentials_file
    return _setup


@pytest.fixture
def web_identity(monkeypatch):
    """Makes the environment look like GitHub Actions with the id-token: write permission."""
    def _setup(role_arn=ROLE_ARN):
        monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_URL", "https://example.com/token?api-version=1")
        monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "request-token")
        if role_arn:
            monkeypatch.setenv("AWS_OIDC_ROLE_ARN", role_arn)
        response = type("Response", (), {"raise_for_status": lambda self: None,
                                         "json": lambda self: {"value": "the.jwt.token"}})()
        return monkeypatch.setattr(
            "submitr.rclone.testing.rclone_utils_for_testing_amazon.requests.get",
            lambda *args, **kwargs: response)
    return _setup


# ----------------------------------------------------------------------------------------------
# Which STS operation is used to mint scoped temporary credentials.
# ----------------------------------------------------------------------------------------------

class _FakeSts:
    def __init__(self, arn=None):
        self.calls = {}
        self._arn = arn
        self._credentials = {"Credentials": {"AccessKeyId": "ASIAEXAMPLE",
                                             "SecretAccessKey": "secret",
                                             "SessionToken": SESSION_TOKEN}}

    def get_federation_token(self, **kwargs):
        self.calls["get_federation_token"] = kwargs
        return self._credentials

    def assume_role_with_web_identity(self, **kwargs):
        self.calls["assume_role_with_web_identity"] = kwargs
        return self._credentials

    def get_caller_identity(self):
        return {"Account": "537626822796", "Arn": self._arn}


@pytest.fixture
def fake_sts(monkeypatch):
    def _setup(arn=None):
        sts = _FakeSts(arn=arn)
        monkeypatch.setattr(AwsS3, "_create_boto_client", staticmethod(lambda *args, **kwargs: sts))
        return sts
    return _setup


def test_uses_get_federation_token_without_web_identity(fake_sts) -> None:
    # A normal command-line user with an IAM user's long-term keys; behavior must be unchanged.
    sts = fake_sts()
    credentials = AwsS3._generate_temporary_credentials(
        generating_credentials=AmazonCredentials(access_key_id="AKIA", secret_access_key="s"),
        policy={"Version": "2012-10-17", "Statement": []})
    assert "get_federation_token" in sts.calls
    assert "assume_role_with_web_identity" not in sts.calls
    assert credentials.session_token == SESSION_TOKEN


def test_uses_assume_role_with_web_identity_under_oidc(fake_sts, web_identity) -> None:
    # This is the case that used to fail outright: a role session cannot call GetFederationToken.
    sts = fake_sts()
    web_identity()
    policy = {"Version": "2012-10-17",
              "Statement": [{"Effect": "Allow", "Action": ["s3:GetObject"],
                             "Resource": ["arn:aws:s3:::a-bucket/a-key"]}]}
    credentials = AwsS3._generate_temporary_credentials(
        generating_credentials=AmazonCredentials(access_key_id="ASIA", secret_access_key="s",
                                                 session_token=SESSION_TOKEN),
        policy=policy)
    assert "get_federation_token" not in sts.calls
    arguments = sts.calls["assume_role_with_web_identity"]
    assert arguments["RoleArn"] == ROLE_ARN
    assert arguments["WebIdentityToken"] == "the.jwt.token"
    # The scoping is the whole point: the same session policy must reach AssumeRoleWithWebIdentity.
    assert "arn:aws:s3:::a-bucket/a-key" in arguments["Policy"]
    # A role session cannot outlive the role's maximum session duration, one hour by default.
    assert arguments["DurationSeconds"] <= 60 * 60
    # RoleSessionName has a restricted character set and a 64 character limit.
    assert len(arguments["RoleSessionName"]) <= 64
    assert credentials.session_token == SESSION_TOKEN


def test_falls_back_to_federation_token_when_no_role_arn(fake_sts, web_identity) -> None:
    # Web identity is configured but we cannot tell which role to assume, and the caller identity
    # is not an assumed role either, so there is nothing to derive it from.
    sts = fake_sts(arn="arn:aws:iam::537626822796:user/some-user")
    web_identity(role_arn=None)
    AwsS3._generate_temporary_credentials(
        generating_credentials=AmazonCredentials(access_key_id="AKIA", secret_access_key="s"),
        policy={"Version": "2012-10-17", "Statement": []})
    assert "get_federation_token" in sts.calls


def test_role_arn_derived_from_assumed_role_identity(fake_sts, web_identity) -> None:
    sts = fake_sts(arn="arn:aws:sts::537626822796:assumed-role/some-role/GitHubActions")
    web_identity(role_arn=None)
    AwsS3._generate_temporary_credentials(
        generating_credentials=AmazonCredentials(access_key_id="ASIA", secret_access_key="s",
                                                 session_token=SESSION_TOKEN),
        policy={"Version": "2012-10-17", "Statement": []})
    arguments = sts.calls["assume_role_with_web_identity"]
    assert arguments["RoleArn"] == "arn:aws:iam::537626822796:role/some-role"


def test_is_web_identity_configured(web_identity) -> None:
    assert AwsS3.is_web_identity_configured() is False
    web_identity()
    assert AwsS3.is_web_identity_configured() is True


# ----------------------------------------------------------------------------------------------
# The KMS resource ARN needs an account number, which must not come from iam:GetUser.
# ----------------------------------------------------------------------------------------------

def test_account_number_uses_caller_identity(monkeypatch) -> None:
    # iam:GetUser has no answer for a role session, so account_number must not rely on it;
    # sts:GetCallerIdentity requires no permissions and works whoever we are.
    requested = {}

    def _boto_client(service, **kwargs):
        requested["service"] = service
        return type("Sts", (), {"get_caller_identity": lambda self: {"Account": "537626822796"}})()

    monkeypatch.setattr("submitr.rclone.amazon_credentials.BotoClient", _boto_client)
    credentials = AmazonCredentials(access_key_id="ASIA", secret_access_key="s",
                                    session_token=SESSION_TOKEN)
    assert credentials.account_number == "537626822796"
    assert requested["service"] == "sts"


def test_kms_policy_fails_clearly_without_account_number(monkeypatch, fake_sts) -> None:
    # Otherwise the account number lands in the resource ARN as "None" and AWS rejects the request
    # with MalformedPolicyDocument, which is a confusing way to learn this.
    fake_sts()
    monkeypatch.setattr(AmazonCredentials, "account_number", property(lambda self: None))
    s3 = AwsS3(AmazonCredentials(access_key_id="AKIA", secret_access_key="s", region="us-east-1"))
    with pytest.raises(Exception, match="account number"):
        s3.generate_temporary_credentials(bucket="a-bucket", key="a-key",
                                          kms_key_id="27d040a3-ead1-4f5a-94ce-0fa6e7f84a95")


# ----------------------------------------------------------------------------------------------
# The credentials shape the harness expects from the ambient environment.
# ----------------------------------------------------------------------------------------------

def test_default_credentials_accepted_for_iam_user_keys(amazon_credentials_file) -> None:
    amazon_credentials_file()
    credentials = Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)
    assert credentials.access_key_id == "AKIAIOSFODNN7EXAMPLE"
    assert not credentials.session_token
    assert not credentials.kms_key_id


def test_default_credentials_accepted_for_role_session_under_oidc(amazon_credentials_file,
                                                                  web_identity) -> None:
    # Under OIDC the ambient credentials are a role session and so do carry a session token; this
    # is the shape that used to fail the harness outright, and it must now be accepted.
    web_identity()
    amazon_credentials_file(session_token=SESSION_TOKEN)
    credentials = Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)
    assert credentials.session_token == SESSION_TOKEN


def test_default_credentials_shape_must_match_the_environment(amazon_credentials_file,
                                                              web_identity) -> None:
    # A session token with no web identity configured, or vice versa, means credentials are coming
    # from somewhere other than where we think.
    amazon_credentials_file(session_token=SESSION_TOKEN)
    with pytest.raises(AssertionError, match="not setup for web identity"):
        Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)
    web_identity()
    amazon_credentials_file()
    with pytest.raises(AssertionError, match="no session token"):
        Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT)


def test_default_credentials_kms_key_id_still_honored(amazon_credentials_file) -> None:
    amazon_credentials_file()
    credentials = Amazon.credentials(credentials_type=Amazon.CredentialsType.DEFAULT, kms=True)
    assert credentials.kms_key_id == testing_rclone_helpers.AMAZON_KMS_KEY_ID
    assert not credentials.session_token


def test_ping_reports_why_it_failed(amazon_credentials_file, mocker) -> None:
    # A ping failure used to be reported as a bare False, which left the integration test setup
    # saying only "Amazon credentials do not appear to work!" -- no help at all in distinguishing
    # an invalid credential from, say, a bad region. Callers can now ask for the reason.
    amazon_credentials_file()
    credentials = AmazonCredentials(testing_rclone_setup.amazon_credentials_file_path())
    mocker.patch("submitr.rclone.amazon_credentials.BotoClient",
                 side_effect=Exception("The security token included in the request is invalid"))
    assert credentials.ping() is False
    with pytest.raises(Exception, match="security token"):
        credentials.ping(raise_exception=True)
