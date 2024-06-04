from __future__ import annotations
from boto3 import client as BotoClient
import configparser
import os
from typing import Optional, Tuple, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import normalize_string


class AmazonCredentials:

    def __init__(self,
                 credentials: Optional[Union[AmazonCredentials, str]] = None,
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
            self._account_number = credentials._account_number
        elif credentials := normalize_path(credentials, expand_home=True):
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

    def to_dictionary(self, environment_names: bool = True) -> dict:
        if environment_names is True:
            result = {
                "AWS_ACCESS_KEY_ID": self.access_key_id,
                "AWS_SECRET_ACCESS_KEY": self.secret_access_key
            }
            if session_token := self.session_token:
                result["AWS_SESSION_TOKEN"] = session_token
            if region := self.region:
                result["AWS_DEFAULT_REGION_NAME"] = region
        else:
            result = {
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key
            }
            if session_token := self.session_token:
                result["aws_session_token"] = session_token
            if region := self.region:
                result["region_name"] = region
        return result

    def ping(self) -> bool:
        try:
            sts = BotoClient("sts",
                             region_name=self.region,
                             aws_access_key_id=self.access_key_id,
                             aws_secret_access_key=self.secret_access_key,
                             aws_session_token=self.session_token)
            _ = sts.get_caller_identity()
            return True
        except Exception:
            return False

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
    def obtain(credentials_file: Optional[str] = None,
               region: Optional[str] = None,
               access_key_id: Optional[str] = None,
               secret_access_key: Optional[str] = None,
               session_token: Optional[str] = None,
               kms_key_id: Optional[str] = None,
               credentials_section: Optional[str] = None,
               ignore_environment_variables: bool = False) -> Optional[AmazonCredentials]:

        aws_region = aws_access_key_id = aws_secret_access_key = aws_session_token = None
        if credentials_file := normalize_path(credentials_file, expand_home=True):
            if os.path.isdir(credentials_file):
                credentials_file = os.path.join(credentials_file, "credentials")
            if not os.path.isfile(credentials_file):
                return None
            aws_region, aws_access_key_id, aws_secret_access_key, aws_session_token = (
                AmazonCredentials._read_credentials_file(credentials_file, credentials_section=credentials_section))
        elif ((ignore_environment_variables is not True) and
              (credentials_file := normalize_path(
                  os.environ.get("AWS_SHARED_CREDENTIALS_FILE", os.environ.get("AWS_CONFIG_FILE")), expand_home=True))):
            if not os.path.isfile(credentials_file):
                return None
            aws_region, aws_access_key_id, aws_secret_access_key, aws_session_token = (
                AmazonCredentials._read_credentials_file(credentials_file, credentials_section=credentials_section))
        elif ignore_environment_variables is not True:
            aws_region, aws_access_key_id, aws_secret_access_key, aws_session_token = (
                AmazonCredentials._read_environment_variables())
        if region := normalize_string(region):
            aws_region = region
        if access_key_id := normalize_string(access_key_id):
            aws_access_key_id = access_key_id
        if secret_access_key := normalize_string(secret_access_key):
            aws_secret_access_key = secret_access_key
        if session_token := normalize_string(session_token):
            aws_session_token = session_token
        if not (aws_access_key_id and aws_secret_access_key):
            return None
        return AmazonCredentials(
             region=aws_region,
             access_key_id=aws_access_key_id,
             secret_access_key=aws_secret_access_key,
             session_token=aws_session_token,
             kms_key_id=kms_key_id)

    @staticmethod
    def _read_credentials_file(credentials_file: str,
                               credentials_section: Optional[str] = None) -> Tuple[Optional[str], Optional[str],
                                                                                   Optional[str], Optional[str]]:
        noresult = (None, None, None, None)
        if not (credentials_file := normalize_path(credentials_file, expand_home=True)):
            return noresult
        if os.path.isdir(credentials_file):
            credentials_file = os.path.join(credentials_file, "credentials")
        if not os.path.isfile(credentials_file):
            return noresult
        config = configparser.ConfigParser()
        try:
            config.read(credentials_file)
        except configparser.MissingSectionHeaderError:
            # Allow a credentials file with no section header just because.
            try:
                with open(credentials_file) as f:
                    config.read_string("[default]\n" + f.read())
            except Exception:
                return noresult
        except Exception:
            return noresult
        try:
            if credentials_section := normalize_string(credentials_section):
                if credentials_section not in config:
                    return noresult
                credentials_section = config[credentials_section]
            elif "default" in config:
                credentials_section = config["default"]
            elif len(config.sections()) > 0:
                credentials_section = config[config.sections()[0]]
            else:
                return noresult
            region = (credentials_section.get("region", None) or
                      credentials_section.get("region_name", None) or
                      credentials_section.get("aws_default_region", None))
            access_key_id = (credentials_section.get("aws_access_key_id", None) or
                             credentials_section.get("access_key_id", None))
            secret_access_key = (credentials_section.get("aws_secret_access_key", None) or
                                 credentials_section.get("secret_access_key", None))
            session_token = (credentials_section.get("aws_session_token", None) or
                             credentials_section.get("session_token", None))
            return region, access_key_id, secret_access_key, session_token
        except Exception:
            return noresult

    @staticmethod
    def _read_environment_variables() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", None))
        access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        session_token = os.environ.get("AWS_SESSION_TOKEN", None)
        return region, access_key_id, secret_access_key, session_token
