import boto3
from collections import namedtuple
import os
import signal
import sys
import time
from tqdm import tqdm
from typing import Callable, Optional
from dcicutils.command_utils import yes_or_no
from .utils import get_s3_bucket_and_key_from_s3_uri, format_duration, format_size


def upload_file_to_aws_s3(file: str, s3_uri: str,
                          aws_credentials: Optional[dict] = None,
                          aws_kms_key_id: Optional[str] = None,
                          print_progress: bool = True,
                          print_preamble: bool = True,
                          print_function: Optional[Callable] = print,
                          verify_upload: bool = True,
                          catch_interrupt: bool = True) -> bool:

    print_preamble = False
    verify_upload = False
    if not isinstance(file, str) or not file or not isinstance(s3_uri, str) or not s3_uri:
        return False
    if not os.path.exists(file):
        return False

    s3_bucket, s3_key = get_s3_bucket_and_key_from_s3_uri(s3_uri)
    if not s3_bucket or not s3_key:
        return False

    printf = print_function if callable(print_function) else print

    if isinstance(aws_credentials, dict):
        s3_client_args = {
            "region_name": aws_credentials.get("AWS_DEFAULT_REGION") or "us-east-1",
            "aws_access_key_id": aws_credentials.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": aws_credentials.get("AWS_SECRET_ACCESS_KEY"),
            "aws_session_token": aws_credentials.get("AWS_SESSION_TOKEN") or aws_credentials.get("AWS_SECURITY_TOKEN")
        }
    else:
        s3_client_args = {}
    if aws_kms_key_id:
        s3_client_args["SSEKMSKeyId"] = aws_kms_key_id

    nbytes_file = os.path.getsize(file)

    def define_upload_file_callback() -> None:
        nonlocal file
        started = time.time()
        nbytes_transferred = 0
        ncallbacks = 0
        upload_done = None
        bar_message = "▶ Upload progress"
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} | {rate_fmt} | {elapsed}{postfix} | ETA: {remaining}"
        bar = tqdm(total=max(nbytes_file, 1), desc=bar_message,
                   dynamic_ncols=True, bar_format=bar_format, unit="", file=sys.stdout)
        def upload_file_callback(nbytes_chunk: int) -> None:  # noqa
            # The execution of this may be in any number of child threads due to the way upload_fileobj
            # works; we do not create the progress bar until the upload actually starts because if we
            # do we get some initial bar output file.
            nonlocal s3_client_args, s3_bucket, s3_key, printf
            nonlocal started, nbytes_file, nbytes_transferred, ncallbacks, upload_done, bar
            ncallbacks += 1
            nbytes_transferred += nbytes_chunk
            # We do not use bar.update(nbytes_chunk) but rather set the total work done (bar.n)
            # so far to nbytes_transferred, so that counts add up right when interrupted; during
            # interrupt handling (outside in caller/main-thread) this callback continues executing,
            # as upload_fileobj continues its work; we just (during interrupt handling) pause/disable
            # the output of the progress bar; but bar.update(0) still needs to be called so it takes.
            bar.n = nbytes_transferred
            bar.update(0)
            if nbytes_transferred >= nbytes_file:
                # This set_description seems to be need make sure the
                # last bit is flushed out; in the case of interrupt.
                bar.set_description(bar_message)
                cleanup()
                duration = time.time() - started
                upload_done = (f"Upload done: {format_size(nbytes_transferred)}"
                               f" in {format_duration(duration)}"
                               f" | {format_size(nbytes_transferred / duration)} per second ◀")
        def pause_output() -> None:  # noqa
            nonlocal bar
            bar.disable = True
        def resume_output() -> None:  # noqa
            nonlocal bar
            bar.disable = False
        def cleanup() -> None:  # noqa
            nonlocal bar
            # N.B. Do NOT do a bar.disable = True before this or it messes up output on
            # multiple calls; found out the hard way; a couple hour will never get back :-/
            bar.close()
        def done() -> Optional[str]:  # noqa
            nonlocal bar, ncallbacks, upload_done
            if ncallbacks == 0:
                upload_file_callback(max(nbytes_file, 1))
            bar.set_description(bar_message)
            cleanup()
            if upload_done:
                printf(upload_done)
        upload_file_callback_type = namedtuple("upload_file_callback",
                                               ["function", "pause_output", "resume_output", "cleanup", "done"])
        return upload_file_callback_type(upload_file_callback, pause_output, resume_output, cleanup, done)

    def verify_upload_file() -> None:
        nonlocal file, nbytes_file, s3_client_args, s3_bucket, s3_key
        printf("Verifying upload ... ", end="")
        # If we don't recreate a new s3 client object we get the previous file size if any.
        s3_client = boto3.client("s3", **s3_client_args)
        s3_file_head = s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
        if (content_length := s3_file_head.get("ContentLength")) == nbytes_file:
            printf("OK")
        else:
            printf(f"ERROR (file size inconsistency: {nbytes_file} vs. {content_length})")

    if print_preamble is True:
        printf(f"Uploading {os.path.basename(file)} ({format_size(nbytes_file)}) to: {s3_uri}")

    upload_file_callback = define_upload_file_callback() if print_progress else None

    previous_interrupt_handler = None
    def handle_interrupt(signum, frame):  # noqa
        nonlocal previous_interrupt_handler, upload_file_callback
        signal.signal(signal.SIGINT, lambda signum, frame: None)
        if upload_file_callback:
            upload_file_callback.pause_output()
        if yes_or_no("\nATTENTION! You have interrupted this upload. Do you want to stop (exit)?"):
            signal.signal(signal.SIGINT, previous_interrupt_handler)
            if upload_file_callback:
                upload_file_callback.cleanup()
            printf("Upload aborted.")
            exit(1)
        signal.signal(signal.SIGINT, handle_interrupt)
        if upload_file_callback:
            upload_file_callback.resume_output()

    if catch_interrupt is True:
        previous_interrupt_handler = signal.signal(signal.SIGINT, handle_interrupt)

    s3_client = boto3.client("s3", **s3_client_args)
    with open(file, "rb") as f:
        s3_client.upload_fileobj(f, s3_bucket, s3_key,
                                 Callback=upload_file_callback.function if upload_file_callback else None)

    if upload_file_callback:
        upload_file_callback.done()

    if verify_upload:
        verify_upload_file()

    if catch_interrupt is True:
        signal.signal(signal.SIGINT, previous_interrupt_handler)

    return True
