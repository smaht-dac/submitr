from __future__ import annotations
import os
import pathlib
from typing import Callable, List, Optional, Tuple, Union
from dcicutils.command_utils import yes_or_no
from dcicutils.file_utils import compute_file_md5, get_file_size, normalize_path, search_for_file
from dcicutils.function_cache_decorator import function_cache
from dcicutils.misc_utils import format_size, normalize_string
from dcicutils.structured_data import Portal, StructuredDataSet
from submitr.output import PRINT
from submitr.rclone import RCloneAmazon, RCloneStore
from submitr.utils import chars

# See smaht-portal/.../schemas/file.json for these values; and see the definition and
# usage of SHOW_UPLOAD_CREDENTIALS_STATUSES in encoded-core/.../types/file.py for logic
# preventing upload credentials from being generated for anything but these statuss.
_FILE_STATUS_UPLOADING = "uploading"
_FILE_STATUSES_REQUIRED_FOR_UPLOAD = [_FILE_STATUS_UPLOADING, "to be uploaded by workflow", "upload failed"]


# Unified the logic for looking for files to upload (to AWS S3), and storing
# related info; whether or not the file is coming from the local file system
# or from Cloud Storage (GCS or AWS S3), via rclone.


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
                 cloud_store: Optional[RCloneStore] = None) -> Optional[FileForUpload]:

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
        self._cloud_store = cloud_store if isinstance(cloud_store, RCloneStore) else None
        self._path_cloud = None
        self._size_cloud = None
        self._checksum_cloud = None
        self._cloud_inaccessible = False
        self._favor_local = None
        self._ignore = False
        self._status = None

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
        """
        Returns True iff the file this object represents is coming from the local filesystem,
        otherwise False. However not that it is possible for this to return False if the file
        was found locally but was also found in GCS, and the favor_local property is None, meaning
        the review function has not yet been called, which resolves favor_local to True or False;
        in which case (if found both locally and in the cloud) from_cloud would also return False.
        """
        return self.found_local and ((not self.found_cloud) or (self.favor_local is True))

    @property
    def from_cloud(self) -> bool:
        """
        Returns True iff the file this object represents is coming from GCS, otherwise False.
        However not that it is possible for this to return False if the file was found locally
        but was also found in GCS, and the favor_local property is None, meaning the review
        function has not yet been called, which resolves favor_local to True or False; in
        which case (if found both locally and in the cloud) from_cloud would also return False.
        """
        return self.found_cloud and ((not self.found_local) or (self.favor_local is False))

    @property
    def found(self) -> bool:
        """
        Returns True iff the file this object represents was found either locally or in GCS,
        otherwise returns False.
        """
        return self.path_local is not None or self.path_cloud is not None

    @property
    def path(self) -> Optional[str]:
        return self.path_local if self.from_local else (self.path_cloud if self.from_cloud else None)

    @property
    def display_path(self) -> Optional[str]:
        return self.path_local if self.from_local else (self.display_path_cloud if self.from_cloud else None)

    @property
    def size(self) -> Optional[int]:
        return self.size_local if self.from_local else (self.size_cloud if self.from_cloud else None)

    @property
    def checksum(self) -> Optional[str]:
        return self.checksum_local if self.from_local else (self.checksum_cloud if self.from_cloud else None)

    @property
    def favor_local(self) -> Optional[bool]:
        """
        Returns True if we are favoring a local file over one in GCS; if no file at all found in GCS
        then naturally this returns True; otherwise if a GCS was found then this only returns True
        or False after the review function has been called where which file we is resolved to favor
        the local or the GCS file; before then this will return None in such a case.
        """
        if self._favor_local in (True, False):
            return self._favor_local
        if self.found_local:
            if self.found_cloud:
                return None
            return True
        return False

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
    def cloud_store(self) -> Optional[RCloneStore]:
        return self._cloud_store

    @property
    def found_cloud(self) -> bool:
        return self.path_cloud is not None

    @property
    def path_cloud(self) -> Optional[str]:
        if (self._path_cloud is None) and (cloud_store := self.cloud_store) and (not self._cloud_inaccessible):
            # We use the obtaining of the cloud file size as a proxy for existence.
            if (size_cloud := cloud_store.file_size(self.name)) is not None:
                self._path_cloud = cloud_store.path(self.name)
                self._size_cloud = size_cloud
            else:
                self._cloud_inaccessible = True
        return self._path_cloud

    @property
    def display_path_cloud(self) -> Optional[str]:
        if (path_cloud := self.path_cloud) and (cloud_store := self.cloud_store):
            return cloud_store.display_path(path_cloud)
        return None

    @property
    def size_cloud(self) -> Optional[int]:
        if self._size_cloud is None:
            _ = self.path_cloud  # Initializes size as part of checking existence.
        return self._size_cloud

    @property
    def checksum_cloud(self) -> Optional[str]:
        if self._checksum_cloud is None:
            if (cloud_store := self.cloud_store) and (not self._cloud_inaccessible):
                if checksum_cloud := cloud_store.file_checksum(self.name):
                    self._checksum_cloud = checksum_cloud
                else:
                    self._cloud_inaccessible = True
        return self._checksum_cloud

    @property
    def display_name(self) -> Optional[str]:
        display_name = self.name
        if self.uuid:
            if self.accession:
                display_name += f" ({self.uuid} | {self.accession})"
            else:
                display_name += f" ({self.uuid})"
        elif self.accession:
            display_name += f" ({self.accession})"
        return display_name

    def get_destination(self, portal: Portal) -> Optional[str]:
        if not self.uuid or not isinstance(portal, Portal):
            return None
        if not (file_upload_bucket := get_file_upload_bucket(portal)):
            return None
        accession, accession_file_name = get_file_accession_info(self.uuid, portal)
        if accession:
            self._accession = accession
        if accession_file_name:
            self._accession_name = accession_file_name
            return f"{RCloneAmazon.prefix}{file_upload_bucket}/{self.uuid}/{accession_file_name}"
        return None

    def get_status(self, portal: Portal, printf: Optional[Callable] = None) -> Optional[str]:
        if self._status is None:
            try:
                if self.uuid:
                    self._status = portal.get_metadata(self.uuid).get("status", "")
            except Exception:
                if callable(printf):
                    printf(f"ERROR: Cannot get status for file: {self.name} ({self.uuid})")
                return None
        return self._status

    def should_upload(self, portal: Portal, printf: Optional[Callable] = None) -> bool:
        if not self.uuid:
            # No uuid for the file  means we are validating only.
            return True
        file_status = self.get_status(portal, printf=printf)
        if file_status not in _FILE_STATUSES_REQUIRED_FOR_UPLOAD:
            # Here, the file status is not "uploading" (or one of the others
            # in _FILE_STATUSES_REQUIRED_FOR_UPLOAD), so it should not uploaded.
            if callable(printf):
                printf(f"{chars.xmark} WARNING: Ignoring file for upload: {self.display_name}")
                printf(f"  Because the status of this file is: {self.get_status(portal)}"
                       f" (must be one of: {', '.join(_FILE_STATUSES_REQUIRED_FOR_UPLOAD)})")
            return False
        if file_status == _FILE_STATUS_UPLOADING:
            try:
                # N.B. This Portal /upload_file_exists endpoint is new as of 2024-08-22; if not
                # present then this block will catch the exception and fall through to returning True below.
                if (((file_size_response := portal.get(f"/files/{self.uuid}/upload_file_size")).status_code == 200) and
                    isinstance(file_size := file_size_response.json().get("size"), int)):  # noqa
                    if callable(printf):
                        printf(f"{chars.xmark} WARNING: Ignoring file for upload: {self.display_name}")
                        printf(f"  It has already been uploaded:"
                               f" {get_file_upload_bucket(portal)}/{self.uuid}/{self.accession_name}"
                               f" ({format_size(file_size)})")
                    return False
            except Exception:
                pass
        return True

    def review(self, portal: Optional[Portal] = None, review_only: bool = False,
               last_in_list: bool = False, verbose: bool = False, printf: Optional[Callable] = None) -> bool:
        """
        Reviews, possibly confirming interactively the file for upload. If the
        file was found both locally (on the filesystem) and in the cloud, we
        will prompt the user as to which they want to use. If the file is found
        locally multiple times (due to recursive directory search) then gives a
        warning and skips (return False). Otherwise just returns True.
        """

        if not callable(printf):
            printf = PRINT

        destination = self.get_destination(portal)

        if not self.should_upload(portal, printf=printf):
            self._ignore = True
            return False
        elif self.found_local:
            found_both_local_and_cloud = False
            if self.found_cloud:
                found_both_local_and_cloud = True
                printf(f"- File for upload found BOTH locally"
                       f" AND in {self.cloud_store.proper_name_title}"
                       f" ({self.cloud_store.proper_name}): {self.display_name}")
                printf(f"  - {self.cloud_store.proper_name} cloud storage: {self.display_path_cloud}"
                       f"{f' ({format_size(self.size_cloud)})' if self.size_cloud else ''}")
            if self.found_local_multiple and (not self.found_cloud or (self._favor_local is True)):
                # Here there are multiple local files found (due to recursive directory lookup),
                # and there was either no cloud file found or if there was but we are favoring local.
                # For this case (multiple/ambiguous local files) return False and ignore this file.
                # Could prompt the user to choose which of the multiple local files to use or
                # something; but probably not worth it; doubt it will come up much if at all.
                if not review_only:
                    indent = ""
                    printf(f"- WARNING: Ignoring file for upload"
                           f" as multiple/ambiguous local instances found: {self.display_name}")
                else:
                    if found_both_local_and_cloud:
                        indent = "  "
                        printf(f"{indent}- Local file AMBIGUITY (multiple local instances found): {self.display_name}")
                    else:
                        indent = ""
                        printf(f"- File for upload AMBIGUITY (multiple local instances found): {self.display_name}")
                for path_local in self.path_local_multiple:
                    printf(f"{indent}  - {path_local} ({format_size(get_file_size(path_local))})")
                printf(f"{indent}  - Use --directory-only rather than --directory to NOT search recursively.")
                if not review_only:
                    if found_both_local_and_cloud:
                        self._favor_local = (
                            not yes_or_no(f"  - Do you want to use the {self.cloud_store.proper_name} version?"))
                    else:
                        printf(f"  - Upload later with:"
                               f" {self.resume_upload_command(env=portal.env if portal else None)}")
                self._ignore = True
                return False
            else:
                if found_both_local_and_cloud:
                    printf(f"  - Local file: {self.path_local} ({format_size(self.size_local)})")
                    if not review_only:
                        self._favor_local = (
                            not yes_or_no(f"  - Do you want to use the {self.cloud_store.proper_name} version?"))
                        printf(f"- File for upload: {self.display_path} ({format_size(self.size)})")
                        if destination:
                            printf(f"  AWS destination: {destination}")
                else:
                    printf(f"- File for upload: {self.path_local} ({format_size(self.size_local)})")
                    if destination:
                        printf(f"  AWS destination: {destination}")
            return True

        elif self.found_cloud:
            printf(f"- File for upload from {self.cloud_store.proper_name_title} ({self.cloud_store.proper_name}):"
                   f" {self.display_path_cloud} ({format_size(self.size_cloud)})")
            if destination:
                printf(f"  AWS destination: {destination}")
            return True

        else:  # I.e. self.found is False
            printf(f"{chars.xmark} WARNING: File NOT FOUND: {self.display_name} {chars.xmark}")
            if isinstance(portal, Portal):
                if not review_only:
                    printf(f"  - Upload later with:"
                           f" {self.resume_upload_command(env=portal.env if portal else None)}")
                elif last_in_list is True:
                    printf(f"  - Use --directory to specify a directory where the file(s) can be found.")
            self._ignore = True
            return False

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
            f"found_cloud={self.found_cloud}|"
            f"path_cloud={self.path_cloud}|"
            f"size_cloud={self.size_cloud}|"
            f"status={self._status}")


class FilesForUpload:

    @staticmethod
    def assemble(files: Union[StructuredDataSet, List[dict], List[Union[str, pathlib.Path]], str, pathlib.Path],
                 main_search_directory: Optional[Union[str, pathlib.Path]] = None,
                 main_search_directory_recursively: bool = False,
                 other_search_directories: Optional[List[Union[str, pathlib.Path]]] = None,
                 cloud_store: Optional[RCloneStore] = None) -> List[FileForUpload]:

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
                cloud_store=cloud_store)
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
            printf = PRINT
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
            max_index = len(files_for_upload) - 1
            for index, file_for_upload in enumerate(files_for_upload):
                if not file_for_upload.review(portal=portal, review_only=review_only,
                                              last_in_list=index == max_index,
                                              verbose=verbose, printf=printf):
                    result = False
        return result


@function_cache(maxsize=1)
def get_file_upload_bucket(portal: Portal) -> Optional[str]:
    if not isinstance(portal, Portal):
        return None
    try:
        return portal.get_health().json()["file_upload_bucket"]
    except Exception:
        return None


@function_cache(maxsize=2048)
def get_file_accession_info(uuid: str, portal: Portal) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(uuid, str) or not uuid or not isinstance(portal, Portal):
        return None, None
    try:
        file_extension = None
        if file_object := portal.get_metadata(uuid):
            accession = file_object.get("accession")
            accession_file_name = None
            if file_extension := get_file_extension(file_object, portal):
                accession_file_name = f"{accession}.{file_extension}"
            return accession, accession_file_name
    except Exception:
        pass
    return None, None


@function_cache(maxsize=64, serialize_key=True)
def get_file_extension(file_format_uuid_or_file_object: Union[str, dict], portal: Portal) -> Optional[str]:
    if isinstance(file_format_uuid_or_file_object, dict):
        if not (file_format_uuid := file_format_uuid_or_file_object.get("file_format", {}).get("uuid")):
            return None
    elif isinstance(file_format_uuid_or_file_object, str):
        file_format_uuid = file_format_uuid_or_file_object
    if file_format_uuid and (file_format_object := portal.get_metadata(file_format_uuid)):
        if file_extension := file_format_object.get("standard_file_extension"):
            return file_extension
    return None
