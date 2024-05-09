from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from shutil import copy as copy_file
from typing import List, Optional
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from dcicutils.misc_utils import create_uuid, normalize_string
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_utils import cloud_path


class RCloneConfig(AbstractBaseClass):

    def __init__(self,
                 name: Optional[str] = None,
                 credentials: Optional[RCloneCredentials] = None,
                 bucket: Optional[str] = None) -> None:
        self._name = normalize_string(name) or create_uuid()
        self._credentials = credentials if isinstance(credentials, RCloneCredentials) else None
        # We allow here not just a bucket name but any "path", such as they are (i.e. path-like),
        # beginning with a bucket name, within the cloud (S3, GCP) storage system. If set then
        # this will be prepended (via cloud_path.join) to any path which is operated upon,
        # e.g. for the path_exists, file_size, file_checksum, and RClone.copy functions.
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

    @property
    def credentials(self) -> RCloneCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: RCloneCredentials) -> None:
        if isinstance(value, RCloneCredentials):
            self._credentials = value

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
    def config_file(self, persist: bool = False) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            self.write_config_file_lines(temporary_config_file_name, self.config_lines)
            if persist is True:
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    @staticmethod
    def write_config_file_lines(file: str, lines: List[str]) -> None:
        if (file := normalize_string(file)) is None:
            return
        if not isinstance(lines, list) or not lines:
            return
        with open(file, "w") as f:
            for line in lines:
                f.write(f"{line}\n")

    def path(self, path: str) -> Optional[str]:
        if path := cloud_path.normalize(path):
            return cloud_path.join(self.bucket, path)
        return None

    def path_exists(self, path: str) -> Optional[bool]:
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.exists_command(
                    source=f"{self.name}:{path}", config=config_file)
        return False

    def file_size(self, path: str) -> Optional[int]:
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.size_command(
                    source=f"{self.name}:{path}", config=config_file)
        return None

    def file_checksum(self, path: str) -> Optional[str]:
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.checksum_command(
                    source=f"{self.name}:{path}", config=config_file)

    def ping(self) -> bool:
        # For some reason with this command we need the project_number in the config for Google.
        with self.config_file() as config_file:
            return RCloneCommands.ping_command(source=f"{self.name}:", config=config_file)

    def __eq__(self, other: RCloneConfig) -> bool:
        return (isinstance(other, RCloneConfig) and
                (self.name == other.name) and
                (self.bucket == other.bucket) and
                (self.credentials == other.credentials))

    def __ne__(self, other: RCloneConfig) -> bool:
        return not self.__eq__(other)


class RCloneCredentials(AbstractBaseClass):
    pass
