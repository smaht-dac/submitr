import boto3
from collections import namedtuple
import os
import threading
import time
from typing import Callable, Optional
from dcicutils.command_utils import yes_or_no
from dcicutils.file_utils import compute_file_md5
from dcicutils.misc_utils import format_duration, format_size
from dcicutils.progress_bar import ProgressBar
from submitr.file_for_upload import FileForUpload
from submitr.rclone import RClone, RCloneConfigAmazon, RCloneConfigGoogle, cloud_path
from submitr.utils import get_s3_bucket_and_key_from_s3_uri, format_datetime

# Module to upload a given file, with the given AWS credentials to AWS S3.
# Displays progress bar and other info; checks if file already exists; verifies
# upload; catches interrupts; et cetera. Circa May 2024 added support for upload,
# or transfer rather, from Google Cloud Storage (GCS) directly to S3 via rclone.

# Notes on checksums:
#
# Our primary use of checksums is to tell the user, in the case that the destination file
# in S3 already exists, if the source and destination files appear to be the same or not.
#
# For large files we can get ONLY the etag from AWS S3 and ONLY the md5 from Google Cloud Storage (GCS).
# So comparing checksums when uploading from GCS to AWS (our only current cloud-to-cloud use-case)
# is not so straightforward. Further, though we have not yet encountered this, it is a plausible
# assumption that under some circumstance, e.g. multi-part upload, even getting an md5 from GCS will
# be impossible. So, we just tell the user in this case that a reasonable comparison cannot be made.
#
# WRT the "rclone hashsum md5" command, it seems unreliable for S3 (it seems to just return
# the etag which generally seems to be the same as md5 for smaller files); so we do not use it;
# this rclone command does seem to be reliable for GCS (modulo the above comment about multi-parts).
#
# Given this, we will get the md5 of the file to be uploaded to S3 and store it as metadata on
# the uploaded S3 file/object. For local file uploads we just compute this md5 directly. For files
# being uploaded from GCS we (trust and) take/use the md5 value stored in GCS for the file/object.
# Then when we need the md5 of an already existing file in S3 we read this metadata rather than
# using rclone (or boto3 for that matter) to do it.

# This is to control whether or not we first prompt the user to take the time
# to do a checksum on the local file to see if it appears to be exactly the
# the same as an already exisiting file in AWS S3.
_BIG_FILE_SIZE = 1024 * 1024 * 500  # 500 MB


def OLD_upload_file_to_aws_s3(file: str, s3_uri: str,
                              aws_credentials: Optional[dict] = None,
                              aws_kms_key_id: Optional[str] = None,
                              rclone_google_source: Optional[str] = None,
                              rclone_google_credentials: Optional[str] = None,
                              print_progress: bool = True,
                              print_preamble: bool = True,
                              verify_upload: bool = True,
                              catch_interrupt: bool = True,
                              print_function: Optional[Callable] = print) -> bool:

    # import pdb ; pdb.set_trace()  # noqa
    pass
    if not isinstance(file, str) or not file or not isinstance(s3_uri, str) or not s3_uri:
        return False
    if not rclone_google_source and not os.path.exists(file):
        return False

    s3_bucket, s3_key = get_s3_bucket_and_key_from_s3_uri(s3_uri)
    if not s3_bucket or not s3_key:
        return False

    if isinstance(aws_credentials, dict):
        aws_credentials = {
            "region_name": aws_credentials.get("AWS_DEFAULT_REGION") or "us-east-1",
            "aws_access_key_id": aws_credentials.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_credentials.get("AWS_SECRET_ACCESS_KEY"),
            "aws_session_token": aws_credentials.get("AWS_SESSION_TOKEN") or aws_credentials.get("AWS_SECURITY_TOKEN")
        }
    else:
        aws_credentials = {}

    print_progress = print_progress is True
    print_preamble = print_preamble is True
    verify_upload = verify_upload is True
    catch_interrupt = catch_interrupt is True
    printf = print_function if callable(print_function) else print

    if rclone_google_source:
        rclone_config_amazon = RCloneConfigAmazon(region=aws_credentials.get("region_name"),
                                                  access_key_id=aws_credentials.get("aws_access_key_id"),
                                                  secret_access_key=aws_credentials.get("aws_secret_access_key"),
                                                  session_token=aws_credentials.get("aws_session_token"),
                                                  kms_key_id=aws_kms_key_id)
        rclone_config_google = RCloneConfigGoogle(service_account_file=rclone_google_credentials)
        rclone = RClone(source=rclone_config_google, destination=rclone_config_amazon)
        google_cloud_path = cloud_path.join(rclone_google_source, os.path.basename(file))
        if not rclone_config_google.path_exists(google_cloud_path):
            printf(f"ERROR: Cannot find Google Cloud Storage object: {google_cloud_path}")
            return False
        file_size = rclone_config_google.file_size(google_cloud_path)
        file_checksum = None
        if file_size >= _BIG_FILE_SIZE:
            if yes_or_no("Do you want to compute the checksum on this file?"):
                file_checksum = rclone_config_google.file_checksum(google_cloud_path)
        else:
            file_checksum = rclone_config_google.file_checksum(google_cloud_path)
        file_checksum_timestamp = time.time()
    else:
        rclone = None
        file_size = os.path.getsize(file)
        file_checksum = None
        file_checksum_timestamp = None

    def define_upload_file_callback(progress_total_nbytes: bool = False) -> None:
        nonlocal file_size

        def upload_file_callback_internal(nbytes_chunk: int) -> None:  # noqa
            # The execution of this may be in any number of child threads due to the way upload_fileobj
            # works; we do not create the progress bar until the upload actually starts because if we
            # do we get some initial bar output file.
            nonlocal started, file_size, nbytes_transferred, ncallbacks, upload_done, bar, progress_total_nbytes
            ncallbacks += 1
            if progress_total_nbytes is True:
                if (nbytes_transferred := nbytes_chunk) > file_size:
                    nbytes_transferred = file_size
            else:
                nbytes_transferred += nbytes_chunk
            # We do not use bar.increment_progress(nbytes_chunk) but rather set the total work
            # done (bar.set_total) so far to nbytes_transferred, so that counts add up right when
            # interrupted; during interrupt handling (outside in caller/main-thread) this callback
            # continues executing, as upload_fileobj continues its work; we just (during interrupt
            # handling) pause/disable the output of the progress bar; but bar.increment_progress(0)
            # still needs to be called so it takes.
            bar.set_progress(nbytes_transferred)
            if nbytes_transferred >= file_size:
                duration = time.time() - started
                upload_done = (f"Upload complete: {os.path.basename(file)}"
                               f" | {format_size(nbytes_transferred)} in {format_duration(duration)}"
                               f" | {format_size(nbytes_transferred / duration)} per second ◀")

        def upload_file_callback(nbytes_chunk: int) -> None:  # noqa
            nonlocal threads_aborted, thread_lock, should_abort
            thread_id = threading.current_thread().ident
            will_abort = False
            with thread_lock:
                # Queasy about raising an exception from within a lock.
                if should_abort and thread_id not in threads_aborted:
                    threads_aborted.add(thread_id)
                    will_abort = True
            if will_abort:
                raise Exception("Abort upload.")
            # For some reason using a try/except block here does not catch the abort exception above;
            # but we do in fact successfully kill these upload_fileobj threads; and main caller below catches.
            upload_file_callback_internal(nbytes_chunk)

        def done() -> Optional[str]:  # noqa
            nonlocal bar, ncallbacks, upload_done, printf
            if ncallbacks == 0:
                upload_file_callback(file_size)
            bar.done()
            if upload_done:
                printf(upload_done)
        def abort_upload(bar: ProgressBar) -> bool:  # noqa
            nonlocal should_abort
            with thread_lock:
                should_abort = True
            return False

        bar = ProgressBar(file_size, "▶ Upload progress",
                          use_byte_size_for_rate=True,
                          catch_interrupt=catch_interrupt,
                          interrupt_stop=abort_upload,
                          interrupt_continue=lambda _: False,
                          interrupt_message="upload",
                          tidy_output_hack=True)

        started = time.time()
        nbytes_transferred = 0
        ncallbacks = 0
        upload_done = None
        should_abort = False
        threads_aborted = set()
        thread_lock = threading.Lock()
        upload_file_callback_type = namedtuple("upload_file_callback", ["function", "done", "abort_upload"])
        return upload_file_callback_type(upload_file_callback, done, abort_upload)

    def get_uploaded_file_info() -> Optional[dict]:
        nonlocal aws_credentials, s3_bucket, s3_key
        try:
            # Note that we do not need to use any KMS key for head_object.
            s3 = boto3.client("s3", **aws_credentials)
            s3_file_head = s3.head_object(Bucket=s3_bucket, Key=s3_key)
            s3_file_etag = s3_file_head.get("ETag", "").strip("\"")
            result = {
                "modified": format_datetime(s3_file_head["LastModified"]),
                "size": s3_file_head["ContentLength"],
                "etag": s3_file_etag
            }
            if s3_file_md5 := s3_file_head.get("Metadata", {}).get("md5"):
                result["md5"] = s3_file_md5
                if s3_file_md5_timestamp := s3_file_head["Metadata"].get("md5-timestamp"):
                    result["md5_timestamp"] = s3_file_md5_timestamp
                if s3_file_md5_source := s3_file_head["Metadata"].get("md5-source"):
                    result["md5_source"] = s3_file_md5_source
            return result
        except Exception:
            # Ignore error for now because (1) verification usage not absolutely necessary,
            # and (2) portal permission change for this not yet deployed everywhere.
            return None

    def verify_with_any_already_uploaded_file() -> None:
        nonlocal file, file_size, file_checksum, file_checksum_timestamp
        if existing_file_info := get_uploaded_file_info():
            existing_file_modified = existing_file_info["modified"]
            existing_file_size = existing_file_info["size"]
            existing_file_md5 = existing_file_info.get("md5")  # might not be set
            # The file we are uploading already exists in S3.
            printf(f"WARNING: This file already exists in AWS S3:"
                   f" {format_size(existing_file_size)} | {existing_file_modified}")
            if files_appear_to_be_the_same := (existing_file_size == file_size):
                # File sizes are the same. See if these files appear to be the same according
                # to their checksums; but if it is a big file prompt the user first to check.
                if file_checksum:
                    compare_checksums = True
                elif not (compare_checksums := existing_file_size <= _BIG_FILE_SIZE):
                    if yes_or_no("Do you want to see if these files appear to be exactly the same (via checksum)?"):
                        compare_checksums = True
                    else:
                        files_appear_to_be_the_same = None  # sic: neither True nor False (see below)
                if compare_checksums:
                    if not file_checksum:
                        file_checksum = compute_file_md5(file)
                        file_checksum_timestamp = time.time()
                    if existing_file_md5:
                        if file_checksum != existing_file_md5:
                            files_appear_to_be_the_same = False
                            file_difference = f" | checksum: {file_checksum} vs {existing_file_md5}"
            else:
                file_difference = f" | size: {file_size} vs {existing_file_size}"
            if files_appear_to_be_the_same is False:
                printf(f"These files appear to be different{file_difference}")
            elif files_appear_to_be_the_same is True:
                if not existing_file_md5:
                    printf(f"NOTE: These files are the same size; checksum not available for further comparison.")
                else:
                    printf(f"These files appear to be the same | checksum: {existing_file_md5}")
            if not yes_or_no("Do you want to continue with this upload anyways?"):
                printf(f"Skipping upload of {os.path.basename(file)} ({format_size(file_size)}) to: {s3_uri}")
                return False
        return True

    def verify_uploaded_file() -> bool:
        nonlocal file_size
        if file_info := get_uploaded_file_info():
            printf(f"Verifying upload: {os.path.basename(file)} ... ", end="")
            if file_info["size"] != file_size:
                printf(f"WARNING: File size mismatch ▶ {file_size} vs {file_info['size']}")
                return False
            if file_checksum and file_info.get("md5") and (file_checksum != file_info["md5"]):
                printf(f"WARNING: File checksum mismatch ▶ {file_checksum} vs {file_info['md5']}")
                return False
            printf("OK")
            return True
        return False

    def create_metadata_for_uploading_file() -> dict:
        nonlocal aws_credentials, s3_bucket, s3_key, file_checksum, file_checksum_timestamp, rclone_google_source
        try:
            s3 = boto3.client("s3", **aws_credentials)
            metadata = s3.head_object(Bucket=s3_bucket, Key=s3_key).get("Metadata", {})
            # FYI no need to actually use the md5-timestamp WRT it being up-to-date as the metadata
            # for an S3 object is blown away whenever a new version of it is uploaded (by whatever means
            # it seems); so this, and md5-source, are really only useful for troubleshooting purpose.
            if file_checksum:
                metadata["md5"] = file_checksum
                metadata["md5-timestamp"] = str(file_checksum_timestamp)
                metadata["md5-source"] = "google-cloud-storage" if rclone_google_source else "file-system"
            return metadata
        except Exception:
            return {}

    def update_metadata_for_uploaded_file() -> bool:
        # Only need in the GCS case, as this metadata is set (via ExtraArgs) on the actual upload for S3.
        nonlocal aws_credentials, s3_bucket, s3_key
        if metadata := create_metadata_for_uploading_file():
            try:
                s3 = boto3.client("s3", **aws_credentials)
                s3.copy_object(Bucket=s3_bucket, Key=s3_key,
                               CopySource={"Bucket": s3_bucket, "Key": s3_key},
                               Metadata=metadata, MetadataDirective="REPLACE")
                return True
            except Exception:
                pass
        return False

    if print_preamble:
        printf(f"Uploading {os.path.basename(file)} ({format_size(file_size)}) to: {s3_uri}")

    if verify_upload and not verify_with_any_already_uploaded_file():
        return False

    metadata = create_metadata_for_uploading_file()
    upload_aborted = False

    if rclone:
        upload_file_callback = define_upload_file_callback(progress_total_nbytes=True)
        try:
            rclone.copy(cloud_path.join(rclone_google_source, os.path.basename(file)),
                        cloud_path.join(s3_bucket, s3_key),
                        progress=upload_file_callback.function)
            update_metadata_for_uploaded_file()
        except Exception:
            pass
    else:
        upload_file_callback = define_upload_file_callback(progress_total_nbytes=False)
        s3 = boto3.client("s3", **aws_credentials)
        aws_extra_args = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": aws_kms_key_id} if aws_kms_key_id else {}
        if metadata:
            aws_extra_args["Metadata"] = metadata
        with open(file, "rb") as f:
            try:
                if aws_extra_args:
                    s3.upload_fileobj(f, s3_bucket, s3_key,
                                      ExtraArgs=aws_extra_args,
                                      Callback=upload_file_callback.function)
                else:
                    s3.upload_fileobj(f, s3_bucket, s3_key, Callback=upload_file_callback.function)
            except Exception:
                printf(f"Upload ABORTED: {file} ◀")
                upload_aborted = True

    upload_file_callback.done()

    if not upload_aborted and verify_upload:
        verify_uploaded_file()

    return not upload_aborted


def upload_file_to_aws_s3(file: FileForUpload,
                          s3_uri: str,
                          aws_credentials: Optional[dict] = None,
                          aws_kms_key_id: Optional[str] = None,
                          print_progress: bool = True,
                          print_preamble: bool = True,
                          verify_upload: bool = True,
                          catch_interrupt: bool = True,
                          print_function: Optional[Callable] = print) -> bool:

    # import pdb ; pdb.set_trace()  # noqa
    pass
    if not (isinstance(file, FileForUpload) and file.found and isinstance(s3_uri, str) and s3_uri):
        return False

    s3_bucket, s3_key = get_s3_bucket_and_key_from_s3_uri(s3_uri)
    if not s3_bucket or not s3_key:
        return False

    if isinstance(aws_credentials, dict):
        aws_credentials = {
            "region_name": aws_credentials.get("AWS_DEFAULT_REGION") or "us-east-1",
            "aws_access_key_id": aws_credentials.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_credentials.get("AWS_SECRET_ACCESS_KEY"),
            "aws_session_token": aws_credentials.get("AWS_SESSION_TOKEN") or aws_credentials.get("AWS_SECURITY_TOKEN")
        }
    else:
        aws_credentials = {}

    print_progress = print_progress is True
    print_preamble = print_preamble is True
    verify_upload = verify_upload is True
    catch_interrupt = catch_interrupt is True
    printf = print_function if callable(print_function) else print

    if file.found_locally:
        rclone = None
        file_size = file.local_size
        file_checksum = None
        file_checksum_timestamp = None

    elif file.found_in_google:
        rclone_config_google = file.google_config
        rclone_config_amazon = RCloneConfigAmazon(region=aws_credentials.get("region_name"),
                                                  access_key_id=aws_credentials.get("aws_access_key_id"),
                                                  secret_access_key=aws_credentials.get("aws_secret_access_key"),
                                                  session_token=aws_credentials.get("aws_session_token"),
                                                  kms_key_id=aws_kms_key_id)
        rclone = RClone(source=rclone_config_google, destination=rclone_config_amazon)
        if not rclone_config_google.path_exists(file.google_path):
            printf(f"ERROR: Cannot find Google Cloud Storage object: {file.google_path}")
            return False
        file_size = file.google_size
        file_checksum = None
        # Note that it is known to be the case that calling rclone hashsum to get the checksum
        # of a file in Google Cloud Storage (GCS) merely retrieves the checksum from GCS,
        # which had previously been computed/stored by GCS for the file within GCS.
        file_checksum = rclone_config_google.file_checksum(file.google_path)
        file_checksum_timestamp = time.time()

    else:
        return False

    def define_upload_file_callback(progress_total_nbytes: bool = False) -> None:
        nonlocal file_size

        def upload_file_callback_internal(nbytes_chunk: int) -> None:  # noqa
            # The execution of this may be in any number of child threads due to the way upload_fileobj
            # works; we do not create the progress bar until the upload actually starts because if we
            # do we get some initial bar output file.
            nonlocal started, file, file_size, nbytes_transferred, ncallbacks, upload_done, bar, progress_total_nbytes
            ncallbacks += 1
            if progress_total_nbytes is True:
                if (nbytes_transferred := nbytes_chunk) > file_size:
                    nbytes_transferred = file_size
            else:
                nbytes_transferred += nbytes_chunk
            # We do not use bar.increment_progress(nbytes_chunk) but rather set the total work
            # done (bar.set_total) so far to nbytes_transferred, so that counts add up right when
            # interrupted; during interrupt handling (outside in caller/main-thread) this callback
            # continues executing, as upload_fileobj continues its work; we just (during interrupt
            # handling) pause/disable the output of the progress bar; but bar.increment_progress(0)
            # still needs to be called so it takes.
            bar.set_progress(nbytes_transferred)
            if nbytes_transferred >= file_size:
                duration = time.time() - started
                upload_done = (f"Upload complete: {file.name}"
                               f" | {format_size(nbytes_transferred)} in {format_duration(duration)}"
                               f" | {format_size(nbytes_transferred / duration)} per second ◀")

        def upload_file_callback(nbytes_chunk: int) -> None:  # noqa
            nonlocal threads_aborted, thread_lock, should_abort
            thread_id = threading.current_thread().ident
            will_abort = False
            with thread_lock:
                # Queasy about raising an exception from within a lock.
                if should_abort and thread_id not in threads_aborted:
                    threads_aborted.add(thread_id)
                    will_abort = True
            if will_abort:
                raise Exception("Abort upload.")
            # For some reason using a try/except block here does not catch the abort exception above;
            # but we do in fact successfully kill these upload_fileobj threads; and main caller below catches.
            upload_file_callback_internal(nbytes_chunk)

        def done() -> Optional[str]:  # noqa
            nonlocal bar, ncallbacks, upload_done, printf
            if ncallbacks == 0:
                upload_file_callback(file_size)
            bar.done()
            if upload_done:
                printf(upload_done)
        def abort_upload(bar: ProgressBar) -> bool:  # noqa
            nonlocal should_abort
            with thread_lock:
                should_abort = True
            return False

        bar = ProgressBar(file_size, "▶ Upload progress",
                          use_byte_size_for_rate=True,
                          catch_interrupt=catch_interrupt,
                          interrupt_stop=abort_upload,
                          interrupt_continue=lambda _: False,
                          interrupt_message="upload",
                          tidy_output_hack=True)

        started = time.time()
        nbytes_transferred = 0
        ncallbacks = 0
        upload_done = None
        should_abort = False
        threads_aborted = set()
        thread_lock = threading.Lock()
        upload_file_callback_type = namedtuple("upload_file_callback", ["function", "done", "abort_upload"])
        return upload_file_callback_type(upload_file_callback, done, abort_upload)

    def get_uploaded_file_info() -> Optional[dict]:
        nonlocal aws_credentials, s3_bucket, s3_key
        try:
            # Note that we do not need to use any KMS key for head_object.
            s3 = boto3.client("s3", **aws_credentials)
            s3_file_head = s3.head_object(Bucket=s3_bucket, Key=s3_key)
            s3_file_etag = s3_file_head.get("ETag", "").strip("\"")
            result = {
                "modified": format_datetime(s3_file_head["LastModified"]),
                "size": s3_file_head["ContentLength"],
                "etag": s3_file_etag
            }
            if s3_file_md5 := s3_file_head.get("Metadata", {}).get("md5"):
                result["md5"] = s3_file_md5
                if s3_file_md5_timestamp := s3_file_head["Metadata"].get("md5-timestamp"):
                    result["md5_timestamp"] = s3_file_md5_timestamp
                if s3_file_md5_source := s3_file_head["Metadata"].get("md5-source"):
                    result["md5_source"] = s3_file_md5_source
            return result
        except Exception:
            # Ignore error for now because (1) verification usage not absolutely necessary,
            # and (2) portal permission change for this not yet deployed everywhere.
            return None

    def verify_with_any_already_uploaded_file() -> None:
        nonlocal file, file_size, file_checksum, file_checksum_timestamp
        if existing_file_info := get_uploaded_file_info():
            existing_file_modified = existing_file_info["modified"]
            existing_file_size = existing_file_info["size"]
            existing_file_md5 = existing_file_info.get("md5")  # might not be set
            # The file we are uploading already exists in S3.
            printf(f"WARNING: This file already exists in AWS S3:"
                   f" {format_size(existing_file_size)} | {existing_file_modified}")
            if files_appear_to_be_the_same := (existing_file_size == file_size):
                # File sizes are the same. See if these files appear to be the same according
                # to their checksums; but if it is a big file prompt the user first to check.
                if file_checksum:
                    compare_checksums = True
                elif not (compare_checksums := existing_file_size <= _BIG_FILE_SIZE):
                    if yes_or_no("Do you want to see if these files appear to be exactly the same (via checksum)?"):
                        compare_checksums = True
                    else:
                        files_appear_to_be_the_same = None  # sic: neither True nor False (see below)
                if compare_checksums:
                    if not file_checksum:
                        # Here only for local file; for GCS we got the checksum up front (above).
                        file_checksum = compute_file_md5(file.local_path)
                        file_checksum_timestamp = time.time()
                    if existing_file_md5:
                        if file_checksum != existing_file_md5:
                            files_appear_to_be_the_same = False
                            file_difference = f" | checksum: {file_checksum} vs {existing_file_md5}"
            else:
                file_difference = f" | size: {file_size} vs {existing_file_size}"
            if files_appear_to_be_the_same is False:
                printf(f"These files appear to be different{file_difference}")
            elif files_appear_to_be_the_same is True:
                if not existing_file_md5:
                    printf(f"NOTE: These files are the same size; checksum not available for further comparison.")
                else:
                    printf(f"These files appear to be the same | checksum: {existing_file_md5}")
            if not yes_or_no("Do you want to continue with this upload anyways?"):
                printf(f"Skipping upload of {file.name} ({format_size(file_size)}) to: {s3_uri}")
                return False
        return True

    def verify_uploaded_file() -> bool:
        nonlocal file, file_size
        if file_info := get_uploaded_file_info():
            printf(f"Verifying upload: {file.name} ... ", end="")
            if file_info["size"] != file_size:
                printf(f"WARNING: File size mismatch ▶ {file_size} vs {file_info['size']}")
                return False
            if file_checksum and file_info.get("md5") and (file_checksum != file_info["md5"]):
                printf(f"WARNING: File checksum mismatch ▶ {file_checksum} vs {file_info['md5']}")
                return False
            printf("OK")
            return True
        return False

    def create_metadata_for_uploading_file() -> dict:
        nonlocal aws_credentials, s3_bucket, s3_key, file_checksum, file_checksum_timestamp
        try:
            s3 = boto3.client("s3", **aws_credentials)
            metadata = s3.head_object(Bucket=s3_bucket, Key=s3_key).get("Metadata", {})
            if file_checksum:
                metadata["md5"] = file_checksum
                metadata["md5-timestamp"] = str(file_checksum_timestamp)
                metadata["md5-source"] = "google-cloud-storage" if file.found_in_google else "file-system"
            return metadata
        except Exception:
            return {}

    def update_metadata_for_uploaded_file() -> bool:
        # Only need in the GCS case, as this metadata is set (via ExtraArgs) on the actual upload for S3.
        nonlocal aws_credentials, s3_bucket, s3_key
        if metadata := create_metadata_for_uploading_file():
            try:
                s3 = boto3.client("s3", **aws_credentials)
                s3.copy_object(Bucket=s3_bucket, Key=s3_key,
                               CopySource={"Bucket": s3_bucket, "Key": s3_key},
                               Metadata=metadata, MetadataDirective="REPLACE")
                return True
            except Exception:
                pass
        return False

    if print_preamble:
        # printf(f"Uploading {file.name} ({format_size(file_size)}) to: {s3_uri}")
        printf(f"▶ Upload: {file.name} ({format_size(file.size)}) ...")
        printf(f"  - From: {file.path_for_display}")
        printf(f"  -   To: {s3_uri}")

    if verify_upload and not verify_with_any_already_uploaded_file():
        return False

    metadata = create_metadata_for_uploading_file()
    upload_aborted = False

    if rclone:
        upload_file_callback = define_upload_file_callback(progress_total_nbytes=True)
        try:
            rclone.copy(file.google_path, cloud_path.join(s3_bucket, s3_key), progress=upload_file_callback.function)
            update_metadata_for_uploaded_file()
        except Exception:
            printf(f"Upload ABORTED: {file.google_path} ◀")  # TODO: test
            upload_aborted = True
            pass
    else:
        upload_file_callback = define_upload_file_callback(progress_total_nbytes=False)
        s3 = boto3.client("s3", **aws_credentials)
        aws_extra_args = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": aws_kms_key_id} if aws_kms_key_id else {}
        if metadata:
            aws_extra_args["Metadata"] = metadata
        with open(file.local_path, "rb") as f:
            try:
                if aws_extra_args:
                    s3.upload_fileobj(f, s3_bucket, s3_key,
                                      ExtraArgs=aws_extra_args,
                                      Callback=upload_file_callback.function)
                else:
                    s3.upload_fileobj(f, s3_bucket, s3_key, Callback=upload_file_callback.function)
            except Exception:
                printf(f"Upload ABORTED: {file.local_path} ◀")
                upload_aborted = True

    upload_file_callback.done()

    if not upload_aborted and verify_upload:
        verify_uploaded_file()

    return not upload_aborted
