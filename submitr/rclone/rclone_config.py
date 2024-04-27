from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from shutil import copy as copy_file
from typing import List, Optional
from uuid import uuid4 as create_uuid
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file


class RCloneConfig(AbstractBaseClass):

    def __init__(self, name: Optional[str] = None, bucket: Optional[str] = None) -> None:
        self._name = self._normalize_string_value(name) or create_uuid()
        self._bucket = self._normalize_string_value(bucket) or None

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
    def bucket(self) -> Optional[str]:
        return self._bucket

    @bucket.setter
    def bucket(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._bucket = value or None

    @abstractproperty
    def config(self) -> dict:
        return {}

    @property
    def config_lines(self) -> List[str]:
        lines = []
        if isinstance(config := self.config, dict):
            lines.append(f"[{self.name}]")
            for key in self.config:
                if config[key] is not None:
                    lines.append(f"{key} = {config[key]}")
        return lines

    @contextmanager
    def config_file(self, persist_file: bool = False) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            self.write_config_file(temporary_config_file_name)
            if persist_file is True:
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    def write_config_file(self, file: str) -> None:
        self._write_config_file_lines(file, self.config_lines)

    @staticmethod
    def _write_config_file_lines(file: str, lines: List[str]) -> None:
        if (file := RCloneConfig._normalize_string_value(file)) is None:
            return
        if not isinstance(lines, list) or not lines:
            return
        with open(file, "w") as f:
            for line in lines:
                f.write(f"{line}\n")

    @staticmethod
    def _normalize_string_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip()
        return None
