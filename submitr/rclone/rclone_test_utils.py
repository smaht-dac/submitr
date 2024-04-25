from __future__ import annotations
import boto3
from botocore.client import BaseClient as BotoClient
import configparser
import os
import random
import string
from typing import Optional
from dcicutils.misc_utils import create_dict
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file


class S3:

    @staticmethod
    def create(*args, **kwargs) -> S3:
        return S3(*args, **kwargs)

    def __init__(self,
                 aws_credentials_file: Optional[str] = None,
                 aws_credentials_file_section: Optional[str] = None,
                 aws_default_region: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_session_token: Optional[str] = None,
                 aws_kms_key_id: Optional[str] = None,
                 default_bucket: Optional[str] = None,
                 env: Optional[str] = None) -> None:
        if aws_credentials_file:
            aws_credentials = S3.get_credentials_from_file(aws_credentials_file, aws_credentials_file_section)
            self._default_region = aws_default_region or aws_credentials.get("aws_default_region", None)
            self._access_key_id = aws_access_key_id or aws_credentials.get("aws_access_key_id", None)
            self._secret_access_key = aws_secret_access_key or aws_credentials.get("aws_secret_access_key", None)
            self._session_token = aws_session_token or aws_credentials.get("aws_session_token", None)
        else:
            self._default_region = aws_default_region
            self._access_key_id = aws_access_key_id
            self._secret_access_key = aws_secret_access_key
            self._session_token = aws_session_token
        self._default_bucket = default_bucket
        self._env = env
        self._client = boto3.client(
            "s3",
            region_name=aws_default_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token)
        self._kms_key_id = aws_kms_key_id

    @staticmethod
    def get_credentials_from_file(credentials_file: str, section_name: str = None) -> dict:
        result = {}
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
                aws_session_token=session_token)
        except Exception:
            pass
        return result

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

    @property
    def client(self) -> BotoClient:
        return self._client

    @property
    def default_region(self) -> Optional[str]:
        return self._default_region

    @property
    def access_key_id(self) -> Optional[str]:
        return self._access_key_id

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._secret_access_key

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    @property
    def default_bucket(self) -> Optional[str]:
        return self._default_bucket

    @property
    def env(self) -> Optional[str]:
        return self._env

    @property
    def extra_args(self) -> Optional[dict]:
        if self.kms_key_id:
            return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self.kms_key_id}
        return None

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None) -> bool:
        try:
            if not key:
                key = os.path.basename(file)
            self.client.upload_file(file, bucket, key, ExtraArgs=self.extra_args)
            return True
        except Exception as e:
            raise e

    def download_file(self, bucket: str, key: str, file: str) -> bool:
        try:
            self.client.download_file(bucket, key, file)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            raise e

    def delete_file(self, bucket: str, key: str, check: bool = False) -> bool:
        try:
            if not check or self.file_exists(bucket, key):
                self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def file_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            raise e

    def file_equals(self, bucket: str, key: str, file: str) -> bool:
        try:
            with temporary_file() as temporary_downloaded_file_name:
                if self.download_file(bucket, key, temporary_downloaded_file_name):
                    return self.are_files_equal(file, temporary_downloaded_file_name)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            raise e

    @staticmethod
    def are_files_equal(filea: str, fileb: str) -> bool:
        try:
            with open(filea, "rb") as fa:
                with open(fileb, "rb") as fb:
                    chunk_size = 4096
                    while True:
                        chunka = fa.read(chunk_size)
                        chunkb = fb.read(chunk_size)
                        if chunka != chunkb:
                            return False
                        if not chunka:
                            break
            return True
        except Exception:
            return False

    @staticmethod
    def create_random_file(file: Optional[str] = None,
                           prefix: Optional[str] = None, suffix: Optional[str] = None,
                           nbytes: int = 1024, binary: bool = False) -> str:
        if not file:
            file = create_temporary_file_name(prefix=prefix, suffix=suffix)
        with open(file, "wb" if binary is True else "w") as f:
            if binary is True:
                f.write(os.urandom(nbytes))
            else:
                f.write(''.join(random.choices(string.ascii_letters + string.digits, k=nbytes)))
        return file
