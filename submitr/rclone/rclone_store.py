from __future__ import annotations
from abc import ABC as AbstractBaseClass, abstractmethod
import argparse
from contextlib import contextmanager
from datetime import datetime
import os
from shutil import copy as copy_file
import sys
from typing import Any, Callable, List, Optional, Union
from dcicutils.datetime_utils import parse_datetime
from dcicutils.misc_utils import create_uuid, normalize_string, PRINT
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_store_registry import RCloneStoreRegistry
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import DEBUGGING


class RCloneStore(AbstractBaseClass):

    # These prefix/proper-name properties are to be set by the classes derived from RCloneStore.
    # i.e. e.g. RCloneAmazon (where it is "s3://"), and RCloneGoogle (where it is "gs://").

    @classmethod
    @property
    @abstractmethod
    def prefix(cls) -> str:
        return None

    @classmethod
    @property
    @abstractmethod
    def proper_name(cls) -> str:
        return None

    @classmethod
    @property
    @abstractmethod
    def proper_name_title(cls) -> str:
        return None

    @classmethod
    @property
    @abstractmethod
    def proper_name_label(cls) -> str:
        return None

    def __init__(self,
                 name: Optional[str] = None,
                 credentials: Optional[Any] = None,
                 bucket: Optional[str] = None) -> None:
        self._name = normalize_string(name) or create_uuid()
        self._credentials = credentials
        # For the bucket property we allow not ONLY a bucket name but ANY "path", such as
        # they are (i.e. path-like) for cloud storage, i.e. a bucket name followed by an
        # optional sub-folder, e.g. gs://bucket/sub-folder. If set then will be prepended,
        # via cloud_path.path/join, to any path which is operated upon, e.g. for the
        # path_exists, file_size, file_checksum, and RCloner.copy functions.
        self._bucket = cloud_path.normalize(bucket) or None

    @property
    def name(self) -> str:
        if not self._name:
            self._name = create_uuid()
        return self._name

    @property
    def bucket(self) -> Optional[str]:
        return self._bucket

    def bucket_exists(self) -> Optional[bool]:
        """
        If this object does NOT have a bucket associated with it then returns None; otherwise returns True
        if that bucket exists, or False if it does not exist OR if it is a KEY (or if there is some other
        problem). As NOTED in the constructor, this "bucket" can actually be ANY path, which includes the
        bucket (of course) and an optional sub-folder.

        NOTE: If the bucket property for this cloud store object DOES contains a sub-folder, this ONLY
        returns True if that bucket/sub-folder in the cloud contains something, i.e. some key, or another
        sub-folder et cetera which EVENTUALLY contains some actual key; but this is fine for our purposes,
        where this function is (currently - in the RCloneStore implementations of the verify_connectivity
        function) used only to check that a given cloud source (for files to upload/transfer, i.e. via
        the --cloud-source option) exists; in this case we expect an actual/specific source key to exist,
        i.e. since we do not handle/allow copying (from) and entire bucket/folder.
        """
        if not (bucket := self.bucket):
            return None
        with self.config_file() as config_file:
            return RCloneCommands.exists_command(source=f"{self.name}:{bucket}", config=config_file)

    @property
    def credentials(self) -> Optional[Any]:
        return self._credentials

    @abstractmethod
    def config(self, checksum: bool = False) -> dict:
        return {}

    def config_lines(self) -> List[str]:
        lines = []
        if isinstance(config := self.config(), dict):
            lines.append(f"[{self.name}]")
            for key in config:
                if config[key] is not None:
                    lines.append(f"{key} = {config[key]}")
        return lines

    @contextmanager
    def config_file(self, persist: bool = False) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            os.chmod(temporary_config_file_name, 0o600)  # for security
            self.write_config_file(temporary_config_file_name, self.config_lines())
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

    def path(self, path: Optional[str], preserve_suffix: bool = False) -> Optional[str]:
        """
        Returns the given path prefixed/joined with any bucket defined in this cloud store object.
        If the preserve_suffix argument is True then any trailing slash will be preserved.
        """
        if path is None:
            path = ""
        elif not isinstance(path, str):
            return None
        return cloud_path.join(self.bucket, path, preserve_suffix=preserve_suffix)

    def display_path(self, path: Optional[str]) -> Optional[str]:
        if path := self.path(path):
            return f"{self.prefix}{path}"
        return None

    def is_path_bucket_only(self, path: str) -> bool:
        """
        Returns True iff the give path, prefixed/joined with any bucket defined
        in this cloud store object, represents just a bucket; iff this joined
        path has no slashes; otherwise returns False.
        """
        if path := self.path(path, preserve_suffix=True):
            if cloud_path.is_bucket_only(path):
                return True
        return False

    def is_path_folder(self, path: str) -> bool:
        """
        Returns True iff the give path, prefixed/joined with any bucket defined in this cloud
        store object, represents a folder, i.e. iff this joined path ends in a slash;
        otherwise returns False.
        """
        if path := self.path(path, preserve_suffix=True):
            if cloud_path.is_folder(path):
                return True
        return False

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
                # N.B. For AWS S3 keys with KMS encryption rclone hashsum md5 does not seem to work;
                # the command does not fail but returns no checksum (just the filename in the output);
                # removing the KMS info from the rclone config file fixes this, and it does return a
                # checksum value but it is not the same as the one we compute for the same file.
                # So not good, but for our use-cases so far it is of no consequence because at least
                # currently, although we do (as of June 2024) allow S3-to-S3 copy, we do not yet allow
                # the specification of a KMS Key ID for the source, and for the verify step after upload
                # to S3 we use boto3 to get the checksum (because we can as we have the targeted credentials).
                # Ror integration tests, we can just use AWS directly (via boto and our credentials).
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

    @staticmethod
    def register(cls):
        return RCloneStoreRegistry.register(cls)

    @staticmethod
    def from_args(cloud_source: Union[str, argparse.Namespace],
                  cloud_credentials: Optional[str] = None,
                  cloud_location: Optional[str] = None,
                  verify_installation: bool = True,
                  verify_connectivity: bool = True,
                  usage: Optional[Callable] = None,
                  printf: Optional[Callable] = None) -> Optional[RCloneStore]:
        """
        Generic function to create an instance/implementation for a RCloneStore,
        i.e. e.g. RCloneAmazon or RCloneGoogle, based on the given cloud_source
        which should be qualified path, i.e. like s3://bucket/key or gs://bucket/key.
        The cloud_credentials should be a path name to a credentials file (but FYI
        note not necessary if GCS and running on a Google Compute Engine (GCE)).
        """

        if isinstance(cloud_source, argparse.Namespace):
            # Initialize from actual command-line arguments.
            # Note the backward compatibility for the old/original --rclone-google-xyz options.
            args = cloud_source
            cloud_source = args.cloud_source or args.rclone_google_source
            cloud_credentials = cloud_credentials or args.cloud_credentials or args.rclone_google_credentials
            cloud_location = cloud_location or args.cloud_location or args.rclone_google_location

        if not (isinstance(cloud_source, str) and cloud_source):
            return None
        if not callable(usage):
            usage = PRINT
        if not callable(printf):
            printf = PRINT
        if (verify_installation is True) and not RCloneInstallation.verify_installation():
            usage(f"Cannot install rclone for some reason (contact support - sorry).")
            sys.exit(1)
        if cloud_store_class := RCloneStoreRegistry.lookup(cloud_source):
            return cloud_store_class.from_args(cloud_source=cloud_source,
                                               cloud_credentials=cloud_credentials,
                                               cloud_location=cloud_location,
                                               verify_connectivity=verify_connectivity,
                                               usage=usage,
                                               printf=printf)
        usage(f"Unknown cloud source specified: {cloud_source}")
        return None
