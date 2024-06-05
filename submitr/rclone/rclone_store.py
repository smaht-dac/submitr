from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractproperty
from contextlib import contextmanager
from datetime import datetime
import os
from shutil import copy as copy_file
from typing import Any, Callable, List, Optional, Union
from dcicutils.datetime_utils import parse_datetime
from dcicutils.misc_utils import create_uuid, normalize_string, PRINT
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import DEBUGGING


class RCloneStore(AbstractBaseClass):

    # This prefix class variable is to be set by the classes derived from RCloneStore.
    # i.e. RCloneAmazon (where it is "s3://"), and RCloneGoogle (where it is "gs://").
    prefix = None
    proper_name = None
    proper_name_title = None

    def __init__(self,
                 name: Optional[str] = None,
                 credentials: Optional[Any] = None,
                 bucket: Optional[str] = None) -> None:
        self._name = normalize_string(name) or create_uuid()
        self._credentials = credentials
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
        If this object does not have a bucket associated with it then returns None;
        otherwise returns True if that bucket exists or False if it does not (or some other problem).
        As noted in constructor, this "bucket" can actually be any path (which includes the bucket of course).
        And NOTE: If the bucket/path is just a folder, this ONLY returns True if it contains something.
        """
        if not (bucket := self.bucket):
            return None
        with self.config_file() as config_file:
            return RCloneCommands.exists_command(source=f"{self.name}:{bucket}", config=config_file)

    @property
    def credentials(self) -> Optional[Any]:
        return self._credentials

    @credentials.setter
    def credentials(self, value: Optional[Any]) -> None:
        if value:
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
        if path is None:
            path = ""
        if isinstance(path, str):
            if path.lower()[0:5] in [cloud_path.google_prefix, cloud_path.amazon_prefix]:
                path = path[5:]
            # Sic: Not cloud_path.normalize above as, so long as the given path
            # is a string or None allow, it to be joined with any defined bucket.
            return cloud_path.join(self.bucket, path)
        return None

    def display_path(self, path: str) -> Optional[str]:
        if path := self.path(path):
            return f"{self.prefix}{path}"
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

    def file_exists(self, path: str) -> Optional[bool]:
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.file_exists_command(source=f"{self.name}:{path}", config=config_file)
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

    def file_modified(self, path: str, formatted: bool = False) -> Optional[Union[datetime, str]]:
        if info := self.file_info(path):
            if not (formatted is True):
                return parse_datetime(info.get("modified"))
            return info.get("modified")

    def file_info(self, path: str) -> Optional[str]:
        if path := self.path(path):
            with self.config_file() as config_file:
                return RCloneCommands.info_command(source=f"{self.name}:{path}", config=config_file)

    def ping(self) -> bool:
        # For some reason with this command we need the project_number in the config for Google.
        with self.config_file() as config_file:
            return RCloneCommands.ping_command(source=f"{self.name}:", config=config_file)

    def __eq__(self, other: Optional[RCloneStore]) -> bool:
        return (isinstance(other, RCloneStore) and
                (self.name == other.name) and
                (self.bucket == other.bucket) and
                (self.credentials == other.credentials))

    def __ne__(self, other: Optional[RCloneStore]) -> bool:
        return not self.__eq__(other)

    _registered_cloud_stores = []

    @staticmethod
    def register(cls):
        RCloneStore._registered_cloud_stores.append(cls)
        return cls

    @staticmethod
    def from_args(cloud_source: str,
                  cloud_credentials: Optional[str] = None,
                  cloud_location: Optional[str] = None,
                  verify_installation: bool = True,
                  verify_connectivity: bool = True,
                  printf: Optional[Callable] = None) -> Optional[RCloneStore]:

        # We could get fancy here and use decorators for RCloneAmazon and RCloneGoogle
        # et cetera to programmaticaly get the specific RCloneStore instance based on the
        # prefix of the cloud storage object specified; but at the moment doesn't seem worth it.
        # TODO: Actually need to do the decorator thing if we don't want circular imports, or something else ...
        # cloud_store = None
        # if cloud_path.is_amazon(args.rclone_google_source):
        #     cloud_store = RCloneAmazon.from_command_args(args.rclone_google_source,
        #                                                  args.rclone_google_credentials,
        #                                                  args.rclone_google_location)
        # elif cloud_path.is_google(args.rclone_google_source) or args.rclone_google_source:
        #     cloud_store = RCloneGoogle.from_command_args(args.rclone_google_source,
        #                                                  args.rclone_google_credentials,
        #                                                  args.rclone_google_location)

        if not (isinstance(cloud_source, str) and cloud_source):
            return None
        if not callable(printf):
            printf = PRINT
        if (verify_installation is True) and not RCloneInstallation.verify_installation():
            printf(f"ERROR: Cannot install rclone for some reason (contact support).")
            exit(1)
        for cloud_store_class in RCloneStore._registered_cloud_stores:
            if cloud_source.lower().startswith(cloud_store_class.prefix.lower()):
                return cloud_store_class.from_args(cloud_source=cloud_source,
                                                   cloud_credentials=cloud_credentials,
                                                   cloud_location=cloud_location,
                                                   verify_connectivity=verify_connectivity,
                                                   printf=printf)
        return None
