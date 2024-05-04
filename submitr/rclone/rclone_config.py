from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from shutil import copy as copy_file
from typing import List, Optional
from uuid import uuid4 as create_uuid
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from dcicutils.misc_utils import normalize_string
from submitr.rclone.rclone_utils import cloud_path


class RCloneConfig(AbstractBaseClass):

    def __init__(self, name: Optional[str] = None, bucket: Optional[str] = None) -> None:
        self._name = normalize_string(name) or create_uuid()
        self._bucket = cloud_path.normalize(bucket)

    @property
    def name(self) -> str:
        if not self._name:
            self._name = create_uuid()
        return self._name

    @name.setter
    def name(self, value: Optional[str]) -> None:
        if (value := normalize_string(value)) is not None:
            if not value:
                self._name = create_uuid()
            else:
                self._name = value

    @property
    def bucket(self) -> Optional[str]:
        return self._bucket

    @bucket.setter
    def bucket(self, value: str) -> None:
        if (value := cloud_path.normalize(value)) is not None:
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
    def config_file(self, persist: bool = False, extra_lines: Optional[List[str]] = None) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            self.write_config_file(temporary_config_file_name, extra_lines=extra_lines)
            if persist is True:
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    def write_config_file(self, file: str, extra_lines: Optional[List[str]] = None) -> None:
        self._write_config_file_lines(file, self.config_lines, extra_lines=extra_lines)

    @staticmethod
    def _write_config_file_lines(file: str, lines: List[str], extra_lines: Optional[List[str]] = None) -> None:
        if (file := normalize_string(file)) is None:
            return
        if not isinstance(lines, list) or not lines:
            return
        with open(file, "w") as f:
            for line in lines:
                f.write(f"{line}\n")
            if isinstance(extra_lines, list):
                for extra_line in extra_lines:
                    f.write(f"{extra_line}\n")
