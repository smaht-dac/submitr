from __future__ import annotations
import os
import pathlib
from typing import List, Optional, Union
from dcicutils.file_utils import get_file_size, search_for_file
from dcicutils.structured_data import StructuredDataSet
from submitr.rclone import cloud_path, RCloneConfigGoogle

# Unified the logic for looking for files to upload.


class FileForUpload:

    @staticmethod
    def define(file: Union[str, pathlib.PosixPath, dict],
               main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
               main_search_directory_recursively: bool = False,
               other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
               google_source: Optional[str] = None,
               google_credentials: Optional[str] = None) -> Optional[FileForUpload]:

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

        if isinstance(main_search_directory, (str, pathlib.PosixPath)) and main_search_directory:
            # Actually, main_search_directory can also be a list (of str or PosixPath) of directories.
            file_paths = search_for_file(file,
                                         location=main_search_directory,
                                         recursive=main_search_directory_recursively is True)
        elif not isinstance(other_search_directories, list) or not other_search_directories:
            # Only if to main search directory specifed to we default ther "other" search
            # directories to the current directory (.) if it is not otherwise specified.
            other_search_directories = ["."]

        if not isinstance(file_paths, list) or not file_paths:
            # Only look at "other" search directories if we haven't yet found the file; and if
            # multiple instances of the file exist within these directories it doesn't matter,
            # we just take the first one we find, with no flagging of multiple files found;
            # unlike the case (above) of searching the specified main search directory where,
            # if recursive is specified, we will flag any multiple file instances found.
            # In practice these other directories are the directory containing the
            # submission file and the current directory.
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

        file_for_upload = FileForUpload(_for_internal_use_only=True,
                                        name=file,
                                        type=file_type,
                                        uuid=file_uuid,
                                        local_path=local_path,
                                        local_paths=local_paths,
                                        local_size=local_size,
                                        google_source=google_source,
                                        google_credentials=google_credentials)
        return file_for_upload

    def __init__(self,
                 _for_internal_use_only: bool,
                 name: str,
                 type: Optional[str] = None,
                 uuid: Optional[str] = None,
                 local_path: Optional[str] = None,
                 local_paths: Optional[List[str]] = None,
                 local_size: Optional[int] = None,
                 google_source: Optional[str] = None,
                 google_credentials: Optional[str] = None) -> None:

        if not (_for_internal_use_only is True):
            raise Exception("Cannot create FileForUpload object directly; use FileForUpload.define")
        self._name = name.strip() if isinstance(name, str) else ""
        self._type = type if isinstance(type, str) else None
        self._uuid = uuid if isinstance(uuid, str) else None
        self._local_path = local_path if isinstance(local_path, str) else None
        self._local_paths = local_paths if isinstance(local_paths, list) else None
        self._local_size = local_size if isinstance(local_size, int) else None
        self._google_source = google_source if isinstance(google_source, str) else None
        self._google_credentials = google_credentials if isinstance(google_credentials, str) else None
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
    def found(self) -> bool:
        return self._local_path is not None or self._google_path is not None

    @property
    def found_locally(self) -> bool:
        return self._local_path is not None

    @property
    def found_locally_multiple(self) -> bool:
        return self._local_paths is not None

    @property
    def found_in_google(self) -> bool:
        return self._google_path is not None

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
    def local_path(self) -> Optional[str]:
        return self._local_path

    @property
    def local_paths(self) -> Optional[List[str]]:
        return self._local_paths

    @property
    def google_path(self) -> Optional[str]:
        if not self._google_path:
            if self._google_source and self._google_credentials and not self._google_tried_and_failed:
                rclone_config_google = RCloneConfigGoogle(service_account_file=self._google_credentials)
                google_file = cloud_path.join(self._google_source, self.name)
                if isinstance(google_size := rclone_config_google.file_size(google_file), int) is not None:
                    self._google_path = google_file
                    self._google_size = google_size
                else:
                    self._google_tried_and_failed = True
        return self._google_path

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
        return self._google_size

    def resume_upload_command(self, env: Optional[str] = None) -> str:
        return f"resume-uploads{f' --env {env}' if isinstance(env, str) else ''}{f' {self.uuid}' if self.uuid else ''}"

    def __str__(self) -> str:
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
               google_credentials: Optional[str] = None) -> List[FileForUpload]:

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
