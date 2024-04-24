from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from typing import List, Optional
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
    def config_file(self) -> str:
        with temporary_file(suffix=".conf") as temporary_file_name:
            self.write_config_file(temporary_file_name)
            yield temporary_file_name

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
