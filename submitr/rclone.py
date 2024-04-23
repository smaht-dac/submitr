from __future__ import annotations
from enum import Enum
from typing import Optional
from submitr.rclone_installation import install_rclone_executable, rclone_executable_exists


class RClone:

    def __init___(self) -> None:
        self._source = None
        self._destination = None
        pass

    @property
    def source(self) -> RCloneConfig:
        return self._source

    @source.setter
    def source(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig):
            self._source = value

    @property
    def destination(self) -> destination:
        return self._destination

    @destination.setter
    def destination(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig):
            self._destination = value

    def copy(source: str, destination: str, raise_exception: bool = False) -> bool:
        return False

    @staticmethod
    def install(force_update: bool = True) -> bool:
        if not rclone_executable_exists() or force_update:
            return install_rclone_executable()
        return True


class RCloneConfig:

    class Type(Enum):
        LOCAL = "local"
        AMAZON_S3 = "s3"
        GOOGLE_CLOUD_STORAGE = "google cloud storage"

    def __init__(self) -> None:
        self._config = {}
        pass

    def set_name(self, value: Optional[str]) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("name", None)
            else:
                self._config["name"] = value
        return self

    def set_type(self, value: Optional[RCloneConfig.Type]) -> RCloneConfig:
        if value is None:
            self._config.pop("type", None)
            self._config.pop("provider", None)
        elif isinstance(value, RCloneConfig.Type):
            self._config["type"] = value.value
            if value == RCloneConfig.Type.AMAZON_S3:
                self._config["provider"] = "aws"
            else:
                self._config.pop("provider", None)
        return self

    def set_region(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("region", None)
            else:
                self._config["region"] = value
        return self

    def set_aws_access_key_id(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_access_key_id", None)
            else:
                self._config["aws_access_key_id"] = value
        return self

    def set_aws_secret_access_key(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_secret_access_key", None)
            else:
                self._config["aws_secret_access_key"] = value
        return self

    def set_aws_session_token(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_session_token", None)
            else:
                self._config["aws_session_token"] = value
        return self

    def set_aws_kms_key_id(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_kms_key_id", None)
            else:
                self._config["aws_kms_key_id"] = value
        return self

    def set_google_service_account_file(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("google_service_account_file", None)
            else:
                self._config["google_service_account_file"] = value
        return self

    @staticmethod
    def _normalize_string_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip()
        return None
