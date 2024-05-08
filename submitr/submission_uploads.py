import os
import pathlib
import re
from typing import List, Optional, Union
from dcicutils.function_cache_decorator import function_cache
from dcicutils.misc_utils import environ_bool
from dcicutils.s3_utils import HealthPageKey
from dcicutils.structured_data import Portal
from submitr.file_for_upload import FileForUpload, FilesForUpload
from submitr.output import PRINT
from submitr.rclone import RCloneConfigGoogle
from submitr.s3_utils import upload_file_to_aws_s3
from submitr.utils import tobool


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def do_any_uploads_new(arg, upload_folder=None, ingestion_filename=None,
                       rclone_google_config=None, subfolders=False, portal=None):

    files_for_upload = assemble_files_for_upload(
        arg=arg,
        main_search_directory=upload_folder,
        main_search_directory_recursively=subfolders,
        metadata_file=ingestion_filename,
        google_config=rclone_google_config,
        portal=portal)

    upload_files(files_for_upload, portal)


def assemble_files_for_upload(arg: Union[str, dict],
                              main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
                              main_search_directory_recursively: bool = False,
                              other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
                              metadata_file: Optional[str] = None,
                              google_config: Optional[RCloneConfigGoogle] = None,
                              portal: Optional[Portal] = None,
                              review: bool = True,
                              _recursive: bool = False) -> Optional[List[FileForUpload]]:

    # Returns a list of FileForUpload from the given argument; the given argument can be any of:
    #
    # - Submission type (IngestionSubmission) object:
    #   In which case we get the list of FileForUpload for upload-files associated with the submission.
    # - Submission type (IngestionSubmission) UUID:
    #   In which case we get the list of FileForUpload for upload-files associated with the submission.
    # - File type UUID:
    # - Accession ID (e.g. SMAFIQL563L8):
    # - Accession based file name (e.g. SMAFIQL563L8.fastq):
    #   In which case we get the SINGLE FileForUpload for the upload-file as a (SINGLE item) LIST.
    #
    # Returns empty list no files found, or None if something unexpected in the data.

    if not isinstance(portal, Portal) or not isinstance(arg, (str, dict)) or not arg:
        return None

    files_for_upload = None

    if item := arg if isinstance(arg, dict) else portal.get_metadata(arg, raise_exception=False):

        if is_validation_object(item, portal):
            # Here a validation (i.e. validate-only IngestinonSubmission) UUID was given (and was found);
            # if we can get the associated submission ID then implicitly use that, otherwise error.
            if not (associated_submission_uuid := get_associated_submission_uuid(item, portal)):
                PRINT(f"This submission ID ({arg}) is for a validation not an actual submission.")
                return None
            if _recursive is True:  # Just-in-case paranoid guard against infinite recursive loop.
                return None
            files_for_upload = assemble_files_for_upload(
                associated_submission_uuid,
                main_search_directory=main_search_directory,
                main_search_directory_recursively=main_search_directory_recursively,
                other_search_directories=other_search_directories,
                metadata_file=metadata_file,
                google_config=google_config,
                portal=portal, _recursive=True)

        elif is_submission_object(item, portal):
            # Here a submission (i.e. non-validate-only IngestionSubmission) UUID was given (and was found).
            # Note that other_directories ends up being handled by dcicutils.file_utils.search_for_file
            # which is flexible; handling lists with None, or non-strings, or file names rather
            # directories in which case the parent directory of the file will be assumed.
            if not isinstance(other_search_directories, list):
                other_search_directories = []
            other_search_directories.append(metadata_file)
            other_search_directories.append(get_submission_object_metadata_file_directory(item, portal))
            other_search_directories.append(os.path.curdir)
            files_for_upload = FilesForUpload.define(
                get_submission_object_upload_files(item, portal),
                main_search_directory=main_search_directory,
                main_search_directory_recursively=main_search_directory_recursively,
                other_search_directories=other_search_directories,
                google_config=google_config)

        elif portal.is_schema_file_type(item):
            # Here a file type UUID, or accession ID (e.g. SMAFIQL563L8) for a file type, was given (and was found).
            if not (file := item.get("filename")):
                PRINT(f"The given ID ({arg}) is for a file type but the associated file name cannot be found.")
                return None
            file_for_upload = FileForUpload(
                file,
                type=portal.get_schema_type(item),
                accession=item.get("accession"),
                accession_name=item.get("display_title"),
                uuid=item.get("uuid"),
                main_search_directory=main_search_directory,
                main_search_directory_recursively=main_search_directory_recursively,
                other_search_directories=other_search_directories,
                google_config=google_config)
            files_for_upload = [file_for_upload] if file_for_upload else []

        else:
            undesired_type = portal.get_schema_type(item)
            PRINT(f"The type ({undesired_type}) of the given ID ({arg}) is neither a submission nor a file type.")
            return None

    elif accession_id := _extract_accession_id(arg):
        # Here the given UUID (or accession ID) could not be found; it seems an
        # accession based file name was given; use the accession ID extacted from it.
        if _recursive is True:  # Just-in-case paranoid guard against infinite recursive loop.
            return None
        files_for_upload = assemble_files_for_upload(
            accession_id,
            main_search_directory=main_search_directory,
            main_search_directory_recursively=main_search_directory_recursively,
            other_search_directories=other_search_directories,
            metadata_file=metadata_file,
            google_config=google_config,
            portal=portal, _recursive=True)
        if files_for_upload and files_for_upload[0].accession_name and (files_for_upload[0].accession_name != arg):
            PRINT(f"Accession ID found but wrong filename: {files_for_upload[0].accession_name} vs {arg}")
            return None

    else:
        # Here the given UUID (or accession ID) could not be found.
        PRINT(f"Cannot find the given submission type or file type or accession ID: {arg}")
        return None

    if review is True:
        FilesForUpload.review(files_for_upload, portal=portal)
    return files_for_upload


def is_submission_ingestion_object(item: dict, portal: Portal) -> bool:
    if isinstance(item, dict) and isinstance(portal, Portal):
        return portal.is_schema_type(item, "IngestionSubmission")
    return False


def is_validation_object(item: dict, portal: Portal) -> bool:
    if is_submission_ingestion_object(item, portal):
        if isinstance(parameters := item.get("parameters"), dict):
            return tobool(parameters.get("validate_only"))
    return False


def is_submission_object(item: dict, portal: Portal) -> bool:
    if is_submission_ingestion_object(item, portal):
        return not is_validation_object(item, portal)
    return False


def get_associated_submission_uuid(validation_item: dict, portal: Portal) -> Optional[str]:
    if is_validation_object(validation_item, portal):
        return validation_item.get("parameters", {}).get("submission_uuid", None)
    return None


def get_submission_object_metadata_file_directory(submission_item: dict, portal: Portal) -> Optional[str]:
    if is_submission_ingestion_object(submission_item, portal):
        if isinstance(parameters := submission_item.get("parameters"), dict):
            return parameters.get("ingestion_directory", None)
    return None


def get_submission_object_upload_files(submission_item: dict, portal: Portal) -> Optional[str]:
    if is_submission_ingestion_object(submission_item, portal):
        if isinstance(upload_info := submission_item.get("upload_info"), list):
            return upload_info
        elif isinstance(additional_data := submission_item.get("additional_data"), dict):
            if isinstance(upload_info := additional_data.get("upload_info"), list):
                return upload_info
    return None


def upload_file(file_for_upload: FileForUpload, portal: Portal):  # NEW: replacement for upload_file_to_uuid
    """
    Upload file to a target environment.

    :param filename: the name of a file to upload.
    :param uuid: the item into which the filename is to be uploaded.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
    :returns: item metadata dict or None
    """
    if not isinstance(file_for_upload, FileForUpload) or not isinstance(portal, Portal):
        return

    metadata = None
    patch_data = {"filename": file_for_upload.name}
    response = portal.patch_metadata(object_id=file_for_upload.uuid, data=patch_data)
    metadata, upload_credentials = extract_metadata_and_upload_credentials(response,
                                                                           method="PATCH", uuid=file_for_upload.uuid,
                                                                           filename=file_for_upload.name,
                                                                           payload_data=patch_data,
                                                                           portal=portal)
    try:
        s3_uri = upload_credentials["upload_url"]
        aws_credentials = {
            "AWS_ACCESS_KEY_ID": upload_credentials["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": upload_credentials["SecretAccessKey"],
            "AWS_SECURITY_TOKEN": upload_credentials["SessionToken"]
        }
        aws_kms_key_id = get_s3_encrypt_key_id(upload_credentials=upload_credentials, auth=portal.key)
    except Exception as e:
        raise ValueError("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))

    # PRINT(f"▶ Upload: {file_for_upload.name} ({format_size(file_for_upload.size)}) ...")
    # PRINT(f"  - From: {file_for_upload.display_path}")
    # PRINT(f"  -   To: {s3_uri}")
    upload_file_to_aws_s3(file=file_for_upload,
                          s3_uri=s3_uri,
                          aws_credentials=aws_credentials,
                          aws_kms_key_id=aws_kms_key_id,
                          print_progress=True,
                          print_function=PRINT,
                          verify_upload=True,
                          catch_interrupt=True)

#   execute_prearranged_upload(file_for_upload.name,
#                              rclone_google_config=rclone_google_config,
#                              upload_credentials=upload_credentials, auth=auth)

    return metadata


def upload_files(files_for_upload: List[FileForUpload], portal: Portal):
    if isinstance(files_for_upload, list):
        files_for_upload = [file for file in files_for_upload if not file.ignore]
        for file in files_for_upload:
            upload_file(file, portal=portal)


def generate_credentials_for_upload(file: str, uuid: str) -> dict:
    pass


def extract_metadata_and_upload_credentials(response, filename, method, payload_data,
                                            uuid=None, schema_name=None, portal=None):
    try:
        [metadata] = response['@graph']
        upload_credentials = metadata['upload_credentials']
    except Exception as e:
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"Problem trying to {method} to get upload credentials.")
            PRINT(f" payload_data={payload_data}")
            if uuid:
                PRINT(f" uuid={uuid}")
            if schema_name:
                PRINT(f" schema_name={schema_name}")
            PRINT(f" response={response}")
            PRINT(f"Got error {type(e)}: {e}")
        file_status = None
        if portal and uuid:
            try:
                file_status = portal.get_metadata(uuid).get("status")
            except Exception:
                pass
        message = f"Unable to obtain upload credentials for file {filename}."
        if file_status:
            message += f" File status: {file_status}"
        raise RuntimeError(message)
    return metadata, upload_credentials


def _extract_accession_id(value: str) -> Optional[str]:
    if isinstance(value, str):
        if value.endswith(".gz"):
            value = value[:-3]
        value, _ = os.path.splitext(value)
        if _is_accession_id(value):
            return value
    return None


def get_s3_encrypt_key_id_from_health_page(auth):
    try:
        return _get_health_page(key=auth).get(HealthPageKey.S3_ENCRYPT_KEY_ID)
    except Exception:  # pragma: no cover
        # We don't actually unit test this section because _get_health_page realistically always returns
        # a dictionary, and so health.get(...) always succeeds, possibly returning None, which should
        # already be tested. Returning None here amounts to the same and needs no extra unit testing.
        # The presence of this error clause is largely pro forma and probably not really needed.
        return None


def get_s3_encrypt_key_id(*, upload_credentials, auth):
    if 's3_encrypt_key_id' in upload_credentials:
        s3_encrypt_key_id = upload_credentials.get('s3_encrypt_key_id')
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"Extracted s3_encrypt_key_id from upload_credentials: {s3_encrypt_key_id}")
    else:
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f"No s3_encrypt_key_id entry found in upload_credentials.")
            PRINT(f"Fetching s3_encrypt_key_id from health page.")
        s3_encrypt_key_id = get_s3_encrypt_key_id_from_health_page(auth)
        if DEBUG_PROTOCOL:  # pragma: no cover
            PRINT(f" =id=> {s3_encrypt_key_id!r}")
    return s3_encrypt_key_id


def _is_accession_id(value: str) -> bool:
    # See smaht-portal/.../schema_formats.py
    return isinstance(value, str) and re.match(r"^SMA[1-9A-Z]{9}$", value) is not None
    # return isinstance(value, str) and re.match(r"^[A-Z0-9]{12}$", value) is not None


@function_cache(serialize_key=True)
def _get_health_page(key: dict) -> dict:
    return Portal(key).get_health().json()
