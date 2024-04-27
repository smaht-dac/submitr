from __future__ import annotations
from boto3 import client as BotoClient
from datetime import timedelta
from json import dumps as dump_json
from typing import Optional, Union
from uuid import uuid4 as create_uuid
from dcicutils.misc_utils import create_dict
from submitr.rclone.rclone_config import RCloneConfig


class RCloneConfigAmazon(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[AmazonCredentials, RCloneConfigAmazon]] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 name: Optional[str] = None, bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneConfigAmazon):
            name = RCloneConfig._normalize_string_value(name) or credentials_or_config.name
            bucket = RCloneConfig._normalize_string_value(bucket) or credentials_or_config.bucket
            credentials = None
        elif isinstance(credentials_or_config, AmazonCredentials):
            credentials = credentials_or_config
        else:
            credentials = None

        super().__init__(name=name, bucket=bucket)
        self._credentials = AmazonCredentials(credentials=credentials,
                                              region=region,
                                              access_key_id=access_key_id,
                                              secret_access_key=secret_access_key,
                                              session_token=session_token,
                                              kms_key_id=kms_key_id)

    @property
    def credentials(self) -> AmazonCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: AmazonCredentials) -> None:
        if isinstance(value, AmazonCredentials):
            self._credentials = value

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
        return ((self.name == other.name) and
                (self.bucket == other.bucket) and
                (self.credentials == other.credentials))

    def __ne__(self, other: RCloneConfigAmazon) -> bool:
        return self.__eq__(other)

    @property
    def config(self) -> dict:
        return create_dict(provider="AWS",
                           type="s3",
                           access_key_id=self.access_key_id,
                           secret_access_key=self.secret_access_key,
                           session_token=self.session_token,
                           sse_kms_key_id=self.kms_key_id,
                           server_side_encryption="aws:kms" if self.kms_key_id else None)


class AmazonCredentials:

    @staticmethod
    def create(*args, **kwargs) -> AmazonCredentials:
        return AmazonCredentials(*args, **kwargs)

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
        else:
            self._region = None
            self._access_key_id = None
            self._secret_access_key = None
            self._session_token = None
            self._kms_key_id = None

        if region := RCloneConfig._normalize_string_value(region):
            self._region = region
        if access_key_id := RCloneConfig._normalize_string_value(access_key_id):
            self._access_key_id = access_key_id
        if secret_access_key := RCloneConfig._normalize_string_value(secret_access_key):
            self._secret_access_key = secret_access_key
        if session_token := RCloneConfig._normalize_string_value(session_token):
            self._session_token = session_token
        if kms_key_id := RCloneConfig._normalize_string_value(kms_key_id):
            self._kms_key_id = kms_key_id

    @property
    def region(self) -> Optional[str]:
        return self._region

    @region.setter
    def region(self, value: Optional[str]) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._region = value or None

    @property
    def access_key_id(self) -> Optional[str]:
        return self._access_key_id

    @access_key_id.setter
    def access_key_id(self, value: Optional[str]) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._access_key_id = value or None

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value: Optional[str]) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._secret_access_key = value or None

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    @session_token.setter
    def session_token(self, value: Optional[str]) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._session_token = value or None

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @kms_key_id.setter
    def kms_key_id(self, value: Optional[str]) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._kms_key_id = value or None

    def __eq__(self, other: AmazonCredentials) -> bool:
        return ((self.region == other.region) and
                (self.access_key_id == other.access_key_id) and
                (self.secret_access_key == other.secret_access_key) and
                (self.session_token == other.session_token) and
                (self.kms_key_id == other.kms_key_id))

    def __ne__(self, other: AmazonCredentials) -> bool:
        return self.__eq__(other)

    def generate_temporary_credentials(self,
                                       duration: Optional[Union[int, timedelta]] = None,
                                       policy: Optional[dict] = None,
                                       raise_exception: bool = True) -> Optional[AmazonCredentials]:
        """
        Generates and returns temporary AWS credentials. The default duration of validity
        for the generated credential is one hour; this can be overridden by specifying
        the duration argument (which is in seconds). By default the generated credentials
        will have the same permissions as the credentials of this (self) AmazonCredentials
        object; this can be changed by passing in an AWS policy object (dictionary).
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

        sts = BotoClient("sts",
                         aws_access_key_id=self.access_key_id,
                         aws_secret_access_key=self.secret_access_key,
                         aws_session_token=self.session_token)

        name = f"test.smaht.submitr.{self._create_short_unique_identifier()}"
        try:
            if policy:
                response = sts.get_federation_token(Name=name, DurationSeconds=duration, Policy=policy)
            else:
                response = sts.get_federation_token(Name=name, DurationSeconds=duration)
            if isinstance(credentials := response.get("Credentials"), dict):
                return AmazonCredentials(
                    access_key_id=credentials.get("AccessKeyId"),
                    secret_access_key=credentials.get("SecretAccessKey"),
                    session_token=credentials.get("SessionToken"),
                    kms_key_id=self.kms_key_id)
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def _create_short_unique_identifier(length: int = 13):
        return create_uuid().hex[:length]
