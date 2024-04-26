from __future__ import annotations
import boto3
from botocore.client import BaseClient as BotoClient
import configparser
from datetime import timedelta
import os
from typing import Optional, Union
from dcicutils.file_utils import are_files_equal, create_random_file, normalize_file_path
from dcicutils.misc_utils import create_dict
from dcicutils.tmpfile_utils import temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_config_amazon import AmazonCredentials


# Module with class/functions to aid in
# integration testing of smaht-submitr rclone support.

class AwsCredentials(AmazonCredentials):

    @staticmethod
    def create(*args, **kwargs) -> AwsCredentials:
        return AwsCredentials(*args, **kwargs)

    def __init__(self,
                 credentials: Optional[Union[str, AwsCredentials]] = None,
                 credentials_section: Optional[str] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None) -> None:

        import pdb ; pdb.set_trace()
        pass
        if isinstance(credentials, AmazonCredentials):
            super().__init__(credentials)
            self._credentials_file = None
        elif (isinstance(credentials, str) and
              (credentials := AwsCredentials.get_credentials_from_file(credentials, credentials_section))):
            super().__init__(region=credentials.get("region"),
                             access_key_id=credentials.get("access_key_id"),
                             secret_access_key=credentials.get("secret_access_key"),
                             session_token=credentials.get("session_token"))
            self._credentials_file = credentials.get("credentials_file")
        else:
            super().__init__()
            self._credentials_file = None

        if region := RCloneConfig._normalize_string_value(region):
            super().region = region
        if access_key_id := RCloneConfig._normalize_string_value(access_key_id):
            super().access_key_id = access_key_id
        if secret_access_key := RCloneConfig._normalize_string_value(secret_access_key):
            super().secret_access_key = secret_access_key
        if session_token := RCloneConfig._normalize_string_value(session_token):
            super().session_token = session_token
        if kms_key_id := RCloneConfig._normalize_string_value(kms_key_id):
            super().kms_key_id = kms_key_id

    @property
    def credentials_file(self) -> Optional[str]:
        return self._credentials_file

    @staticmethod
    def get_credentials_from_file(credentials_file: str, credentials_section: str = None) -> Optional[dict]:
        if not credentials_section:
            credentials_section = "default"
        try:
            credentials_file = os.path.expanduser(credentials_file)
            if not os.path.isfile(credentials_file):
                if os.path.isdir(credentials_file):
                    credentials_file = os.path.join(credentials_file, "credentials")
                else:
                    credentials_file = os.path.join(f"~/.aws_test.{credentials_file}/credentials")
            config = configparser.ConfigParser()
            config.read(os.path.expanduser(credentials_file))
            credentials = config[credentials_section]
            region = (credentials.get("region", None) or
                      credentials.get("region_name", None) or
                      credentials.get("aws_default_region", None))
            access_key_id = (credentials.get("aws_access_key_id", None) or
                             credentials.get("access_key_id", None))
            secret_access_key = (credentials.get("aws_secret_access_key", None) or
                                 credentials.get("secret_access_key", None))
            session_token = (credentials.get("aws_session_token", None) or
                             credentials.get("session_token", None))
            return create_dict(
                region=region,
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                credentials_file=normalize_file_path(credentials_file))
        except Exception:
            return None

    @staticmethod
    def get_credentials_from_environment_variables() -> dict:
        return create_dict(
            region=os.environ.get("AWS_DEFAULT_REGION", None),
            access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", None),
            secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", None),
            session_token=os.environ.get("AWS_SESSION_TOKEN", None))

    @staticmethod
    def clear_credentials_from_environment_variables() -> None:
        os.environ.pop("AWS_DEFAULT_REGION", None)
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        os.environ.pop("AWS_SESSION_TOKEN", None)

    def generate_temporary_credentials(self, *args, **kwargs):
        return AwsCredentials(super().generate_temporary_credentials(*args, **kwargs))


class AwsS3:

    @staticmethod
    def create(*args, **kwargs) -> AwsS3:
        return AwsS3(*args, **kwargs)

    def __init__(self, credentials: AmazonCredentials, default_bucket: Optional[str] = None) -> None:
        self._credentials = AwsCredentials(credentials)
        self._default_bucket = default_bucket
        self._client = boto3.client(
            "s3",
            region_name=self._credentials.region,
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

    def generate_temporary_credentials(self, duration: Optional[Union[int, timedelta]] = None,
                                       bucket: Optional[str] = None, key: Optional[str] = None,
                                       readonly: bool = False) -> AwsCredentials:
        policy_resources = ["*"]
        policy_include_deny = False
        if isinstance(bucket, str) and bucket:
            if isinstance(key, str) and bucket:
                policy_resources = ["arn:aws:s3:::{bucket}/{key}"]
            else:
                policy_resources = ["arn:aws:s3:::{bucket}", "arn:aws:s3:::{bucket}/*"]
                policy_include_deny = True

        if readonly:
            # AmazonS3ReadOnlyAccess
            policy_actions = ["s3:Get*", "s3:Head*", "s3:List*", "s3:Describe*",
                              "s3-object-lambda:Get*", "s3-object-lambda:Head*", "s3-object-lambda:List*"]
        else:
            # AmazonS3FullAccess
            policy_actions = ["s3:*", "s3-object-lambda:*"]

        statements = []
        statements.append({"Effect": "Allow", "Action": policy_actions, "Resource": policy_resources})
        if policy_include_deny:
            statements.append = [{"Effect": "Deny", "Action": policy_actions, "NotResource": policy_resources}]

        policy = {"Version": "2012-10-17", "Statement": statements}

        return self.credentials.generate_temporary_credentials(duration=duration, policy=policy)
