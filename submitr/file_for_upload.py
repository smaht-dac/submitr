from __future__ import annotations
import os
import pathlib
from typing import Callable, List, Optional, Union
from dcicutils.command_utils import yes_or_no
from dcicutils.file_utils import compute_file_md5, get_file_size, normalize_path, search_for_file
from dcicutils.misc_utils import format_size, normalize_string
from dcicutils.structured_data import Portal, StructuredDataSet
from submitr.rclone import RCloneGoogle

# Unified the logic for looking for files to upload (to AWS S3), and storing
# related info; whether or not the file is coming from the local file system
# or from Google Cloud Storage (GCS), via rclone.


class FileForUpload:

    def __init__(self,
                 file: Union[dict, str, pathlib.Path],
                 type: Optional[str] = None,
                 accession: Optional[str] = None,
                 accession_name: Optional[str] = None,
                 uuid: Optional[str] = None,
                 main_search_directory: Optional[Union[str, pathlib.Path]] = None,
                 main_search_directory_recursively: bool = False,
                 other_search_directories: Optional[Union[List[Union[str, pathlib.Path]], str, pathlib.Path]] = None,
                 config_google: Optional[RCloneGoogle] = None) -> Optional[FileForUpload]:

        # Given file can be a dictionary (from structured_data.upload_files) like:
        # {"type": "ReferenceFile", "file": "first_file.fastq"}
        # Or a dictionary (from additional_data.upload_info of IngestionSubmission object) like:
        # {"uuid": "96f29020-7abd-4a42-b4c7-d342563b7074", "filename": "first_file.fastq"}
        # Or just a file name.

        if isinstance(file, dict):
            self._name = file.get("file", file.get("filename", ""))
            self._type = normalize_string(file.get("type")) or None
            self._uuid = normalize_string(file.get("uuid")) or None
        elif isinstance(file, pathlib.Path):
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
            if isinstance(other_search_directories, (str, pathlib.Path)) and other_search_directories:
                other_search_directories = [other_search_directories]
            if (not main_search_directory and
                not isinstance(other_search_directories, list) or not other_search_directories):  # noqa
                # Only if no main search directory is specifed do we make the default for other
                # search directories the current directory (.), iff it is not otherwise specified.
                other_search_directories = ["."]
            if isinstance(other_search_directories, list) and other_search_directories:
                # Actually, other_search_directories can also be just a str and/or Path.
                if file_path := search_for_file(self._name,
                                                location=other_search_directories,
                                                single=True, recursive=False):
                    file_paths = [file_path]

        self._path_local = None
        self._path_local_multiple = None
        if isinstance(file_paths, list) and file_paths:
            self._path_local = file_paths[0]
            if len(file_paths) > 1:
                self._path_local_multiple = file_paths

        self._accession = normalize_string(accession) or None
        self._accession_name = normalize_string(accession_name) or None
        self._size_local = None
        self._checksum_local = None
        self._config_google = config_google if isinstance(config_google, RCloneGoogle) else None
        self._path_google = None
        self._size_google = None
        self._checksum_google = None
        self._google_inaccessible = False
        self._favor_local = None
        self._ignore = False

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
    def from_local(self) -> bool:
        # Possible for this to return False if the file was found locally but was also found
        # in Google Cloud Storage, and the favor_local property is None, meaning the review
        # function has not yet been called, which resolves favor_local to True or False.
        return self.found_local and ((not self.found_google) or (self.favor_local is True))

    @property
    def from_google(self) -> bool:
        # Same exact comment as from_local above applies here.
        return self.found_google and ((not self.found_local) or (self.favor_local is False))

    @property
    def found(self) -> bool:
        return self.path_local is not None or self.path_google is not None

    @property
    def path(self) -> Optional[str]:
        return self.path_local if self.from_local else (self.path_google if self.from_google else None)

    @property
    def display_path(self) -> Optional[str]:
        return self.path_local if self.from_local else (self.display_path_google if self.from_google else None)

    @property
    def size(self) -> Optional[int]:
        return self.size_local if self.from_local else (self.size_google if self.from_google else None)

    @property
    def checksum(self) -> Optional[str]:
        return self.checksum_local if self.from_local else (self.checksum_google if self.from_google else None)

    @property
    def favor_local(self) -> Optional[bool]:
        return self._favor_local if self.found_google else True

    @property
    def ignore(self) -> bool:
        return self._ignore

    def resume_upload_command(self, env: Optional[str] = None) -> Optional[str]:
        return (f"resume-uploads{f' --env {env}' if isinstance(env, str) else ''}"
                f"{f' {self.uuid or self.name}' if self.uuid else ''}") if self.uuid else None

    @property
    def found_local(self) -> bool:
        return self.path_local is not None

    @property
    def found_local_multiple(self) -> bool:
        return self.path_local_multiple is not None

    @property
    def path_local(self) -> Optional[str]:
        return self._path_local

    @property
    def path_local_multiple(self) -> Optional[List[str]]:
        return self._path_local_multiple

    @property
    def size_local(self) -> Optional[int]:
        if self._size_local is None and (path_local := self._path_local):
            self._size_local = get_file_size(path_local)
        return self._size_local

    @property
    def checksum_local(self) -> Optional[str]:
        if self._checksum_local is None and (path_local := self._path_local):
            self._checksum_local = compute_file_md5(path_local)
        return self._checksum_local

    @property
    def config_google(self) -> Optional[RCloneGoogle]:
        return self._config_google

    @property
    def found_google(self) -> bool:
        return self.path_google is not None

    @property
    def path_google(self) -> Optional[str]:
        if (self._path_google is None) and (config_google := self.config_google) and (not self._google_inaccessible):
            # We use the obtaining of the Google Cloud Storage file size as a proxy for existence.
            if (size_google := config_google.file_size(self.name)) is not None:
                self._path_google = config_google.path(self.name)
                self._size_google = size_google
            else:
                self._google_inaccessible = True
        return self._path_google

    @property
    def display_path_google(self) -> Optional[str]:
        if path_google := self.path_google:
            return f"gs://{path_google}"
        return None

    @property
    def size_google(self) -> Optional[int]:
        if self._size_google is None:
            _ = self.path_google  # Initializes size as part of checking existence.
        return self._size_google

    @property
    def checksum_google(self) -> Optional[str]:
        if self._checksum_google is None:
            if (config_google := self.config_google) and (not self._google_inaccessible):
                if checksum_google := config_google.file_checksum(self.name):
                    self._checksum_google = checksum_google
                else:
                    self._google_inaccessible = True
        return self._checksum_google

    def review(self, portal: Optional[Portal] = None, review_only: bool = False,
               verbose: bool = False, printf: Optional[Callable] = None) -> bool:
        """
        Reviews, possibly confirming interactively the file for upload. If the file
        was found both locally (on the filesystem) and in Google Cloud Storage, we
        will prompt the user as to which they want to use. If the file is found
        locally multiple times (due to recursive directory search) then gives a
        warning and skips (return False). Otherwise just returns True.
        """

        if not callable(printf):
            printf = print

        file_identifier = self.name
        if self.uuid:
            if self.accession:
                file_identifier += f" ({self.uuid} | {self.accession})"
            else:
                file_identifier += f" ({self.uuid})"
        elif self.accession:
            file_identifier += f" ({self.accession})"

        if not self.found:
            printf(f"- WARNING: File for upload NOT FOUND: {file_identifier}")
            if isinstance(portal, Portal):
                printf(f"  - Use --directory to specify a directory where the file can be found.")
                if not review_only:
                    printf(f"  - Upload later with:"
                           f" {self.resume_upload_command(env=portal.env if portal else None)}")
            self._ignore = True
            return False

        found_local_and_google = False

        if self.found_local:
            if self.found_google:
                found_local_and_google = True
                printf(f"- File for upload found BOTH locally AND in Google Cloud Storage: {file_identifier}")
                printf(f"  - Google Cloud Storage: {self.display_path_google}"
                       f"{f' ({format_size(self.size_google)})' if self.size_google else ''}")
            if self.found_local_multiple and (not self.found_google or self._favor_local is True):
                # Here there are multiple local files found (due to recursive directory lookup),
                # and there was either no Google file found or if there was we are favoring local.
                # Could prompt the user to choose which of the multiple local files to use or
                # something; but probably not worth it; doubt it will come up much if at all.
                if not review_only:
                    indent = ""
                    printf(f"- WARNING: Ignoring file for upload"
                           f" as multiple/ambiguous local instances found: {file_identifier}")
                else:
                    if found_local_and_google:
                        indent = "  "
                        printf(f"{indent}- Local file AMBIGUITY (multiple local instances found): {file_identifier}")
                    else:
                        indent = ""
                        printf(f"- File for upload AMBIGUITY (multiple local instances found): {file_identifier}")
                for path_local in self.path_local_multiple:
                    printf(f"{indent}  - {path_local} ({format_size(get_file_size(path_local))})")
                printf(f"{indent}  - Use --directory-only rather than --directory to NOT search recursively.")
                if not review_only:
                    if found_local_and_google:
                        self._favor_local = not yes_or_no("  - Do you want to use the Google Cloud Storage version?")
                    else:
                        printf(f"  - Upload later with:"
                               f" {self.resume_upload_command(env=portal.env if portal else None)}")
                self._ignore = True
                return False
            else:
                if found_local_and_google:
                    printf(f"  - Local: {self.path_local} ({format_size(self.size_local)})")
                    if not review_only:
                        self._favor_local = not yes_or_no("  - Do you want to use the Google Cloud Storage version?")
                else:
                    printf(f"- File for upload: {self.path_local} ({format_size(self.size_local)})")

            if not review_only and verbose:
                printf(f"- File for upload: {self.display_path} ({format_size(self.size)})")
            return True
        elif self.found_google:
            if verbose:
                printf(f"- File for upload (from Google Cloud Storage):"
                       f" {self.display_path_google} ({format_size(self.size_google)})")
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
            f"found_local={self.found_local}|"
            f"found_local_multiple={self.found_local_multiple}|"
            f"path_local={self.path_local}|"
            f"path_local_multiple={self.path_local_multiple}|"
            f"size_local={self.size_local}|"
            f"found_google={self.found_google}|"
            f"path_google={self.path_google}|"
            f"size_google={self.size_google}")


class FilesForUpload:

    @staticmethod
    def assemble(files: Union[StructuredDataSet, List[dict], List[Union[str, pathlib.Path]], str, pathlib.Path],
                 main_search_directory: Optional[Union[str, pathlib.Path]] = None,
                 main_search_directory_recursively: bool = False,
                 other_search_directories: Optional[List[Union[str, pathlib.Path]]] = None,
                 config_google: Optional[RCloneGoogle] = None) -> List[FileForUpload]:

        if isinstance(files, StructuredDataSet):
            files = files.upload_files
        elif isinstance(files, (str, pathlib.Path)):
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
                config_google=config_google)
            if file_for_upload:
                files_for_upload.append(file_for_upload)
        return files_for_upload

    @staticmethod
    def review(files_for_upload: List[FileForUpload],
               portal: Optional[Portal] = None,
               review_only: bool = False,
               verbose: bool = False,
               printf: Optional[Callable] = None) -> bool:
        if not isinstance(files_for_upload, list):
            return False
        if not callable(printf):
            printf = print
        result = True
        if files_for_upload:
            files_for_upload_missing = [file for file in files_for_upload if not file.found]
            files_for_upload_ambiguous = [file for file in files_for_upload if file.found_local_multiple]
            message = f"Reviewing files for upload to AWS S3 | Total: {len(files_for_upload)}"
            if files_for_upload_missing:
                message += f" | Missing: {len(files_for_upload_missing)}"
            if files_for_upload_ambiguous:
                message += f" | Ambiguous: {len(files_for_upload_ambiguous)}"
            printf(message)
            for file_for_upload in files_for_upload:
                if isinstance(file_for_upload, FileForUpload):
                    if not file_for_upload.review(portal=portal, review_only=review_only,
                                                  verbose=verbose, printf=printf):
                        result = False
        return result
