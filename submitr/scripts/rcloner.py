import argparse
from collections import namedtuple
import os
import signal
import yaml
from typing import Optional
from dcicutils.file_utils import get_file_size
from dcicutils.misc_utils import format_size
from dcicutils.progress_bar import ProgressBar
from submitr.rclone import (
    AmazonCredentials, GoogleCredentials,
    RCloneStore, RCloneAmazon, RCloneGoogle,
    RCloner, cloud_path
)
from submitr.rclone.rclone_store_registry import RCloneStoreRegistry
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsS3
from submitr.utils import chars

# Little command-line utility to interactively exercise our rclone support code in smaht-submitr.
# Only supports Amazon and Google (obviously for now), but meaning these are hard-coded here,
# does not take advantage of generic RCloneStore/RCloneStoreRegistry functionality, as elsewhere.
#
# Examples:
# rcloner cp file s3://bucket/folder/file -aws credentials-file
# rcloner cp file gs://bucket/folder/  -gcs service-account-file
# rcloner cp s3://bucket/folder/file . -aws credentials-file
# rcloner cp gs://bucket/folder/file s3://bucket/folder/file -aws credentials-file -gcs service-account-file
# rcloner cp s3://bucket/folder/file gs://bucket/folder/ -aws credentials-file -gcs service-account-file


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
    args.add_argument("--show-temporary-credentials-policy", "-tcp", action="store_true",
                      help="Show temporary credentials policy.", default=False)
    args.add_argument("--google-credentials", "-gcs", help="Amazon or Google configuration file.")
    args.add_argument("--kms", help="Amazon KMS key ID.", default=None)
    args.add_argument("--noprogress", action="store_true", help="Do not show progress bar.", default=False)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args.add_argument("--debug", action="store_true", help="Debug output.", default=False)
    args = args.parse_args()

    if args.debug:
        os.environ["SMAHT_DEBUG"] = "true"

    action = args.action.lower()
    copy = (action == "copy") or (action == "cp")
    info = (action == "info")

    if copy:
        if not (source := args.source.strip()):
            usage(f"Must specify a source for copy.")
        if not (destination := args.destination.strip()):
            usage(f"Must specify destination for copy.")
    elif info:
        if not (source := args.source.strip()):
            usage(f"Must specify a source for copy.")
        destination = None
    else:
        usage("Must specify copy or info.")

    is_source_amazon = is_amazon_path(source)
    is_source_google = is_google_path(source)
    is_source_cloud = is_source_amazon or is_source_google
    is_destination_amazon = is_amazon_path(destination)
    is_destination_google = is_google_path(destination)
    is_destination_cloud = is_destination_amazon or is_destination_google

    if is_source_cloud:
        if source.endswith(cloud_path.separator):
            usage("May not specify a folder/directory as a source; only single key/file allowed.")
        if not cloud_path.has_separator(cloud_path.normalize(source)):
            usage("May not specify just a bucket as a source; only single key/file allowed.")

    if not is_source_cloud:
        source = os.path.abspath(source)

    copyto = True
    if is_destination_cloud:
        if cloud_path.is_folder(destination) or cloud_path.is_bucket_only(destination):
            # Special case to treat a destination ending in a slash (or just a
            # bucket destination by itself) as a directory (as does aws s3 cp).
            if source_basename := (cloud_path.basename(cloud_path.normalize(source))
                                   if is_source_cloud else os.path.basename(source)):
                destination = cloud_path.join(destination, source_basename, preserve_prefix=True)
            else:
                copyto = False
    else:
        destination = os.path.abspath(destination)

    # Amazon credentials are split into source and destination
    # because we may specify either/both/none as temporary credentials.
    credentials_source_amazon = None
    credentials_destination_amazon = None
    credentials_google = None

    # For AwS temporary credentials if requested, i.e. -tcs and/or -tcd.
    credentials_source_policy_amazon = {}
    credentials_destination_policy_amazon = {}

    if is_source_amazon or is_destination_amazon:

        if not (credentials_amazon := AmazonCredentials.obtain(args.amazon_credentials)):
            usage(f"Cannot find AWS credentials.")
        if not credentials_amazon.ping():
            usage(f"Given AWS credentials appear to be invalid.")

        if is_source_amazon:
            if not (temporary_credentials_source_amazon := args.amazon_temporary_credentials_source):
                temporary_credentials_source_amazon = args.amazon_temporary_credentials
            if temporary_credentials_source_amazon == "-":
                # Special case of untargeted (to any bucket/key) temporary credentials.
                temporary_credentials_source_amazon = (
                    generate_amazon_temporary_credentials(credentials_amazon, kms_key_id=args.kms,
                                                          policy=credentials_source_policy_amazon))
            elif temporary_credentials_source_amazon:
                bucket = key = None
                if temporary_credentials_source_amazon is True:
                    # Default if no argument give for the -tcs option is to target
                    # the temporary credentials to the specified (S3) source bucket/key.
                    bucket, key = cloud_path.bucket_and_key(source)
                else:
                    # Or allow targeting the temporary credentials to a specified bucket/key.
                    bucket, key = cloud_path.bucket_and_key(temporary_credentials_source_amazon)
                if bucket:
                    temporary_credentials_source_amazon = (
                        generate_amazon_temporary_credentials(credentials_amazon,
                                                              bucket=bucket, key=key, kms_key_id=args.kms,
                                                              policy=credentials_source_policy_amazon))
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
                    generate_amazon_temporary_credentials(credentials_amazon, kms_key_id=args.kms,
                                                          policy=credentials_destination_policy_amazon))
            elif temporary_credentials_destination_amazon:
                bucket = key = None
                if temporary_credentials_destination_amazon is True:
                    # Default if no argument give for the -tcd option is to target
                    # the temporary credentials to the specified (S3) destination bucket/key.
                    bucket, key = cloud_path.bucket_and_key(destination)
                else:
                    # Or allow targeting the temporary credentials to a specified bucket/key.
                    bucket, key = cloud_path.bucket_and_key(temporary_credentials_destination_amazon)
                if bucket:
                    temporary_credentials_destination_amazon = (
                        generate_amazon_temporary_credentials(credentials_amazon,
                                                              bucket=bucket, key=key, kms_key_id=args.kms,
                                                              policy=credentials_destination_policy_amazon))
                else:
                    temporary_credentials_destination_amazon = None
            if temporary_credentials_destination_amazon:
                credentials_destination_amazon = temporary_credentials_destination_amazon
            else:
                credentials_destination_amazon = credentials_amazon

    if is_source_google or is_destination_google:
        if ((google_credentials := args.google_credentials) or
            (google_credentials := os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))):  # noqa
            if not (credentials_google := GoogleCredentials.obtain(google_credentials)):
                usage(f"Cannot create GCS credentials from specified value: {args.google}")
        elif RCloneGoogle.is_google_compute_engine():
            credentials_google = GoogleCredentials()
        else:
            usage("No GCP credentials specified.")
        if not credentials_google.ping():
            usage(f"Given GCS credentials appear to be invalid.")

    if copy:
        exit(main_copy(source, destination,
                       credentials_source_amazon=credentials_source_amazon,
                       credentials_destination_amazon=credentials_destination_amazon,
                       credentials_source_policy_amazon=credentials_source_policy_amazon,
                       credentials_destination_policy_amazon=credentials_destination_policy_amazon,
                       credentials_google=credentials_google,
                       copyto=copyto, progress=not args.noprogress,
                       show_temporary_credentials_policy=args.show_temporary_credentials_policy,
                       verbose=args.verbose, debug=args.debug))
    elif info:
        exit(main_info(source, destination,
                       credentials_source_amazon=credentials_source_amazon,
                       credentials_destination_amazon=credentials_destination_amazon,
                       credentials_google=credentials_google,
                       verbose=args.verbose))


def main_copy(source: str, destination: str,
              credentials_source_amazon: Optional[AmazonCredentials] = None,
              credentials_destination_amazon: Optional[AmazonCredentials] = None,
              credentials_source_policy_amazon: Optional[dict] = None,
              credentials_destination_policy_amazon: Optional[dict] = None,
              credentials_google: Optional[GoogleCredentials] = None,
              copyto: bool = True, progress: bool = False,
              show_temporary_credentials_policy: bool = False,
              verbose: bool = False, debug: bool = False) -> None:

    source_config = None
    if is_amazon_path(source):
        source = cloud_path.normalize(source)
        if not credentials_source_amazon:
            usage("No AWS credentials specified or found (in environment).")
        source_config = RCloneAmazon(credentials_source_amazon)
    elif is_google_path(source):
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
    if is_amazon_path(destination):
        destination = cloud_path.normalize(destination)
        if not credentials_destination_amazon:
            usage("No AWS credentials specified or found (in environment).")
        destination_config = RCloneAmazon(credentials_destination_amazon)
    elif is_google_path(destination):
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

    def define_progress_callback(source_target: RCloneStore, source: str) -> None:
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

    if verbose:
        print(f"Source: {source}")
        print(f"Destination: {destination}")

    if show_temporary_credentials_policy:
        if credentials_source_policy_amazon:
            print("AWS temporary source credentials policy:")
            print_amazon_temporary_credentials_policy(credentials_source_policy_amazon)
        if credentials_destination_policy_amazon:
            print("AWS temporary destination credentials policy:")
            print_amazon_temporary_credentials_policy(credentials_destination_policy_amazon)

    progress_callback = define_progress_callback(source_config, source) if progress is True else None
    rcloner = RCloner(source=source_config, destination=destination_config)
    result, output = rcloner.copy(source, destination, copyto=copyto,
                                  progress=progress_callback.function if progress_callback else None,
                                  process_info=progress_callback.process if progress_callback else None,
                                  return_output=True)
    if progress:
        print()

    if result is True:
        if verbose:
            print(f"OK")
        if debug:
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
        if debug:
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


def generate_amazon_temporary_credentials(amazon_credentials: AmazonCredentials,
                                          *args, **kwargs) -> Optional[AmazonCredentials]:
    return AwsS3(amazon_credentials).generate_temporary_credentials(*args, **kwargs) if amazon_credentials else None


def is_amazon_path(path: str):
    return RCloneStoreRegistry.lookup(path) == RCloneAmazon


def is_google_path(path: str):
    return RCloneStoreRegistry.lookup(path) == RCloneGoogle


def print_info(target: str,
               credentials_amazon: Optional[AmazonCredentials],
               credentials_google: Optional[GoogleCredentials]) -> None:

    if not target:
        return
    if is_amazon_path(target):
        if not credentials_amazon:
            usage(f"No AWS credentials specified for: {target}")
        print(f"AWS S3 Target: {target}")
        print_info_via_rclone(target, RCloneAmazon(credentials_amazon))
    elif is_google_path(target):
        if not credentials_google:
            usage(f"No GCS credentials specified for: {target}")
        print("")
        print(f"GCS Target: {target}")
        print_info_via_rclone(target, RCloneGoogle(credentials_google))


def print_info_via_rclone(target: str, rclone_store: RCloneStore) -> None:

    size = rclone_store.file_size(target)
    checksum = rclone_store.file_checksum(target)
    modified = rclone_store.file_modified(target, formatted=True)
    formatted_size = format_size(size)
    print(f"Bucket: {cloud_path.bucket(target)}")
    print(f"Key: {cloud_path.key(target)}")
    print(f"Size: {format_size(size)}{f' ({size} bytes)' if '.' in formatted_size else ''}")
    print(f"Modified: {modified}")
    print(f"Checksum: {checksum}")
    if info := rclone_store.file_info(target):
        if metadata := info.get("metadata"):
            print(f"Metadata ({len(metadata)}):")
            for key in {key: metadata[key] for key in sorted(metadata)}:
                print(f"- {key}: {metadata[key]}")


def print_amazon_temporary_credentials_policy(policy: dict) -> None:
    # Statement:
    # - Action:
    #   - s3:GetObject
    #   - s3:PutObject
    #   Effect: Allow
    #   Resource:
    #   - arn:aws:s3:::smaht-unit-testing-files/test-folder/222TWJLT4-1-IDUDI0055v2_S1_L001_R2_001.fastq.gz
    # - Action: s3:ListBucket
    #   Condition:
    #     StringLike:
    #       s3:prefix:
    #       - test-folder/222TWJLT4-1-IDUDI0055v2_S1_L001_R2_001.fastq.gz
    #   Effect: Allow
    #   Resource: arn:aws:s3:::smaht-unit-testing-files
    # Version: '2012-10-17'
    print(yaml.dump(policy).strip().replace("Statement:\n", ""))


def usage(message: str) -> None:
    print(message)
    exit(1)


if __name__ == "__main__":
    main()
