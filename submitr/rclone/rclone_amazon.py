from __future__ import annotations
from boto3 import client as BotoClient
import configparser
import os
from typing import Optional, Tuple, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string
from submitr.rclone.rclone_config import RCloneConfig, RCloneCredentials
from submitr.rclone.rclone_utils import cloud_path


class RCloneAmazon(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[AmazonCredentials, RCloneAmazon, str]] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 name: Optional[str] = None,
                 bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneAmazon):
            name = normalize_string(name) or credentials_or_config.name
            bucket = cloud_path.normalize(bucket) or credentials_or_config.bucket
            credentials = credentials_or_config.credentials
        elif isinstance(credentials_or_config, AmazonCredentials):
            credentials = credentials_or_config
        elif (isinstance(credentials_or_config, str) and
              (credentials_file := normalize_path(credentials_or_config, expand_home=True))):
            credentials = credentials_file
        else:
            credentials = None
        credentials = AmazonCredentials(credentials=credentials,
                                        region=region,
                                        access_key_id=access_key_id,
                                        secret_access_key=secret_access_key,
                                        session_token=session_token,
                                        kms_key_id=kms_key_id)
        super().__init__(name=name, bucket=bucket, credentials=credentials)

    @property
    def credentials(self) -> AmazonCredentials:
        return super().credentials

    @property
    def config(self) -> dict:
        return create_dict(provider="AWS",
                           type="s3",
                           region=self.region,
                           access_key_id=self.access_key_id,
                           secret_access_key=self.secret_access_key,
                           session_token=self.session_token,
                           sse_kms_key_id=self.kms_key_id,
                           server_side_encryption="aws:kms" if self.kms_key_id else None)

    @property
    def region(self) -> Optional[str]:
        return self._credentials.region

    @property
    def access_key_id(self) -> Optional[str]:
        return self._credentials.access_key_id

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._credentials.secret_access_key

    @property
    def session_token(self) -> Optional[str]:
        return self._credentials.session_token

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._credentials.kms_key_id

    def __eq__(self, other: Optional[RCloneAmazon]) -> bool:
        return isinstance(other, RCloneAmazon) and super().__eq__(other)

    def __ne__(self, other: Optional[RCloneAmazon]) -> bool:
        return not self.__eq__(other)


class AmazonCredentials(RCloneCredentials):

    def __init__(self,
                 credentials: Optional[AmazonCredentials, str] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None) -> None:

        if isinstance(credentials, AmazonCredentials):
            self._region = credentials.region
            self._access_key_id = credentials.access_key_id
            self._secret_access_key = credentials.secret_access_key
            self._session_token = credentials.session_token
            self._kms_key_id = credentials.kms_key_id
            self._account_number = credentials._account_number  # sic underscore
        elif isinstance(credentials, str) and (credentials := normalize_path(credentials, expand_home=True)):
            region, access_key_id, secret_access_key, session_token = (
                AmazonCredentials._read_credentials_file(credentials))
            self._region = region
            self._access_key_id = access_key_id
            self._secret_access_key = secret_access_key
            self._session_token = session_token
            self._kms_key_id = None
            self._account_number = None
        else:
            self._region = None
            self._access_key_id = None
            self._secret_access_key = None
            self._session_token = None
            self._kms_key_id = None
            self._account_number = None

        if region := normalize_string(region):
            self._region = region
        if access_key_id := normalize_string(access_key_id):
            self._access_key_id = access_key_id
        if secret_access_key := normalize_string(secret_access_key):
            self._secret_access_key = secret_access_key
        if session_token := normalize_string(session_token):
            self._session_token = session_token
        if kms_key_id := normalize_string(kms_key_id):
            self._kms_key_id = kms_key_id

    @property
    def region(self) -> Optional[str]:
        return self._region

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
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @property
    def account_number(self) -> Optional[str]:
        if not self._account_number:
            try:
                iam = BotoClient("iam",
                                 region_name=self.region,
                                 aws_access_key_id=self.access_key_id,
                                 aws_secret_access_key=self.secret_access_key,
                                 aws_session_token=self.session_token)
                response = iam.get_user()
                self._account_number = response["User"]["Arn"].split(":")[4]
            except Exception:
                pass
        return self._account_number

    def __eq__(self, other: Optional[AmazonCredentials]) -> bool:
        return (isinstance(other, AmazonCredentials) and
                (self.region == other.region) and
                (self.access_key_id == other.access_key_id) and
                (self.secret_access_key == other.secret_access_key) and
                (self.session_token == other.session_token) and
                (self.kms_key_id == other.kms_key_id))

    def __ne__(self, other: Optional[AmazonCredentials]) -> bool:
        return not self.__eq__(other)

    @staticmethod
    def _read_credentials_file(credentials_file: str,
                               credentials_section: Optional[str] = None) -> Tuple[Optional[str], Optional[str],
                                                                                   Optional[str], Optional[str]]:
        if not credentials_section:
            credentials_section = "default"
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
        return region, access_key_id, secret_access_key, session_token
