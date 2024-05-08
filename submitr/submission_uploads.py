import os
import pathlib
import re
from typing import List, Optional, Tuple, Union
from dcicutils.s3_utils import HealthPageKey
from dcicutils.structured_data import Portal
from submitr.file_for_upload import FileForUpload, FilesForUpload
from submitr.output import PRINT
from submitr.rclone import RCloneConfigGoogle
from submitr.s3_utils import upload_file_to_aws_s3
from submitr.utils import tobool


def do_any_uploads(arg: Union[str, dict],
                   metadata_file: Optional[str] = None,
                   main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
                   main_search_directory_recursively: bool = False,
                   google_config: Optional[RCloneConfigGoogle] = None,
                   portal: Optional[Portal] = None,
                   verbose: bool = False) -> None:

    files_for_upload = assemble_files_for_upload(
        arg,
        main_search_directory=main_search_directory,
        main_search_directory_recursively=main_search_directory_recursively,
        metadata_file=metadata_file,
        google_config=google_config,
        portal=portal,
        verbose=verbose)

    upload_files(files_for_upload, portal)


def assemble_files_for_upload(arg: Union[str, dict],
                              main_search_directory: Optional[Union[str, pathlib.PosixPath]] = None,
                              main_search_directory_recursively: bool = False,
                              other_search_directories: Optional[List[Union[str, pathlib.PosixPath]]] = None,
                              metadata_file: Optional[str] = None,
                              google_config: Optional[RCloneConfigGoogle] = None,
                              portal: Optional[Portal] = None,
                              review: bool = True,
                              verbose: bool = False,
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
            files_for_upload = FilesForUpload.assemble(
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

    elif accession_id := extract_accession_id(arg):
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

    if (review is True) and (_recursive is False):
        FilesForUpload.review(files_for_upload, portal=portal, verbose=verbose)
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


def upload_files(files: List[FileForUpload], portal: Portal):
    if isinstance(files, list):
        for file in [file for file in files if not file.ignore]:
            upload_file(file, portal=portal)


def upload_file(file: FileForUpload, portal: Portal) -> None:
    """
    Upload file to a target environment.

    :param filename: the name of a file to upload.
    :param uuid: the item into which the filename is to be uploaded.
    :param auth: auth info in the form of a dictionary containing 'key', 'secret', and 'server'.
    :returns: item metadata dict or None
    """
    if not isinstance(file, FileForUpload) or not isinstance(portal, Portal):
        return

    aws_s3_uri, aws_credentials, aws_kms_key_id = generate_credentials_for_upload(file.name, file.uuid, portal)

    upload_file_to_aws_s3(file=file,
                          s3_uri=aws_s3_uri,
                          aws_credentials=aws_credentials,
                          aws_kms_key_id=aws_kms_key_id,
                          print_progress=True,
                          verify_upload=True,
                          catch_interrupt=True,
                          printf=PRINT)


def generate_credentials_for_upload(file: str, uuid: str, portal: Portal) -> Tuple[str, str, str]:
    patch_data = {"filename": file}
    response = portal.patch_metadata(object_id=uuid, data=patch_data)
    upload_credentials = extract_upload_credentials(response, filename=file, uuid=uuid, portal=portal)
    try:
        aws_s3_uri = upload_credentials["upload_url"]
        aws_credentials = {
            "AWS_ACCESS_KEY_ID": upload_credentials["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": upload_credentials["SecretAccessKey"],
            "AWS_SECURITY_TOKEN": upload_credentials["SessionToken"]
        }
        aws_kms_key_id = get_s3_encrypt_key_id(upload_credentials=upload_credentials, portal=portal)
        return aws_s3_uri, aws_credentials, aws_kms_key_id
    except Exception as e:
        raise ValueError("Upload specification is not in good form. %s: %s" % (e.__class__.__name__, e))


def extract_upload_credentials(response: dict, filename: str, uuid: str, portal: Portal) -> dict:
    try:
        # TODO
        # N.B. Older code used to pass this metadata back to the caller to process any extra
        # files which might be present; removed all of this processing from smaht-submitr
        # for now to simplify, as this is not currently supported; may well add back later.
        [metadata] = response["@graph"]
        upload_credentials = metadata["upload_credentials"]
    except Exception:
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
    return upload_credentials


def get_s3_encrypt_key_id(upload_credentials: dict, portal: Portal):
    if "s3_encrypt_key_id" in upload_credentials:
        return upload_credentials["s3_encrypt_key_id"]
    return get_s3_encrypt_key_id_from_health_page(portal)


def get_s3_encrypt_key_id_from_health_page(portal: Portal):
    try:
        return portal.get_health().get(HealthPageKey.S3_ENCRYPT_KEY_ID)
    except Exception:  # pragma: no cover
        # We don't actually unit test this section because get_health_page realistically always returns
        # a dictionary, and so health.get(...) always succeeds, possibly returning None, which should
        # already be tested. Returning None here amounts to the same and needs no extra unit testing.
        # The presence of this error clause is largely pro forma and probably not really needed.
        return None


def is_accession_id(value: str) -> bool:
    # See smaht-portal/.../schema_formats.py
    return isinstance(value, str) and re.match(r"^SMA[1-9A-Z]{9}$", value) is not None
    # return isinstance(value, str) and re.match(r"^[A-Z0-9]{12}$", value) is not None


def extract_accession_id(value: str) -> Optional[str]:
    if isinstance(value, str):
        if value.endswith(".gz"):
            value = value[:-3]
        value, _ = os.path.splitext(value)
        if is_accession_id(value):
            return value
    return None
