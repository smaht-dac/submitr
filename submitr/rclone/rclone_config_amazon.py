from __future__ import annotations
from boto3 import client as BotoClient
from typing import Optional, Union
from dcicutils.misc_utils import create_dict, normalize_string
from submitr.rclone.rclone_config import RCloneConfig, RCloneCredentials
from submitr.rclone.rclone_utils import cloud_path


class RCloneConfigAmazon(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[AmazonCredentials, RCloneConfigAmazon]] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 name: Optional[str] = None,
                 bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneConfigAmazon):
            name = normalize_string(name) or credentials_or_config.name
            bucket = cloud_path.normalize(bucket) or credentials_or_config.bucket
            credentials = credentials_or_config.credentials
        elif isinstance(credentials_or_config, AmazonCredentials):
            credentials = credentials_or_config
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

    @credentials.setter
    def credentials(self, value: AmazonCredentials) -> None:
        if isinstance(value, AmazonCredentials):
            super().credentials = value

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

    @region.setter
    def region(self, value: str) -> None:
        self._credentials.region = value

    @property
    def access_key_id(self) -> Optional[str]:
        return self._credentials.access_key_id

    @access_key_id.setter
    def access_key_id(self, value: str) -> None:
        self._credentials.access_key_id = value

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._credentials.secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value: str) -> None:
        self._credentials.secret_access_key = value

    @property
    def session_token(self) -> Optional[str]:
        return self._credentials.session_token

    @session_token.setter
    def session_token(self, value: str) -> None:
        self._credentials.session_token = value

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._credentials.kms_key_id

    @kms_key_id.setter
    def kms_key_id(self, value: str) -> None:
        self._credentials.kms_key_id = value

    def __eq__(self, other: RCloneConfigAmazon) -> bool:
        return isinstance(other, RCloneConfigAmazon) and super().__eq__(other)

    def __ne__(self, other: RCloneConfigAmazon) -> bool:
        return not self.__eq__(other)


class AmazonCredentials(RCloneCredentials):

    def __init__(self,
                 credentials: Optional[AmazonCredentials] = None,
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

    @region.setter
    def region(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            self._region = value or None

    @property
    def access_key_id(self) -> Optional[str]:
        return self._access_key_id

    @access_key_id.setter
    def access_key_id(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            self._access_key_id = value or None

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            self._secret_access_key = value or None

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    @session_token.setter
    def session_token(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            self._session_token = value or None

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @kms_key_id.setter
    def kms_key_id(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            self._kms_key_id = value or None

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

    def to_dict(self) -> dict:
        return {
            "region_name": self.region,
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
            "aws_session_token": self.session_token
        }

    def __eq__(self, other: AmazonCredentials) -> bool:
        return ((self.region == other.region) and
                (self.access_key_id == other.access_key_id) and
                (self.secret_access_key == other.secret_access_key) and
                (self.session_token == other.session_token) and
                (self.kms_key_id == other.kms_key_id))

    def __ne__(self, other: AmazonCredentials) -> bool:
        return self.__eq__(other)
