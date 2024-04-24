from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from typing import Optional
from uuid import uuid4 as create_uuid
from dcicutils.tmpfile_utils import temporary_file


class RCloneConfig(AbstractBaseClass):

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name

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

    @abstractproperty
    def config(self) -> dict:
        return {}

    @contextmanager
    def file(self) -> str:
        with temporary_file(suffix=".conf") as temporary_file_name:
            self.write_file(temporary_file_name)
            yield temporary_file_name

    def write_file(self, file: str) -> None:
        if (file := self._normalize_string_value(file)) is None:
            return
        if not isinstance(config := self.config, dict) or not config:
            return
        with open(file, "w") as f:
            f.write(f"[{self.name}]\n")
            for key in config:
                if config[key] is not None:
                    f.write(f"{key} = {config[key]}\n")

    @staticmethod
    def _normalize_string_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return ""
        elif isinstance(value, str):
            return value.strip()
        return None
