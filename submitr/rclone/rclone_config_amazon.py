from typing import Optional
from dcicutils.misc_utils import create_dict
from submitr.rclone.rclone_config import RCloneConfig


class RCloneConfigAmazon(RCloneConfig):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._region = None
        self._access_key_id = None
        self._secret_access_key = None
        self._session_token = None
        self._kms_key_id = None
        self._bucket = None

    @property
    def region(self) -> Optional[str]:
        return self._region

    @region.setter
    def region(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._region = value or None

    @property
    def access_key_id(self) -> Optional[str]:
        return self._access_key_id

    @access_key_id.setter
    def access_key_id(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._access_key_id = value or None

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._secret_access_key = value or None

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    @session_token.setter
    def session_token(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._session_token = value or None

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @kms_key_id.setter
    def kms_key_id(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._kms_key_id = value or None

    @property
    def bucket(self) -> Optional[str]:
        return self._bucket

    @bucket.setter
    def bucket(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._bucket = value or None

    @property
    def config(self) -> dict:
        return create_dict(provider="AWS",
                           type="s3",
                           access_key_id=self.access_key_id,
                           secret_access_key=self.secret_access_key,
                           session_token=self.session_token,
                           kms_key_id=self.kms_key_id)
