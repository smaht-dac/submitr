from __future__ import annotations
from base64 import b64decode as base64_decode
from boto3 import client as BotoClient
import configparser
from datetime import timedelta
from json import dumps as dump_json
import os
from typing import List, Optional, Union
from dcicutils.file_utils import are_files_equal, normalize_path
from dcicutils.misc_utils import create_short_uuid, normalize_string
from dcicutils.tmpfile_utils import temporary_file
from dcicutils.datetime_utils import format_datetime
from submitr.rclone.rclone_amazon import AmazonCredentials
from submitr.rclone.rclone_utils import cloud_path


# Module with class/functions to aid in integration testing of smaht-submitr rclone support.

class AwsS3:

    @staticmethod
    def create(*args, **kwargs) -> AwsS3:
        return AwsS3(*args, **kwargs)

    def __init__(self, credentials: AmazonCredentials) -> None:
        self._credentials = credentials
        self._client = None

    @property
    def credentials(self) -> AmazonCredentials:
        return self._credentials

    @property
    def client(self) -> BotoClient:
        if not self._client:
            self._client = BotoClient(
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
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if not (key := cloud_path.normalize(key)):
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
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if not (key := cloud_path.normalize(key)):
                return False
            if not isinstance(file, str) or not file:
                return False
            if os.path.isdir(file):
                if cloud_path.has_separator(key):
                    if nodirectories is True:
                        key_as_file_name = key.replace(cloud_path.separator, "_")
                        file = os.path.join(file, key_as_file_name)
                    else:
                        key_as_file_path = cloud_path.to_file_path(key)
                        directory = normalize_path(os.path.join(file, os.path.dirname(key_as_file_path)))
                        os.makedirs(directory, exist_ok=True)
                        file = os.path.join(directory, os.path.basename(key_as_file_path))
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

    def delete_file(self, bucket: str, key: Optional[str] = None,
                    check: bool = False, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return False
        try:
            if not (check is True) or self.file_exists(bucket, key):
                self.client.delete_object(Bucket=bucket, Key=key)
                return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def bucket_exists(self, bucket: str, raise_exception: bool = True) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
            return False

    def file_exists(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return False
        if self._file_head(bucket, key, raise_exception=raise_exception):
            return True
        return False

    def file_equals(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
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

    def file_size(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[int]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            return file_head.get("ContentLength", None)
        return None

    def file_checksum(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[str]:
        # N.B. When using rclone to copy a file to AWS S3, it writes checksum (md5) for the file
        # to the metadata associated with the target key; it seems to put it in two places, in
        # x-amz-meta-md5chksum in the HTTPHeaders and also in md5chksum in the Metadata; see below.
        # But this is (possibly/plausibly) only for smaller sized files; see rclone.py for more
        # comments on checksums; in any case this code here is only for testing and is fine for
        # our purposes of testing the basic functioning of the rclone copy/copyto commands.
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if isinstance(md5 := file_head.get("Metadata", {}).get("md5chksum"), str):
                return base64_decode(md5).hex()
            md5 = file_head.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-meta-md5chksum")
            if isinstance(md5, str):
                return base64_decode(md5).hex()
            return file_head.get("ETag").strip("\"")
        return None

    def file_kms_encrypted(self, bucket: str, key: Optional[str] = None,
                           kms_key_id: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if file_kms_key_id := file_head.get("SSEKMSKeyId"):
                if isinstance(kms_key_id, str) and (kms_key_id := kms_key_id.strip()):
                    return True if (kms_key_id in file_kms_key_id) else False
                return True
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
                                       bucket: Optional[str] = None, key: Optional[str] = None,
                                       kms_key_id: Optional[str] = None,
                                       duration: Optional[Union[int, timedelta]] = None,
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
            else:
                raise Exception("Must use both bucket and key for temporary credentials or no bucket at all.")
        # For how this policy stuff is defined in smaht-portal for file upload
        # session token creation process see: encoded_core.types.file.external_creds
        actions = ["s3:GetObject"]
        if kms_key_id := normalize_string(kms_key_id):
            actions_kms = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
            resource_kms = f"arn:aws:kms:{self.credentials.region}:{self.credentials.account_number}:key/{kms_key_id}"
            statements.append({"Effect": "Allow", "Action": actions_kms, "Resource": resource_kms})
        if not (readonly is True):
            # Note the s3:CreateBucket is specifically required (for some reason) by rclone (but not for plain
            # aws), unless these temporary (session) credentials are targetted specifically for the bucket/key.
            # actions = actions + ["s3:PutObject", "s3:DeleteObject", "s3:CreateBucket"]
            actions = actions + ["s3:PutObject"]
        statements.append({"Effect": "Allow", "Action": actions, "Resource": resources})
        if deny:
            statements.append({"Effect": "Deny", "Action": actions, "NotResource": resources})
        policy = {"Version": "2012-10-17", "Statement": statements}
        return AwsS3._generate_temporary_credentials(generating_credentials=self.credentials,
                                                     policy=policy,
                                                     kms_key_id=kms_key_id,
                                                     duration=duration)

    def _generate_temporary_credentials(generating_credentials: AmazonCredentials,
                                        policy: Optional[dict] = None,
                                        kms_key_id: Optional[str] = None,
                                        duration: Optional[Union[int, timedelta]] = None,
                                        raise_exception: bool = True) -> Optional[AmazonCredentials]:
        """
        Generates and returns temporary AWS credentials. The default duration of validity
        for the generated credential is one hour; this can be overridden by specifying
        the duration argument (which is in seconds). By default the generated credentials
        will have the same permissions as the given generating_credentials; this can be
        changed by passing in an AWS policy object (dictionary).
        """
        DURATION_DEFAULT = 60 * 60  # One hour
        DURATION_MIN = 60 * 15  # Fifteen minutes
        DURATION_MAX = 60 * 60 * 12  # Twelve hours

        if isinstance(duration, timedelta):
            duration = duration.total_seconds()
        if (not isinstance(duration, int)) or (duration <= 0):
            duration = DURATION_DEFAULT
        elif duration < DURATION_MIN:
            duration = DURATION_MIN
        elif duration > DURATION_MAX:
            duration = DURATION_MAX

        policy = dump_json(policy) if isinstance(policy, dict) else None

        name = f"test.smaht.submitr.{create_short_uuid(length=12)}"
        try:
            sts = BotoClient("sts",
                             aws_access_key_id=generating_credentials.access_key_id,
                             aws_secret_access_key=generating_credentials.secret_access_key,
                             aws_session_token=generating_credentials.session_token)
            response = sts.get_federation_token(Name=name, Policy=policy, DurationSeconds=duration)
            if isinstance(credentials := response.get("Credentials"), dict):
                return AwsCredentials(access_key_id=credentials.get("AccessKeyId"),
                                      secret_access_key=credentials.get("SecretAccessKey"),
                                      session_token=credentials.get("SessionToken"),
                                      kms_key_id=kms_key_id)
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    def _file_head(self, bucket: str, key: str, raise_exception: bool = True) -> Optional[dict]:
        try:
            return self.client.head_object(Bucket=bucket, Key=key)
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return None
            if raise_exception is True:
                raise e
            return None


class AwsCredentials(AmazonCredentials):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_temporary_credentials(self, *args, **kwargs) -> Optional[AmazonCredentials]:
        return AwsS3(self).generate_temporary_credentials(*args, **kwargs)

    def to_dictionary(self, environment_names: bool = True) -> dict:
        # FYI used in test_rclone_support to pass into s3_upload.upload_file_to_aws_s3.
        if environment_names is True:
            return {
                "AWS_DEFAULT_REGION_NAME": self.region,
                "AWS_ACCESS_KEY_ID": self.access_key_id,
                "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
                "AWS_SESSION_TOKEN": self.session_token
            }
        else:
            return {
                "region_name": self.region,
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key,
                "aws_session_token": self.session_token
            }

    @staticmethod
    def from_file(credentials_file: str, credentials_section: str = None,
                  region: Optional[str] = None, kms_key_id: Optional[str] = None) -> Optional[AwsCredentials]:
        if not credentials_section:
            credentials_section = "default"
        try:
            credentials_file = normalize_path(credentials_file, expand_home=True)
            if not os.path.isfile(credentials_file):
                if os.path.isdir(credentials_file):
                    credentials_file = os.path.join(credentials_file, "credentials")
                else:
                    credentials_file = os.path.join("~", f".aws_test.{credentials_file}", "credentials")
                    credentials_file = normalize_path(credentials_file, expand_home=True)
                if not os.path.isfile(credentials_file):
                    return None
            config = configparser.ConfigParser()
            config.read(os.path.expanduser(credentials_file))
            section = config[credentials_section]
            region = (normalize_string(region) or
                      section.get("region", None) or
                      section.get("region_name", None) or
                      section.get("aws_default_region", None))
            access_key_id = (section.get("aws_access_key_id", None) or
                             section.get("access_key_id", None))
            secret_access_key = (section.get("aws_secret_access_key", None) or
                                 section.get("secret_access_key", None))
            session_token = (section.get("aws_session_token", None) or
                             section.get("session_token", None))
            if not (access_key_id and secret_access_key):
                return None
            return AwsCredentials(region=region,
                                  access_key_id=access_key_id,
                                  secret_access_key=secret_access_key,
                                  session_token=session_token,
                                  kms_key_id=kms_key_id)
        except Exception:
            pass
        return None

    @staticmethod
    def from_environment_variables() -> Optional[AwsCredentials]:
        region = os.environ.get("AWS_DEFAULT_REGION", None)
        access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        session_token = os.environ.get("AWS_SESSION_TOKEN", None)
        if not (access_key_id and secret_access_key):
            return None
        return AwsCredentials(region=region,
                              access_key_id=access_key_id,
                              secret_access_key=secret_access_key,
                              session_token=session_token)

    @staticmethod
    def remove_credentials_from_environment_variables() -> None:
        os.environ.pop("AWS_DEFAULT_REGION", None)
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        os.environ.pop("AWS_SESSION_TOKEN", None)
