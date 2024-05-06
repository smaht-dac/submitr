from __future__ import annotations
import os
import pathlib
from typing import Callable, List, Optional, Union
from dcicutils.file_utils import get_file_size, search_for_file
from dcicutils.misc_utils import format_size
from dcicutils.structured_data import StructuredDataSet
from submitr.rclone import cloud_path, GoogleCredentials, RCloneConfigGoogle

# Unified the logic for looking for files to upload (to AWS S3), and storing
# related info; whether or not the file is coming from the local file system
# or from Google Cloud Storage (GCS), via rclone.

# TODO/QUESTION: If a file is found both locally and in GCS should we favor the
# local file (I think)? Should we warn/notify and/or solicit choice/confirmation?


class FileForUpload:

    @staticmethod
    def define(file: Union[str, pathlib.PosixPath, dict],
               main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
               main_search_directory_recursively: bool = False,
               other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
               google_source: Optional[str] = None,
               google_credentials: Optional[Union[GoogleCredentials, str]] = None) -> Optional[FileForUpload]:

        # Given file can be a dictionary (from structured_data.upload_files) like:
        # {"type": "ReferenceFile", "file": "first_file.fastq"}
        # Or a dictionary (from additional_data.upload_info of submission object) like:
        # {"uuid": "96f29020-7abd-4a42-b4c7-d342563b7074", "filename": "first_file.fastq"}
        # Or just a file name.
        file_type = None
        file_uuid = None
        if isinstance(file, dict):
            file_type = file.get("type")
            file_uuid = file.get("uuid")
            if not (file := file.get("file", file.get("filename", "")).strip()):
                return None
        if isinstance(file, (str, pathlib.PosixPath)):
            if not (file := os.path.normpath(os.path.basename(file.strip()))):
                return None

        local_path = None
        local_paths = None
        local_size = None
        file_paths = []

        if not isinstance(main_search_directory, (str, pathlib.PosixPath)) or not main_search_directory:
            main_search_directory = None

        if main_search_directory:
            # Actually, main_search_directory can also be a list (of str or PosixPath) of directories.
            file_paths = search_for_file(file,
                                         location=main_search_directory,
                                         recursive=main_search_directory_recursively is True)
        elif not isinstance(other_search_directories, list) or not other_search_directories:
            # Only if no main search directory specifed do we default the "other" search
            # directories to the current directory (.), if it is not otherwise specified.
            other_search_directories = ["."]

        if not isinstance(file_paths, list) or not file_paths:
            # Only look at other search directories if we have no yet found the file within the main
            # search directory; and if multiple instances of the file exist within/among these other
            # directories it doesn't matter; we just take the first one we find, with no flagging of
            # multiple files found. Unlike the case (above) of searching the main search directory
            # where (if recursive is specified) we will flag any multiple file instances found.
            # In practice these other directories are the directory containing
            # the submission file, and the current directory.
            if isinstance(other_search_directories, list) and other_search_directories:
                # Actually, other_search_directories can also be just a str and/or PosixPath.
                if file_path := search_for_file(file, location=other_search_directories, single=True, recursive=False):
                    file_paths = [file_path]

        if isinstance(file_paths, list) and file_paths:
            local_path = file_paths[0]
            local_size = get_file_size(local_path)
            if len(file_paths) > 1:
                local_paths = file_paths

        if isinstance(google_source, str):
            # We actually initialize Google related code lazily in FileForUpdate.google_path.
            pass

        file_for_upload = FileForUpload(name=file,
                                        type=file_type,
                                        uuid=file_uuid,
                                        main_search_directory=main_search_directory,
                                        local_path=local_path,
                                        local_paths=local_paths,
                                        local_size=local_size,
                                        google_source=google_source,
                                        google_credentials=google_credentials,
                                        _internal_use_only=True)
        return file_for_upload

    def __init__(self,
                 name: str,
                 type: Optional[str] = None,
                 uuid: Optional[str] = None,
                 main_search_directory: Optional[str] = None,
                 local_path: Optional[str] = None,
                 local_paths: Optional[List[str]] = None,
                 local_size: Optional[int] = None,
                 google_source: Optional[str] = None,
                 google_credentials: Optional[Union[GoogleCredentials, str]] = None,
                 _internal_use_only: bool = False) -> None:

        if not (_internal_use_only is True):
            raise Exception("Cannot create FileForUpload object directly; use FileForUpload.define")
        self._name = name.strip() if isinstance(name, str) else ""
        self._type = type if isinstance(type, str) else None
        self._uuid = uuid if isinstance(uuid, str) else None
        self._main_search_directory = main_search_directory if isinstance(main_search_directory, str) else None
        self._local_path = local_path if isinstance(local_path, str) else None
        self._local_paths = local_paths if isinstance(local_paths, list) else None
        self._local_size = local_size if isinstance(local_size, int) else None
        self._google_source = google_source if isinstance(google_source, str) else None
        if isinstance(google_credentials, GoogleCredentials):
            self._google_credentials = GoogleCredentials(google_credentials)
        elif isinstance(google_credentials, str):
            self._google_credentials = GoogleCredentials(service_account_file=google_credentials)
        else:
            self._google_credentials = None
        self._google_config = None
        self._google_tried_and_failed = False
        self._google_path = None
        self._google_size = None
        self._favor_local = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> Optional[str]:
        return self._type

    @property
    def uuid(self) -> Optional[str]:
        return self._uuid

    @property
    def main_search_directory(self) -> Optional[str]:
        return self._main_search_directory

    @property
    def found(self) -> bool:
        return self.local_path is not None or self.google_path is not None

    @property
    def found_locally(self) -> bool:
        return self.local_path is not None

    @property
    def found_locally_multiple(self) -> bool:
        return self.local_paths is not None

    @property
    def found_in_google(self) -> bool:
        return self.google_path is not None

    @property
    def path(self) -> Optional[str]:
        if self.found_locally:
            if self.found_in_google:
                if self._favor_local:
                    return self.local_path
                return self.google_path
            return self.local_path
        elif self.found_in_google:
            return self.google_path
        return None

    @property
    def path_for_display(self) -> Optional[str]:
        if self.found_locally:
            if self.found_in_google:
                if self._favor_local:
                    return self.local_path
                return self.google_path_for_display
            return self.local_path
        elif self.found_in_google:
            return self.google_path_for_display
        return None

    @property
    def local_path(self) -> Optional[str]:
        return self._local_path

    @property
    def local_paths(self) -> Optional[List[str]]:
        return self._local_paths

    @property
    def google_path(self) -> Optional[str]:
        if (self._google_path is None) and (not self._google_tried_and_failed):
            if self._google_source and (google_config := self.google_config):
                google_file = cloud_path.join(self._google_source, self.name)
                if (google_size := google_config.file_size(google_file)) is not None:
                    self._google_path = google_file
                    self._google_size = google_size
                else:
                    self._google_tried_and_failed = True
        return self._google_path

    @property
    def google_path_for_display(self) -> Optional[str]:
        if google_path := self.google_path:
            return f"gs://{google_path}"
        return None

    @property
    def size(self) -> Optional[int]:
        if self.found_locally:
            if self.found_in_google:
                if self._favor_local:
                    return self.local_size
                return self.google_size
            return self.local_size
        elif self.found_in_google:
            return self.google_size
        return None

    @property
    def local_size(self) -> Optional[int]:
        return self._local_size

    @property
    def google_size(self) -> Optional[int]:
        if self._google_size is None:
            # Initialize GSC related info.
            _ = self.google_path
        return self._google_size

    @property
    def google_credentials(self) -> Optional[GoogleCredentials]:
        return self._google_credentials

    @property
    def google_config(self) -> Optional[str]:
        if self._google_config is None:
            if google_credentials := self.google_credentials:
                self._google_config = RCloneConfigGoogle(google_credentials)
        return self._google_config

    def resume_upload_command(self, env: Optional[str] = None) -> str:
        return (f"resume-uploads{f' --env {env}' if isinstance(env, str) else ''}"
                f"{f' {self.uuid or self.name}' if self.uuid else ''}")

    def verify(self, verbose: bool = False, printf: Optional[Callable] = None) -> bool:
        if not self.found:
            printf(f"WARNING: Cannot find file for upload: {self.name} ({self.uuid})")
            return False
        elif self.found_in_google:
            if verbose:
                printf(f"File for upload to AWS S3: gs://{self.google_path} ({format_size(self.google_size)})")
            return True
        elif self.found_locally:
            if self.found_locally_multiple:
                printf(f"WARNING: Ignoring file for upload as multiple instances found: {self.name}")
                for local_path in self.local_paths:
                    print(f"- {local_path}")
                return False
            if verbose:
                printf(f"File for upload to AWS S3: {self.local_path} ({format_size(self.local_size)})")
                return True
            else:
                return False

    def __str__(self) -> str:  # for troubleshooting only
        return (
            f"name={self.name}|"
            f"found={self.found}|"
            f"path={self.path}|"
            f"size={self.size}|"
            f"found_locally={self.found_locally}|"
            f"found_locally_multiple={self.found_locally_multiple}|"
            f"found_in_google={self.found_in_google}|"
            f"local_path={self.local_path}|"
            f"local_paths={self.local_paths}|"
            f"local_size={self.local_size}|"
            f"google_path={self.google_path}|"
            f"google_size={self.google_size}")


class FilesForUpload:

    @staticmethod
    def define(files: Union[StructuredDataSet, List[str]],
               main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
               main_search_directory_recursively: bool = False,
               other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
               google_source: Optional[str] = None,
               google_credentials: Optional[Union[GoogleCredentials, str]] = None) -> List[FileForUpload]:

        if isinstance(files, StructuredDataSet):
            files = files.upload_files
        if not isinstance(files, list):
            return []

        files_for_upload = []
        for file in files:
            file_for_upload = FileForUpload.define(
                file,
                main_search_directory=main_search_directory,
                main_search_directory_recursively=main_search_directory_recursively,
                other_search_directories=other_search_directories,
                google_source=google_source,
                google_credentials=google_credentials)
            if file_for_upload:
                files_for_upload.append(file_for_upload)
        return files_for_upload

    @staticmethod
    def verify(files_for_upload: List[FileForUpload], verbose: bool = False, printf: Optional[Callable] = None) -> bool:
        if not callable(printf):
            printf = print
        result = True
        for file_for_upload in files_for_upload:
            if not file_for_upload.verify(verbose=verbose, printf=printf):
                result = False
        return result
