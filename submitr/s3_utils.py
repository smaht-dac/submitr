import boto3
from collections import namedtuple
import os
import signal
import sys
import threading
import time
from tqdm import tqdm
from typing import Callable, Optional
from dcicutils.command_utils import yes_or_no
from .utils import (
    get_file_md5_like_aws_s3_etag, get_s3_bucket_and_key_from_s3_uri,
    format_datetime, format_duration, format_size
)


# This is to control whether or not we first prompt the user to take the time
# to do a checksum on the local file to see if it appears to be exactly the
# the same as an already exisiting file in AWS S3.
_BIG_FILE_SIZE = 1024 * 1024 * 500  # 500 MB


# Uploads the given file with the given AWS credentials to AWS S3.
# Displays progress bar and other info; checks if file already
# exists; verifies upload; catches interrupts; et cetera.
def upload_file_to_aws_s3(file: str, s3_uri: str,
                          file_checksum: Optional[str] = None,
                          aws_credentials: Optional[dict] = None,
                          aws_kms_key_id: Optional[str] = None,
                          print_progress: bool = True,
                          print_preamble: bool = True,
                          verify_upload: bool = True,
                          catch_interrupt: bool = True,
                          print_function: Optional[Callable] = print) -> bool:

    if not isinstance(file, str) or not file or not isinstance(s3_uri, str) or not s3_uri:
        return False
    if not os.path.exists(file):
        return False

    s3_bucket, s3_key = get_s3_bucket_and_key_from_s3_uri(s3_uri)
    if not s3_bucket or not s3_key:
        return False

    file_size = os.path.getsize(file)

    if isinstance(aws_credentials, dict):
        aws_credentials = {
            "region_name": aws_credentials.get("AWS_DEFAULT_REGION") or "us-east-1",
            "aws_access_key_id": aws_credentials.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_credentials.get("AWS_SECRET_ACCESS_KEY"),
            "aws_session_token": aws_credentials.get("AWS_SESSION_TOKEN") or aws_credentials.get("AWS_SECURITY_TOKEN")
        }
    else:
        aws_credentials = {}
    if aws_kms_key_id:
        aws_credentials["SSEKMSKeyId"] = aws_kms_key_id

    print_progress = print_progress is True
    print_preamble = print_preamble is True
    verify_upload = verify_upload is True
    catch_interrupt = catch_interrupt is True
    printf = print_function if callable(print_function) else print

    def define_upload_file_callback() -> None:
        nonlocal file_size
        started = time.time()
        nbytes_transferred = 0
        ncallbacks = 0
        upload_done = None
        should_abort = False
        bar_message = "▶ Upload progress"
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} | {rate_fmt} | {elapsed}{postfix} | ETA: {remaining} "
        bar = tqdm(total=file_size, desc=bar_message,
                   dynamic_ncols=True, bar_format=bar_format, unit="", file=sys.stdout)
        threads_aborted = set()
        thread_lock = threading.Lock()
        def upload_file_callback_internal(nbytes_chunk: int) -> None:  # noqa
            # The execution of this may be in any number of child threads due to the way upload_fileobj
            # works; we do not create the progress bar until the upload actually starts because if we
            # do we get some initial bar output file.
            nonlocal started, file_size, nbytes_transferred, ncallbacks, upload_done, bar
            ncallbacks += 1
            nbytes_transferred += nbytes_chunk
            # We do not use bar.update(nbytes_chunk) but rather set the total work done (bar.n)
            # so far to nbytes_transferred, so that counts add up right when interrupted; during
            # interrupt handling (outside in caller/main-thread) this callback continues executing,
            # as upload_fileobj continues its work; we just (during interrupt handling) pause/disable
            # the output of the progress bar; but bar.update(0) still needs to be called so it takes.
            bar.n = nbytes_transferred
            bar.update(0)
            if nbytes_transferred >= file_size:
                duration = time.time() - started
                # The set_description seems to be need make sure the
                # last bit is flushed out; in the case of interrupt.
                cleanup()
                upload_done = (f"Upload done: {format_size(nbytes_transferred)} in {format_duration(duration)}"
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

        def pause_output() -> None:  # noqa
            nonlocal bar
            bar.disable = True
        def resume_output() -> None:  # noqa
            nonlocal bar
            bar.disable = False
        def cleanup() -> None:  # noqa
            nonlocal bar, bar_message
            bar.set_description(bar_message)
            # N.B. Do NOT do a bar.disable = True before this or it messes up output on
            # multiple calls; found out the hard way; a couple hour will never get back :-/
            bar.close()
        def done() -> Optional[str]:  # noqa
            nonlocal ncallbacks, upload_done, printf
            if ncallbacks == 0:
                upload_file_callback(file_size)
            cleanup()
            if upload_done:
                printf(upload_done)
        def abort_upload() -> None:  # noqa
            nonlocal should_abort
            with thread_lock:
                should_abort = True
        upload_file_callback_type = namedtuple("upload_file_callback",
                                               ["function", "pause_output", "resume_output",
                                                "cleanup", "done", "abort_upload"])
        return upload_file_callback_type(upload_file_callback, pause_output, resume_output, cleanup, done, abort_upload)

    def get_uploaded_file_info() -> Optional[dict]:
        nonlocal aws_credentials, s3_bucket, s3_key
        try:
            s3 = boto3.client("s3", **aws_credentials)
            s3_file_head = s3.head_object(Bucket=s3_bucket, Key=s3_key)
            if (s3_file_etag := s3_file_head["ETag"]) and s3_file_etag.startswith('"') and s3_file_etag.endswith('"'):
                s3_file_etag = s3_file_etag[1:-1]
            return {
                "modified": format_datetime(s3_file_head["LastModified"]),
                "size": s3_file_head["ContentLength"],
                "checksum": s3_file_etag
            }
        except Exception:
            return None

    def verify_with_any_already_uploaded_file() -> None:
        nonlocal file, file_size, file_checksum
        if existing_file_info := get_uploaded_file_info():
            # The file we are uploading already exists in S3.
            printf(f"WARNING: This file already exists in AWS S3:"
                   f" {format_size(existing_file_info['size'])} | {existing_file_info['modified']}")
            if files_appear_to_be_the_same := (existing_file_info["size"] == file_size):
                # File sizes are the same. See if these files appear to be the same according
                # to their checksums; but if it is a big file prompt the user first to check.
                if file_checksum:
                    compare_checksums = True
                elif not (compare_checksums := existing_file_info["size"] < _BIG_FILE_SIZE):
                    if yes_or_no("Do you want to see if these files appear to be exactly the same?"):
                        compare_checksums = True
                    else:
                        files_appear_to_be_the_same = None
                if compare_checksums:
                    if not file_checksum:
                        file_checksum = get_file_md5_like_aws_s3_etag(file)
                    if file_checksum != existing_file_info["checksum"]:
                        files_appear_to_be_the_same = False
                        file_difference = f" | checksum: {file_checksum} vs {existing_file_info['checksum']}"
            else:
                file_difference = f" | size: {file_size} vs {existing_file_info['size']}"
            if files_appear_to_be_the_same is False:
                printf(f"These files appear to be different{file_difference}")
            elif files_appear_to_be_the_same is True:
                printf(f"These files appear to be the same | checksum: {existing_file_info['checksum']}")
            if not yes_or_no("Do you want to continue with this upload anyways?"):
                printf(f"Skipping upload of {os.path.basename(file)} ({format_size(file_size)}) to: {s3_uri}")
                return False
        return True

    def verify_uploaded_file() -> bool:
        nonlocal file_size
        printf("Verifying upload ... ", end="")
        if file_info := get_uploaded_file_info():
            if file_info["size"] != file_size:
                printf(f"WARNING: File size mismatch ▶ {file_size} vs {file_info['size']}")
                return False
            if file_checksum and file_info["checksum"] and file_checksum != file_info["checksum"]:
                printf(f"WARNING: File checksum mismatch ▶ {file_checksum} vs {file_info['checksum']}")
                return False
            printf("OK")
            return True
        printf("WARNING: Cannot verify.")
        return False

    def define_interrupt_handler() -> None:
        nonlocal catch_interrupt
        def handle_interrupt(signum, frame) -> None:  # noqa
            # Note that an interrupt does not actually stop
            # the upload thread(s) from continuing to run.
            def handle_secondary_interrupt(signum, frame):  # noqa
                printf("\nEnter 'yes' to really quit (exit) or CTRL-\\ ...")
            nonlocal upload_file_callback
            signal.signal(signal.SIGINT, handle_secondary_interrupt)
            if upload_file_callback:
                upload_file_callback.pause_output()
            if yes_or_no("\nATTENTION! You have interrupted this upload. Do you want to stop (exit)?"):
                restore_interrupt_handler()
                if upload_file_callback:
                    upload_file_callback.cleanup()
                printf("Aborting upload ...")
                if upload_file_callback:
                    upload_file_callback.abort_upload()
                    return
                exit(1)
            signal.signal(signal.SIGINT, handle_interrupt)
            if upload_file_callback:
                upload_file_callback.resume_output()
        def restore_interrupt_handler() -> None:  # noqa
            nonlocal previous_interrupt_handler
            if previous_interrupt_handler:
                signal.signal(signal.SIGINT, previous_interrupt_handler)
        if catch_interrupt:
            previous_interrupt_handler = signal.signal(signal.SIGINT, handle_interrupt)
        else:
            previous_interrupt_handler = None
        interrupt_handler_type = namedtuple("interrupt_handler", ["restore"])
        return interrupt_handler_type(restore_interrupt_handler)

    if print_preamble:
        printf(f"Uploading {os.path.basename(file)} ({format_size(file_size)}) to: {s3_uri}")

    if verify_upload and not verify_with_any_already_uploaded_file():
        return False

    upload_file_callback = define_upload_file_callback() if print_progress else None
    interrupt_handler = define_interrupt_handler()

    upload_aborted = False
    s3 = boto3.client("s3", **aws_credentials)
    with open(file, "rb") as f:
        try:
            s3.upload_fileobj(f, s3_bucket, s3_key,
                              Callback=upload_file_callback.function if upload_file_callback else None)
        except Exception:
            printf(f"Upload aborted: {file}")
            upload_aborted = True

    if upload_file_callback:
        upload_file_callback.done()

    if not upload_aborted and verify_upload:
        verify_uploaded_file()

    interrupt_handler.restore()

    return not upload_aborted