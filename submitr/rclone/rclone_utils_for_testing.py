from __future__ import annotations
import boto3
from botocore.client import BaseClient as BotoClient
import configparser
import os
from typing import Optional, Tuple
from uuid import uuid4 as create_uuid
from dcicutils.file_utils import are_files_equal, create_random_file, normalize_file_path
from dcicutils.misc_utils import create_dict
from dcicutils.tmpfile_utils import temporary_file


# Module with class/functions to aid in
# integration testing of smaht-submitr rclone support.

class AwsCredentials:

    @staticmethod
    def create(*args, **kwargs) -> AwsCredentials:
        return AwsCredentials(*args, **kwargs)

    def __init__(self,
                 credentials_file: Optional[str] = None,
                 credentials_file_section: Optional[str] = None,
                 default_region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None) -> None:
        self._kms_key_id = kms_key_id
        if credentials_file:
            credentials, credentials_file = AwsCredentials.get_credentials_from_file(
                credentials_file, credentials_file_section)
            if credentials:
                self._default_region = default_region or credentials.get("aws_default_region", None)
                self._access_key_id = access_key_id or credentials.get("aws_access_key_id", None)
                self._secret_access_key = secret_access_key or credentials.get("aws_secret_access_key", None)
                self._session_token = session_token or credentials.get("aws_session_token", None)
                self._credentials_file = normalize_file_path(credentials_file)
                return
        self._default_region = default_region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._session_token = session_token
        self._credentials_file = None

    @property
    def credentials_file(self) -> Optional[str]:
        return self._credentials_file

    @property
    def default_region(self) -> Optional[str]:
        return self._default_region

    @default_region.setter
    def default_region(self, value: str) -> None:
        self._default_region = value

    @property
    def access_key_id(self) -> Optional[str]:
        return self._access_key_id

    @access_key_id.setter
    def access_key_id(self, value: str) -> Optional[str]:
        self._access_key_id = value

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value: str) -> Optional[str]:
        self._secret_access_key = value

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    @session_token.setter
    def session_token(self, value: str) -> Optional[str]:
        self._session_token = value

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @kms_key_id.setter
    def kms_key_id(self, value: str) -> Optional[str]:
        self._kms_key_id = value

    @staticmethod
    def get_credentials_from_file(credentials_file: str,
                                  section_name: str = None) -> Tuple[Optional[dict], Optional[str]]:
        if not section_name:
            section_name = "default"
        try:
            credentials_file = os.path.expanduser(credentials_file)
            if not os.path.isfile(credentials_file):
                if os.path.isdir(credentials_file):
                    credentials_file = os.path.join(credentials_file, "credentials")
                else:
                    credentials_file = os.path.join(f"~/.aws_test.{credentials_file}/credentials")
            config = configparser.ConfigParser()
            config.read(os.path.expanduser(credentials_file))
            credentials = config[section_name]
            default_region = (credentials.get("region", None) or
                              credentials.get("region_name", None) or
                              credentials.get("aws_default_region", None))
            access_key_id = (credentials.get("aws_access_key_id", None) or
                             credentials.get("access_key_id", None))
            secret_access_key = (credentials.get("aws_secret_access_key", None) or
                                 credentials.get("secret_access_key", None))
            session_token = (credentials.get("aws_session_token", None) or
                             credentials.get("session_token", None))
            return create_dict(
                aws_default_region=default_region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                aws_session_token=session_token), credentials_file
        except Exception:
            pass
        return None, None

    @staticmethod
    def get_credentials_from_environment_variables() -> dict:
        return create_dict(
            aws_default_region=os.environ.get("AWS_DEFAULT_REGION", None),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", None),
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN", None))

    @staticmethod
    def clear_credentials_from_environment_variables() -> None:
        os.environ.pop("AWS_DEFAULT_REGION", None)
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        os.environ.pop("AWS_SESSION_TOKEN", None)

    def generate_session_credentials(self, role: Optional[str] = None,
                                     raise_exception: bool = True) -> Optional[AwsCredentials]:
        # This is so we can create a AWS session token programmatically for integration testing.
        # Created this role (integration-testing-s3-related-role) in smaht-wolf on 2024-04-25
        # especially for this purpose; it has full S3 access (AmazonS3FullAccess) and allows
        # only the user david.michaels to assume role.
        DEFAULT_TESTING_ROLE = "arn:aws:iam::537626822796:role/integration-testing-s3-related-role"
        if not isinstance(role, str) or not role:
            role = DEFAULT_TESTING_ROLE
        try:
            sts = boto3.client("sts",
                               aws_access_key_id=self.access_key_id,
                               aws_secret_access_key=self.secret_access_key)
            name = f"smaht-submitr-test-session-{create_uuid()}"
            if isinstance(response := sts.assume_role(RoleArn=role, RoleSessionName=name), dict):
                if isinstance(response_credentials := response.get("Credentials"), dict):
                    access_key_id = response_credentials.get("AccessKeyId", None)
                    secret_access_key = response_credentials.get("SecretAccessKey", None)
                    session_token = response_credentials.get("SessionToken", None)
                    if access_key_id and secret_access_key and session_token:
                        return AwsCredentials(
                            access_key_id=access_key_id,
                            secret_access_key=secret_access_key,
                            session_token=session_token)
        except Exception as e:
            if raise_exception:
                raise e
        return None


class AwsS3:

    @staticmethod
    def create(*args, **kwargs) -> AwsS3:
        return AwsS3(*args, **kwargs)

    def __init__(self,
                 credentials: Optional[AwsCredentials] = None,
                 credentials_file: Optional[str] = None,
                 credentials_file_section: Optional[str] = None,
                 default_region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 default_bucket: Optional[str] = None) -> None:
        if isinstance(credentials, AwsCredentials):
            self._credentials = credentials
        else:
            self._credentials = AwsCredentials(
                credentials_file=credentials_file,
                credentials_file_section=credentials_file_section,
                default_region=default_region,
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                kms_key_id=kms_key_id)
        self._default_bucket = default_bucket
        self._client = boto3.client(
            "s3",
            region_name=self._credentials.default_region,
            aws_access_key_id=self._credentials.access_key_id,
            aws_secret_access_key=self._credentials.secret_access_key,
            aws_session_token=self._credentials.session_token)

    @property
    def credentials(self) -> AwsCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: AwsCredentials) -> None:
        if isinstance(value, AwsCredentials):
            self._credentials = value

    @property
    def client(self) -> BotoClient:
        return self._client

    @property
    def default_bucket(self) -> Optional[str]:
        return self._default_bucket

    @default_bucket.setter
    def default_bucket(self, value: str) -> Optional[str]:
        self._default_bucket = value

    @property
    def extra_args(self) -> Optional[dict]:
        if self.credentials.kms_key_id:
            return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self.credentials.kms_key_id}
        return None

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not key:
                key = os.path.basename(file)
            self.client.upload_file(file, bucket, key, ExtraArgs=self.extra_args)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def download_file(self, bucket: str, key: str, file: str, raise_exception: bool = True) -> bool:
        try:
            self.client.download_file(bucket, key, file)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def delete_file(self, bucket: str, key: str, check: bool = False, raise_exception: bool = True) -> bool:
        try:
            if not (check is True) or self.file_exists(bucket, key):
                self.client.delete_object(Bucket=bucket, Key=key)
                return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def file_exists(self, bucket: str, key: str, raise_exception: bool = True) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def file_equals(self, bucket: str, key: str, file: str, raise_exception: bool = True) -> bool:
        try:
            with temporary_file() as temporary_downloaded_file_name:
                if self.download_file(bucket, key, temporary_downloaded_file_name):
                    return self.are_files_equal(file, temporary_downloaded_file_name)
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    @staticmethod
    def are_files_equal(filea: str, fileb: str) -> bool:
        return are_files_equal(filea, fileb)

    @staticmethod
    def create_random_file(file: Optional[str] = None,
                           prefix: Optional[str] = None, suffix: Optional[str] = None,
                           nbytes: int = 1024, binary: bool = False) -> str:
        return create_random_file(file=file, prefix=prefix, suffix=suffix, nbytes=nbytes, binary=binary)
