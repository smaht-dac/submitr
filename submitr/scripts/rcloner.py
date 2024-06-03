import argparse
from collections import namedtuple
import os
import signal
from typing import Optional
from dcicutils.file_utils import get_file_size
from dcicutils.misc_utils import format_size
from dcicutils.progress_bar import ProgressBar
from submitr.rclone import (
    AmazonCredentials, GoogleCredentials,
    RCloneTarget, RCloneAmazon, RCloneGoogle,
    RCloner, cloud_path
)
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials
from submitr.rclone.testing.rclone_utils_for_testing_google import GcpCredentials
from submitr.utils import chars

# Little command-line utility to interactively test out rclone support code in smaht-submitr.


def main() -> None:
    args = argparse.ArgumentParser(description="Test utility for rclone support in smaht-submitr.")
    args.add_argument("action", help="Action: copy or info.", default=None)
    args.add_argument("source", help="Source file or cloud bucket/key.", default=None)
    args.add_argument("destination", nargs="?",
                      help="Destination file/directory or cloud bucket/key.", default=None)
    args.add_argument("--amazon-credentials", "-aws",
                      help="AWS environment; for ~/.aws_test.{env}/credentials file.", default=None)
    args.add_argument("--amazon-temporary-credentials", "-tc", nargs="?",
                      help="Use Amazon temporary/session credentials for source/destination.", const=True, default=None)
    args.add_argument("--amazon-temporary-credentials-source", "-tcs", nargs="?",
                      help="Use Amazon temporary/session credentials for source.", const=True, default=None)
    args.add_argument("--amazon-temporary-credentials-destination", "-tcd", nargs="?",
                      help="Use Amazon temporary/session credentials for destination.", const=True, default=None)
    args.add_argument("--google-credentials", "-gcs", help="Amazon or Google configuration file.")
    args.add_argument("--kms", help="Amazon KMS key ID.", default=None)
    args.add_argument("--progress", action="store_true", help="Show progress bar.", default=False)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args.add_argument("--debug", action="store_true", help="Debug output.", default=False)
    args = args.parse_args()

    action = args.action.lower()
    copy = (action == "copy") or (action == "cp")
    info = (action == "info")

    if copy:
        if not args.source:
            usage(f"Must specify a source for copy.")
        if not args.destination:
            usage(f"Must specify destination for copy.")
    elif info:
        if not args.source:
            usage(f"Must specify a source for copy.")
    else:
        usage("Must specify copy or info.")

    is_source_amazon = cloud_path.is_amazon(args.source)
    is_source_google = cloud_path.is_google(args.source)
    is_source_cloud = is_source_amazon or is_source_google
    is_destination_amazon = cloud_path.is_amazon(args.destination)
    is_destination_google = cloud_path.is_google(args.destination)
    is_destination_cloud = is_destination_amazon or is_destination_google

    if is_source_cloud:
        if args.source.endswith(cloud_path.separator):
            usage("May not specify a folder/directory as a source; only single key/file allowed.")
        if not cloud_path.has_separator(cloud_path.normalize(args.source)):
            usage("May not specify just a bucket as a source; only single key/file allowed.")
    if is_destination_cloud:
        if args.destination.endswith(cloud_path.separator):
            # Special case to treat a destination ending
            # in a slash as a directory (as does aws s3 cp);
            # unless of course copyto is explicitly specified.
            if source_basename := cloud_path.basename(cloud_path.normalize(args.source)):
                args.destination += source_basename
                copyto = True
            else:
                copyto = False
        else:
            copyto = True

    # Amazon credentials are split into source and destination
    # because we may specify either/both/none as temporary credentials.
    credentials_source_amazon = None
    credentials_destination_amazon = None
    credentials_google = None

    if is_source_amazon or is_destination_amazon:

        credentials_amazon = None
        if ((amazon_credentials := args.amazon_credentials) or
            (amazon_credentials := os.environ.get("AWS_SHARED_CREDENTIALS_FILE"))):
            if not (credentials_amazon := AwsCredentials.from_file(amazon_credentials)):
                usage(f"Cannot create AWS credentials from specified value: {args.amazon}")
        else:
            credentials_amazon = AwsCredentials.from_environment_variables()
        if not credentials_amazon.access_key_id:
            usage(f"No AWS credentials specified.")
        if not credentials_amazon.ping():
            usage(f"Given AWS credentials appear to be invalid.")

        if is_source_amazon:
            if not (temporary_credentials_source_amazon := args.amazon_temporary_credentials_source):
                temporary_credentials_source_amazon = args.amazon_temporary_credentials
            if temporary_credentials_source_amazon == "-":
                # Special case of untargeted (to any bucket/key) temporary credentials.
                temporary_credentials_source_amazon = (
                    credentials_amazon.generate_temporary_credentials(kms_key_id=args.kms))
            elif temporary_credentials_source_amazon:
                bucket = key = None
                if temporary_credentials_source_amazon is True:
                    # Default if no argument give for the -tcd option is to target
                    # the temporary credentials to the specified (S3) source bucket/key.
                    bucket, key = cloud_path.bucket_and_key(args.source)
                else:
                    # Or allow targeting the temporary credentials to a specified bucket/key.
                    bucket, key = cloud_path.bucket_and_key(temporary_credentials_source_amazon)
                if bucket:
                    temporary_credentials_source_amazon = (
                        credentials_amazon.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=args.kms))
                else:
                    temporary_credentials_source_amazon = None
            if temporary_credentials_source_amazon:
                credentials_source_amazon = temporary_credentials_source_amazon
            else:
                credentials_source_amazon = credentials_amazon

        if is_destination_amazon:
            if not (temporary_credentials_destination_amazon := args.amazon_temporary_credentials_destination):
                temporary_credentials_destination_amazon = args.amazon_temporary_credentials
            if temporary_credentials_destination_amazon == "-":
                # Special case of untargeted (to any bucket/key) temporary credentials.
                temporary_credentials_destination_amazon = (
                    credentials_amazon.generate_temporary_credentials(kms_key_id=args.kms))
            elif temporary_credentials_destination_amazon:
                bucket = key = None
                if temporary_credentials_destination_amazon is True:
                    # Default if no argument give for the -tcd option is to target
                    # the temporary credentials to the specified (S3) destination bucket/key.
                    bucket, key = cloud_path.bucket_and_key(args.destination)
                else:
                    # Or allow targeting the temporary credentials to a specified bucket/key.
                    bucket, key = cloud_path.bucket_and_key(temporary_credentials_destination_amazon)
                if bucket:
                    temporary_credentials_destination_amazon = (
                        credentials_amazon.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=args.kms))
                else:
                    temporary_credentials_destination_amazon = None
            if temporary_credentials_destination_amazon:
                credentials_destination_amazon = temporary_credentials_destination_amazon
            else:
                credentials_destination_amazon = credentials_amazon

        if ((google_credentials := args.google_credentials) or
            (google_credentials := os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))):
            if not (credentials_google := GcpCredentials.from_file(google_credentials)):
                usage(f"Cannot create GCS credentials from specified value: {args.google}")
        elif RCloneGoogle.is_google_compute_engine():
            credentials_google = GcpCredentials()
        else:
            usage("No GCP credentials specified.")
        if not credentials_google.ping():
            usage(f"Given GCS credentials appear to be invalid.")

    if copy:
        exit(main_copy(args.source, args.destination,
                       credentials_source_amazon=credentials_source_amazon,
                       credentials_destination_amazon=credentials_destination_amazon,
                       credentials_google=credentials_google,
                       copyto=copyto, progress=args.progress, verbose=args.verbose))
    elif info:
        exit(main_info(args.source, args.destination,
                       credentials_source_amazon=credentials_source_amazon,
                       credentials_destination_amazon=credentials_destination_amazon,
                       credentials_google=credentials_google,
                       verbose=args.verbose))


def main_copy(source: str, destination: str,
              credentials_source_amazon: Optional[AmazonCredentials] = None,
              credentials_destination_amazon: Optional[AmazonCredentials] = None,
              credentials_google: Optional[GoogleCredentials] = None,
              copyto: bool = True, progress: bool = False, verbose: bool = False) -> None:

    source_config = None
    if cloud_path.is_amazon(source):
        source = cloud_path.normalize(source)
        if not credentials_source_amazon:
            usage("No AWS credentials specified or found (in environment).")
        source_config = RCloneAmazon(credentials_source_amazon)
    elif cloud_path.is_google(source):
        source = cloud_path.normalize(source)
        if not credentials_google:
            if not RCloneGoogle.is_google_compute_engine():
                # No Google credentials AND NOT running on a GCE instance.
                usage("No GCP credentials specified.")
            # OK to create RCloneGoogle with no credentials on a GCE instance.
            source_config = RCloneGoogle()
            if verbose:
                google_project = source_config.project
                print(f"Running from Google Cloud Engine (GCE)"
                      f"{f': {google_project} {chars.check}' if google_project else '.'}")
        else:
            source_config = RCloneGoogle(credentials_google)

    destination_config = None
    if cloud_path.is_amazon(destination):
        destination = cloud_path.normalize(destination)
        if not credentials_destination_amazon:
            usage("No AWS credentials specified or found (in environment).")
        destination_config = RCloneAmazon(credentials_destination_amazon)
    elif cloud_path.is_google(destination):
        destination = cloud_path.normalize(destination)
        if not credentials_google:
            if not RCloneGoogle.is_google_compute_engine():
                # No Google credentials AND NOT running on a GCE instance.
                usage("No GCP credentials specified.")
            # OK to create RCloneGoogle with no credentials on a GCE instance.
            destination_config = RCloneGoogle()
            if verbose:
                google_project = destination_config.project
                print(f"Running from Google Cloud Engine (GCE)"
                      f"{f': {google_project} {chars.check}' if google_project else '.'}")
        else:
            destination_config = RCloneGoogle(credentials_google)

    def define_progress_callback(source_target: RCloneTarget, source: str) -> None:
        process_info = {}
        def interrupt_stop(bar: ProgressBar):  # noqa
            nonlocal process_info
            if pid := process_info.get("pid"):
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            return False
        nbytes_total = source_target.file_size(source) if source_target else get_file_size(source)
        progress_bar = ProgressBar(total=nbytes_total,
                                   description="Copying",
                                   use_byte_size_for_rate=True,
                                   interrupt_stop=interrupt_stop,
                                   interrupt_message="upload")
        def progress_callback(nbytes: int) -> None:  # noqa
            nonlocal progress_bar
            progress_bar.set_progress(nbytes)
        return namedtuple("progress_callback", ["function", "process"])(progress_callback, process_info)
        return progress_callback

    progress_callback = define_progress_callback(source_config, source) if progress is True else None
    rcloner = RCloner(source=source_config, destination=destination_config)
    result, output = rcloner.copy(source, destination, copyto=copyto,
                                  progress=progress_callback.function,
                                  process_info=progress_callback.process,
                                  return_output=True)
    if result is True:
        print("OK", end="")
        if verbose:
            print(f" {chars.rarrow} rclone output below ...")
            for line in output:
                print(line)
        else:
            print()
        exit(0)
    else:
        access_denied = len([line for line in output if "accessdenied" in line.lower().replace(" ", "")]) > 0
        if access_denied:
            print(f"ERROR: {'Access Denied' if access_denied else ''}", end="")
        else:
            print(f"ERROR", end="")
        if verbose:
            print(f" {chars.rarrow} rclone output below ...")
            for line in output:
                print(line)
        else:
            print()
        exit(1)


def main_info(source: str,
              destination: Optional[str] = None,
              credentials_source_amazon: Optional[AmazonCredentials] = None,
              credentials_destination_amazon: Optional[AmazonCredentials] = None,
              credentials_google: Optional[GoogleCredentials] = None,
              verbose: bool = False):

    if source:
        print_info(source,
                   credentials_amazon=credentials_source_amazon,
                   credentials_google=credentials_google)
    if destination:
        print_info(destination,
                   credentials_amazon=credentials_destination_amazon,
                   credentials_google=credentials_google)
    print("")


def print_info(target: str,
               credentials_amazon: Optional[AmazonCredentials],
               credentials_google: Optional[GoogleCredentials]) -> None:

    if not target:
        return
    if cloud_path.is_amazon(target):
        if not credentials_amazon:
            usage(f"No AWS credentials specified for: {target}")
        print("")
        print(f"AWS S3 Target: {target}")
        print_info_via_rclone(target, RCloneAmazon(credentials_amazon))
    elif cloud_path.is_google(target):
        if not credentials_google:
            usage(f"No GCS credentials specified for: {target}")
        print("")
        print(f"GCS Target: {target}")
        print_info_via_rclone(target, RCloneGoogle(credentials_google))


def print_info_via_rclone(target: str, rclone_target: RCloneTarget) -> None:

    size = rclone_target.file_size(target)
    checksum = rclone_target.file_checksum(target)
    modified = rclone_target.file_modified(target, formatted=True)
    formatted_size = format_size(size)
    print(f"Bucket: {cloud_path.bucket(target)}")
    print(f"Key: {cloud_path.key(target)}")
    print(f"Size: {format_size(size)}{f' ({size} bytes)' if '.' in formatted_size else ''}")
    print(f"Modified: {modified}")
    print(f"Checksum: {checksum}")
    if info := rclone_target.file_info(target):
        if metadata := info.get("metadata"):
            print(f"Metadata ({len(metadata)}):")
            for key in {key: metadata[key] for key in sorted(metadata)}:
                print(f"- {key}: {metadata[key]}")


def usage(message: str) -> None:
    print(message)
    exit(1)


if __name__ == "__main__":
    main()
