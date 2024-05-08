from __future__ import annotations
import os
import pathlib
from typing import Callable, List, Optional, Union
from dcicutils.command_utils import yes_or_no
from dcicutils.file_utils import get_file_size, normalize_path, search_for_file
from dcicutils.misc_utils import format_size, normalize_string
from dcicutils.structured_data import Portal, StructuredDataSet
from submitr.rclone import cloud_path, RCloneConfigGoogle

# Unified the logic for looking for files to upload (to AWS S3), and storing
# related info; whether or not the file is coming from the local file system
# or from Google Cloud Storage (GCS), via rclone.


class FileForUpload:

    def __init__(self,
                 file: Union[str, pathlib.PosixPath, dict],
                 type: Optional[str] = None,
                 accession: Optional[str] = None,
                 accession_name: Optional[str] = None,
                 uuid: Optional[str] = None,
                 main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
                 main_search_directory_recursively: bool = False,
                 other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
                 google_config: Optional[RCloneConfigGoogle] = None) -> Optional[FileForUpload]:

        # Given file can be a dictionary (from structured_data.upload_files) like:
        # {"type": "ReferenceFile", "file": "first_file.fastq"}
        # Or a dictionary (from additional_data.upload_info of submission object) like:
        # {"uuid": "96f29020-7abd-4a42-b4c7-d342563b7074", "filename": "first_file.fastq"}
        # Or just a file name.

        if isinstance(file, dict):
            self._name = file.get("file", file.get("filename", ""))
            self._type = normalize_string(file.get("type")) or None
            self._uuid = normalize_string(file.get("uuid")) or None
        elif isinstance(file, pathlib.PosixPath):
            self._name = str(file)
        elif isinstance(file, str):
            self._name = file
        else:
            self._name = ""

        self._name = os.path.basename(normalize_path(self._name))
        if not self._name:
            raise Exception("Cannot create FileForUpload.")

        if value := normalize_string(type):
            self._type = value
        if value := normalize_string(uuid):
            self._uuid = value

        if not (main_search_directory := normalize_path(main_search_directory)):
            main_search_directory = None

        file_paths = []
        if main_search_directory:
            file_paths = search_for_file(self._name,
                                         location=main_search_directory,
                                         recursive=main_search_directory_recursively is True)
        if not isinstance(file_paths, list) or not file_paths:
            # Only look at other search directories if we have no yet found the file within the main
            # search directory; and if multiple instances of the file exist within/among these other
            # directories it doesn't matter; we just take the first one we find, with no flagging of
            # multiple files found. Unlike the case (above) of searching the main search directory
            # where (if recursive is specified) we will flag any multiple file instances found.
            # In practice these other directories are the directory containing
            # the submission file, and the current directory.
            if (not main_search_directory and
                not isinstance(other_search_directories, list) or not other_search_directories):  # noqa
                # Only if no main search directory is specifed do we default the other search
                # directories to the current directory (.), if it is not otherwise specified.
                other_search_directories = ["."]
            if isinstance(other_search_directories, list) and other_search_directories:
                # Actually, other_search_directories can also be just a str and/or PosixPath.
                if file_path := search_for_file(self._name,
                                                location=other_search_directories,
                                                single=True, recursive=False):
                    file_paths = [file_path]

        self._local_path = None
        self._local_paths = None
        if isinstance(file_paths, list) and file_paths:
            self._local_path = file_paths[0]
            if len(file_paths) > 1:
                self._local_paths = file_paths

        self._accession = normalize_string(accession) or None
        self._accession_name = normalize_string(accession_name) or None
        self._local_size = None
        self._google_config = google_config if isinstance(google_config, RCloneConfigGoogle) else None
        self._google_path = None
        self._google_size = None
        self._google_tried_and_failed = False
        self._favor_local = None
        self._ignore = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> Optional[str]:
        return self._type

    @property
    def accession(self) -> Optional[str]:
        return self._accession

    @property
    def accession_name(self) -> Optional[str]:
        return self._accession_name

    @property
    def uuid(self) -> Optional[str]:
        return self._uuid

    @property
    def found(self) -> bool:
        return self.local_path is not None or self.google_path is not None

    @property
    def path(self) -> Optional[str]:
        if self.found_locally:
            if self.found_in_google:
                if self.favor_local is None:
                    return None
                elif self.favor_local is False:
                    return self.google_path
            return self.local_path
        elif self.found_in_google:
            return self.google_path
        return None

    @property
    def display_path(self) -> Optional[str]:
        if self.found_locally:
            if self.found_in_google:
                if self.favor_local is None:
                    return None
                elif self.favor_local is False:
                    return self.display_google_path
            return self.local_path
        elif self.found_in_google:
            return self.display_google_path
        return None

    @property
    def size(self) -> Optional[int]:
        if self.found_locally:
            if self.found_in_google:
                if self.favor_local is None:
                    return None
                elif self.favor_local is False:
                    return self.google_size
            return self.local_size
        elif self.found_in_google:
            return self.google_size
        return None

    @property
    def ignore(self) -> bool:
        return self._ignore

    def resume_upload_command(self, env: Optional[str] = None) -> str:
        return (f"resume-uploads{f' --env {env}' if isinstance(env, str) else ''}"
                f"{f' {self.uuid or self.name}' if self.uuid else ''}")

    @property
    def favor_local(self) -> bool:
        return self._favor_local is True

    @property
    def favor_google(self) -> bool:
        return self._favor_local is False

    @property
    def found_locally(self) -> bool:
        return self.local_path is not None

    @property
    def found_locally_multiple(self) -> bool:
        return self.local_paths is not None

    @property
    def local_path(self) -> Optional[str]:
        return self._local_path

    @property
    def local_paths(self) -> Optional[List[str]]:
        return self._local_paths

    @property
    def local_size(self) -> Optional[int]:
        if self._local_size is None and (local_path := self._local_path):
            self._local_size = get_file_size(local_path)
        return self._local_size

    @property
    def found_in_google(self) -> bool:
        return self.google_path is not None

    @property
    def google_path(self) -> Optional[str]:
        if (self._google_path is None) and (not self._google_tried_and_failed):
            if (google_config := self.google_config) and (google_source := google_config.path):
                google_file = cloud_path.join(google_source, self.name)
                if (google_size := google_config.file_size(google_file)) is not None:
                    self._google_path = google_file
                    self._google_size = google_size
                else:
                    self._google_tried_and_failed = True
        return self._google_path

    @property
    def display_google_path(self) -> Optional[str]:
        if google_path := self.google_path:
            return f"gs://{google_path}"
        return None

    @property
    def google_size(self) -> Optional[int]:
        if self._google_size is None:
            _ = self.google_path  # Initialize GSC related info.
        return self._google_size

    @property
    def google_config(self) -> Optional[RCloneConfigGoogle]:
        return self._google_config

    def review(self, portal: Optional[Portal] = None, printf: Optional[Callable] = None) -> bool:
        if not self.found:
            printf(f"WARNING: Cannot find file for upload: {self.name} ({self.uuid})")
            if isinstance(portal, Portal):
                printf(f"- You may upload later with: {self.resume_upload_command(env=portal.env if portal else None)}")
            self._ignore = True
            return False
        elif self.found_locally:
            if self.found_in_google:
                printf(f"File for upload found BOTH locally AND in Google Cloud Storage: {self.name}")
                printf(f"- Local: {self.local_path}")
                printf(f"- Google Cloud Storage: {self.google_path}")
                self._favor_local = not yes_or_no("Do you want to use the Google Cloud Storage version?")
            if self.found_locally_multiple and self.favor_local:
                # TODO: Could prompt for an option to choose one of them or something.
                printf(f"WARNING: Ignoring file for upload as multiple instances found: {self.name}")
                for local_path in self.local_paths:
                    print(f"- {local_path}")
                self._ignore = True
                return False
            printf(f"File for upload to AWS S3: {self.display_path} ({format_size(self.size)})")
            return True
        elif self.found_in_google:
            printf(f"File for upload to AWS S3 (from GCS):"
                   f" gs://{self.google_path} ({format_size(self.google_size)})")
            return True

    def __str__(self) -> str:  # for troubleshooting only
        return (
            f"name={self.name}|"
            f"uuid={self.uuid}|"
            f"accession={self.accession}|"
            f"accession_name={self.accession_name}|"
            f"found={self.found}|"
            f"path={self.path}|"
            f"size={self.size}|"
            f"found_locally={self.found_locally}|"
            f"found_locally_multiple={self.found_locally_multiple}|"
            f"local_path={self.local_path}|"
            f"local_paths={self.local_paths}|"
            f"local_size={self.local_size}|"
            f"found_in_google={self.found_in_google}|"
            f"google_path={self.google_path}|"
            f"google_size={self.google_size}")


class FilesForUpload:

    @staticmethod
    def define(files: Union[StructuredDataSet, List[str]],
               main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
               main_search_directory_recursively: bool = False,
               other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
               google_config: Optional[RCloneConfigGoogle] = None) -> List[FileForUpload]:

        if isinstance(files, StructuredDataSet):
            files = files.upload_files
        elif isinstance(files, (str, pathlib.PosixPath)):
            files = [files]
        if not isinstance(files, list):
            return []

        files_for_upload = []
        for file in files:
            file_for_upload = FileForUpload(
                file,
                main_search_directory=main_search_directory,
                main_search_directory_recursively=main_search_directory_recursively,
                other_search_directories=other_search_directories,
                google_config=google_config)
            if file_for_upload:
                files_for_upload.append(file_for_upload)
        return files_for_upload

    @staticmethod
    def review(files_for_upload: List[FileForUpload],
               portal: Optional[Portal] = None, printf: Optional[Callable] = None) -> bool:
        if not isinstance(files_for_upload, list):
            return False
        if not callable(printf):
            printf = print
        result = True
        for file_for_upload in files_for_upload:
            if isinstance(file_for_upload, FileForUpload):
                if not file_for_upload.review(portal=portal, printf=printf):
                    result = False
        return result
