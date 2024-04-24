from __future__ import annotations
from contextlib import contextmanager
from enum import Enum
from typing import Optional
from uuid import uuid4 as create_uuid
from dcicutils.tmpfile_utils import temporary_file
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

    def copy(source_file: str, destination_file: str, raise_exception: bool = False) -> bool:
        # TODO
        # Use copyto instead of copy to copy to specified file name.
        return False

    @staticmethod
    def install(force_update: bool = True) -> bool:
        if not rclone_executable_exists() or force_update:
            return install_rclone_executable()
        return True


class RCloneConfig:

    class Type(Enum):
        AMAZON_S3 = "s3"
        GOOGLE_CLOUD_STORAGE = "google cloud storage"
        LOCAL = "local"
        UNDEFINED = "undefined"

    def __init__(self) -> None:
        self._name = ""
        self._type = RCloneConfig.Type.UNDEFINED
        self._config = {}
        pass

    @contextmanager
    def config_file(self) -> str:
        with temporary_file(suffix=".config") as temporary_file_name:
            self.write_config_file(temporary_file_name)
            yield temporary_file_name

    def write_config_file(self, file: str) -> bool:
        if (file := self._normalize_string_value(file)) is not None:
            with open(file, "w") as f:
                f.write(self._lines(
                    f"[{self.name}]",
                    f"provider = AWS",
                    f"type = s3",
                    f"access_key_id = {self.aws_access_key_id}" if self.aws_access_key_id else None,
                    f"secret_access_key = {self.aws_secret_access_key}" if self.aws_secret_access_key else None
                ))
                return True
        return False

    @property
    def name(self) -> str:
        if not self._name:
            self._name = create_uuid()
        return self._name

    @name.setter
    def name(self, value: Optional[str]) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._name = create_uuid()
            else:
                self._name = value

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: RCloneConfig.Type) -> None:
        if value is None:
            self._config.pop("type", None)
            self._config.pop("provider", None)
        elif isinstance(value, RCloneConfig.Type):
            self._config["type"] = value.value
            if value == RCloneConfig.Type.AMAZON_S3:
                self._config["provider"] = "aws"
            else:
                self._config.pop("provider", None)

    @property
    def region(self) -> Optional[str]:
        return self._config.get("region")

    @region.setter
    def region(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("region", None)
            else:
                self._config["region"] = value

    @property
    def aws_access_key_id(self) -> Optional[str]:
        return self._config.get("aws_access_key_id", None)

    @aws_access_key_id.setter
    def aws_access_key_id(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_access_key_id", None)
            else:
                self._config["aws_access_key_id"] = value

    @property
    def aws_secret_access_key(self) -> Optional[str]:
        return self._config.get("aws_secret_access_key", None)

    @aws_secret_access_key.setter
    def aws_secret_access_key(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_secret_access_key", None)
            else:
                self._config["aws_secret_access_key"] = value

    @property
    def aws_session_token(self, value: str) -> Optional[str]:
        return self._config.get("aws_session_token", None)

    @aws_session_token.setter
    def aws_session_token(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_session_token", None)
            else:
                self._config["aws_session_token"] = value

    @property
    def aws_kms_key_id(self, value: str) -> Optional[str]:
        return self._config.get("aws_kms_key_id", None)

    @aws_kms_key_id.setter
    def aws_kms_key_id(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            if not value:
                self._config.pop("aws_kms_key_id", None)
            else:
                self._config["aws_kms_key_id"] = value

    @property
    def google_service_account_file(self) -> Optional[str]:
        return self._config.get("google_service_account_file", None)

    @google_service_account_file.setter
    def google_service_account_file(self, value: str) -> RCloneConfig:
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

    @staticmethod
    def _lines(*args) -> str:
        result = ""
        for arg in args:
            if isinstance(arg, str) and arg:
                result += f"{arg}\n"
        return result
