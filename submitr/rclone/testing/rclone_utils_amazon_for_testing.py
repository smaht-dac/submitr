from __future__ import annotations
import boto3
from botocore.client import BaseClient as BotoClient
import configparser
from datetime import timedelta
import os
from typing import List, Optional, Union
from dcicutils.file_utils import are_files_equal
from dcicutils.tmpfile_utils import temporary_file
from dcicutils.datetime_utils import format_datetime
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_config_amazon import AmazonCredentials


# Module with class/functions to aid in integration testing of smaht-submitr rclone support.

class AwsS3:

    @staticmethod
    def create(*args, **kwargs) -> AwsS3:
        return AwsS3(*args, **kwargs)

    def __init__(self, credentials: AmazonCredentials) -> None:
        self._credentials = AmazonCredentials(credentials)
        self._client = None

    @property
    def credentials(self) -> AmazonCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: AmazonCredentials) -> None:
        if isinstance(value, AmazonCredentials) and value != self._credentials:
            self._credentials = value
            self._client = None

    @property
    def client(self) -> BotoClient:
        if not self._client:
            self._client = boto3.client(
                "s3",
                region_name=self.credentials.region,
                aws_access_key_id=self.credentials.access_key_id,
                aws_secret_access_key=self.credentials.secret_access_key,
                aws_session_token=self.credentials.session_token)
        return self._client

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file, str) or not file:
                return False
            if not (bucket := RCloneConfig._normalize_cloud_path(bucket)):
                return False
            if not (key := RCloneConfig._normalize_cloud_path(key)):
                key = os.path.basename(file)
            if kms_key_id := self.credentials.kms_key_id:
                # Note that it is not necessary to use the KMS Key ID when downloading
                # a file uploaded with a KMS Key ID, since this info is stored together
                # with the uploaded file and is used if applicable.
                extra_args = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": kms_key_id}
            else:
                extra_args = None
            self.client.upload_file(file, bucket, key, ExtraArgs=extra_args)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def download_file(self, bucket: str, key: str, file: str,
                      nodirectories: bool = False, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := RCloneConfig._normalize_cloud_path(bucket)):
                return False
            if not (key := RCloneConfig._normalize_cloud_path(key)):
                return False
            if not isinstance(file, str) or not file:
                return False
            if os.path.isdir(file):
                separator = RCloneConfig.CLOUD_PATH_SEPARATOR
                if separator in key:
                    if nodirectories is True:
                        file = os.path.join(file, key.replace(separator, "_"))
                    else:
                        directory = os.path.join(file, os.path.dirname(key.replace(separator, os.sep)))
                        os.makedirs(directory, exist_ok=True)
                        file = os.path.join(directory, os.path.basename(key.replace(separator, os.sep)))
                else:
                    file = os.path.join(file, key)
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
                    return are_files_equal(file, temporary_downloaded_file_name)
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def file_kms_encrypted(self, bucket: str, key: str,
                           kms_key_id: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            if file_kms_key_id := response.get("SSEKMSKeyId"):
                if isinstance(kms_key_id, str) and (kms_key_id := kms_key_id.strip()):
                    return True if (kms_key_id in file_kms_key_id) else False
                return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def list_files(self, bucket: str,
                   prefix: Optional[str] = None,
                   sort: Optional[str] = None,
                   count: Optional[int] = None, offset: Optional[int] = None,
                   raise_exception: bool = True) -> List[str]:
        keys = []
        try:
            args = {"Prefix": prefix} if isinstance(prefix, str) and prefix else {}
            while True:
                response = self.client.list_objects_v2(Bucket=bucket, **args)
                if contents := response.get("Contents"):
                    for item in contents:
                        keys.append({"key": item["Key"],
                                     "modified": format_datetime(item["LastModified"]),
                                     "size": item["Size"]})
                if not (continuation_token := response.get("NextContinuationToken")):
                    break
                args["ContinuationToken"] = continuation_token
            if isinstance(sort, str) and (sort := sort.strip().lower()):
                sort_reverse = sort.startswith("-")
                sort_key = "modified" if "modified" in sort else "name"
                keys = sorted(keys, key=lambda item: item[sort_key], reverse=sort_reverse)
        except Exception as e:
            if raise_exception is True:
                raise e
        if isinstance(offset, int) and (offset >= 0):
            if isinstance(count, int) and (count >= 0):
                keys = keys[offset:offset + count]
            else:
                keys = keys[offset:]
        elif isinstance(count, int) and (count >= 0):
            keys = keys[:count]
        return keys

    def generate_temporary_credentials(self,
                                       duration: Optional[Union[int, timedelta]] = None,
                                       bucket: Optional[str] = None, key: Optional[str] = None,
                                       readonly: bool = False) -> Optional[AmazonCredentials]:
        """
        Generates and returns temporary AWS credentials. The default duration of validity for
        the generated credential is one hour; this can be overridden by specifying the duration
        argument (which is in seconds). By default the generated credentials will have full S3
        access (AmazonS3FullAccess); but if the readonly argument is True then this will be
        limited to readonly S3 access (AmazonS3ReadOnlyAccess). Passing bucket or bucket/key
        key argument/s will further limit access to just the specified bucket or bucket/key.
        """
        statements = []
        resources = ["*"] ; deny = False  # noqa
        if isinstance(bucket, str) and (bucket := bucket.strip()):
            if isinstance(key, str) and (key := key.strip()):
                resources = [f"arn:aws:s3:::{bucket}/{key}"]
                # Note that this is specifically required (for some reason) by rclone (but not for plain aws).
                resources += [f"arn:aws:s3:::{bucket}"]  # does not seem to be needed: f"arn:aws:s3:::{bucket}/*"
            else:
                resources = [f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"] ; deny = True  # noqa
        # For how this policy stuff is defined in smaht-portal for file upload
        # session token creation process see: encoded_core.types.file.external_creds
        actions = ["s3:GetObject", "s3:HeadObject", "s3:ListBucket", "s3:DescribeBucket"]
        if kms_key_id := self.credentials.kms_key_id:
            actions_kms = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
            resource_kms = f"arn:aws:kms:{self.credentials.region}:{self.credentials.account_number}:key/{kms_key_id}"
            statements.append({"Effect": "Allow", "Action": actions_kms, "Resource": resource_kms})
        if not (readonly is True):
            # Note the s3:CreateBucket is specifically required (for some reason) by rclone (but not for plain
            # aws), unless these temporary (session) credentials are targetted specifically for the bucket/key.
            actions = actions + ["s3:PutObject", "s3:DeleteObject", "s3:CreateBucket"]
        statements.append({"Effect": "Allow", "Action": actions, "Resource": resources})
        if deny:
            statements.append({"Effect": "Deny", "Action": actions, "NotResource": resources})
        policy = {"Version": "2012-10-17", "Statement": statements}
        credentials = self.credentials.generate_temporary_credentials(duration=duration, policy=policy)
        return AmazonCredentials(credentials) if credentials else None


class AwsCredentials:

    @staticmethod
    def get_credentials_from_file(credentials_file: str,
                                  credentials_section: str = None,
                                  kms_key_id: Optional[str] = None) -> AmazonCredentials:
        if not credentials_section:
            credentials_section = "default"
        try:
            credentials_file = os.path.expanduser(credentials_file)
            if not os.path.isfile(credentials_file):
                if os.path.isdir(credentials_file):
                    credentials_file = os.path.join(credentials_file, "credentials")
                else:
                    # credentials_file = os.path.join(f"~/.aws_test.{credentials_file}", "credentials")
                    credentials_file = os.path.join("~", f".aws_test.{credentials_file}", "credentials")
            config = configparser.ConfigParser()
            config.read(os.path.expanduser(credentials_file))
            section = config[credentials_section]
            region = (section.get("region", None) or
                      section.get("region_name", None) or
                      section.get("aws_default_region", None))
            access_key_id = (section.get("aws_access_key_id", None) or
                             section.get("access_key_id", None))
            secret_access_key = (section.get("aws_secret_access_key", None) or
                                 section.get("secret_access_key", None))
            session_token = (section.get("aws_session_token", None) or
                             section.get("session_token", None))
            return AmazonCredentials(region=region,
                                     access_key_id=access_key_id,
                                     secret_access_key=secret_access_key,
                                     session_token=session_token,
                                     kms_key_id=kms_key_id)
        except Exception:
            pass
        return AmazonCredentials()

    @staticmethod
    def get_credentials_from_environment_variables() -> AmazonCredentials:
        return AmazonCredentials(
            region=os.environ.get("AWS_DEFAULT_REGION", None),
            access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", None),
            secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", None),
            session_token=os.environ.get("AWS_SESSION_TOKEN", None))

    @staticmethod
    def remove_credentials_from_environment_variables() -> None:
        os.environ.pop("AWS_DEFAULT_REGION", None)
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        os.environ.pop("AWS_SESSION_TOKEN", None)
