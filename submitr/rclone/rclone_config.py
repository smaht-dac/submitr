from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
import os
from shutil import copy as copy_file
from typing import List, Optional
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from dcicutils.misc_utils import create_uuid, normalize_string
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import DEBUGGING


class RCloneConfig(AbstractBaseClass):

    def __init__(self,
                 name: Optional[str] = None,
                 credentials: Optional[RCloneCredentials] = None,
                 bucket: Optional[str] = None) -> None:
        self._name = normalize_string(name) or create_uuid()
        self._credentials = credentials if isinstance(credentials, RCloneCredentials) else None
        # Here we allow not just a bucket name but any "path", such as they are (i.e. path-like),
        # beginning with a bucket name, within the cloud (S3, GCP) storage system. If set then
        # this will be prepended (via cloud_path.path/join) to any path which is operated upon,
        # e.g. for the path_exists, file_size, file_checksum, and RCloner.copy functions.
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

    def bucket_exists(self) -> Optional[bool]:
        """
        If this object does not have  a bucket associated with it then returns None;
        otherwise returns True if that bucket exists or False if it does not (or some other problem).
        """
        if not (bucket := self.bucket):
            return None
        with self.config_file() as config_file:
            return RCloneCommands.exists_command(source=f"{self.name}:{bucket}", config=config_file)

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
            os.chmod(temporary_config_file_name, 0o600)  # for security
            self.write_config_file(temporary_config_file_name, self.config_lines)
            if (persist is True) or DEBUGGING():
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                os.chmod(persistent_config_file_name, 0o600)  # for security
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    @staticmethod
    def write_config_file(file: str, lines: List[str]) -> None:
        if (file := normalize_string(file)) is None:
            return
        if not isinstance(lines, list) or not lines:
            return
        with open(file, "w") as f:
            for line in lines:
                f.write(f"{line}\n")

    def path(self, path: str) -> Optional[str]:
        if isinstance(path, str) or path is None:
            # Sic: Not cloud_path.normalize above as, so long as the given path
            # is a string or None allow, it to be joined with any defined bucket.
            return cloud_path.join(self.bucket, path)
        return None

    def path_exists(self, path: str) -> Optional[bool]:
        # N.B. For AWS S3 rclone ls requires policies s3:GetObject and s3:ListBucket
        # for the bucket/key. So for our main use case (using Portal-granted temporary
        # credentials to copy to AWS S3, which only have s3:PutObject and s3:GetObject
        # policies) this will NOT work. See submitr.s3_upload for special handling.
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.exists_command(source=f"{self.name}:{path}", config=config_file)
        return False

    def file_size(self, path: str) -> Optional[int]:
        # N.B. For AWS S3 rclone size requires policies s3:GetObject and s3:ListBucket
        # for the bucket/key. So for our main use case (using Portal-granted temporary
        # credentials to copy to AWS S3, which only have s3:PutObject and s3:GetObject
        # policies) this will NOT work. See submitr.s3_upload for special handling.
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.size_command(source=f"{self.name}:{path}", config=config_file)
        return None

    def file_checksum(self, path: str) -> Optional[str]:
        # N.B. For AWS S3 rclone hashsum requires policies s3:GetObject and s3:ListBucket
        # for the bucket/key. So for our main use case (using Portal-granted temporary
        # credentials to copy to AWS S3, which only have s3:PutObject and s3:GetObject
        # policies) this will NOT work. See submitr.s3_upload for special handling.
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.checksum_command(source=f"{self.name}:{path}", config=config_file)

    def ping(self) -> bool:
        # For some reason with this command we need the project_number in the config for Google.
        with self.config_file() as config_file:
            return RCloneCommands.ping_command(source=f"{self.name}:", config=config_file)

    def __eq__(self, other: Optional[RCloneConfig]) -> bool:
        return (isinstance(other, RCloneConfig) and
                (self.name == other.name) and
                (self.bucket == other.bucket) and
                (self.credentials == other.credentials))

    def __ne__(self, other: Optional[RCloneConfig]) -> bool:
        return not self.__eq__(other)


class RCloneCredentials(AbstractBaseClass):
    pass
