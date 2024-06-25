import argparse
from base64 import b64decode as base64_decode
from collections import namedtuple
import datetime
import os
import pytz
import signal
import sys
import yaml
from typing import Optional
from dcicutils.datetime_utils import format_datetime
from dcicutils.file_utils import get_file_size
from dcicutils.misc_utils import format_size
from dcicutils.progress_bar import ProgressBar
from submitr.rclone import (
    AmazonCredentials, GoogleCredentials,
    RCloneStore, RCloneAmazon, RCloneGoogle,
    RCloner, cloud_path
)
from submitr.rclone.rclone_installation import RCloneInstallation
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
                      help="AWS credentials file for source and/or destination.", default=None)
    args.add_argument("--amazon-credentials-source", "-aws-source",
                      help="AWS credentials file for for source.", default=None)
    args.add_argument("--amazon-credentials-destination", "-aws-destination",
                      help="AWS credentials file for for destination.", default=None)
    args.add_argument("--amazon-temporary-credentials", "-tc", nargs="?",
                      help="Use Amazon temporary/session credentials for source/destination.", const=True, default=None)
    args.add_argument("--amazon-temporary-credentials-source", "-tc-source", nargs="?",
                      help="Use Amazon temporary/session credentials for source.", const=True, default=None)
    args.add_argument("--amazon-temporary-credentials-destination", "-tc-destination", nargs="?",
                      help="Use Amazon temporary/session credentials for destination.", const=True, default=None)
    args.add_argument("--show-temporary-credentials-policy", "-tcp", action="store_true",
                      help="Show temporary credentials policy.", default=False)
    args.add_argument("--google-credentials", "-gcs", help="Amazon or Google service account file.")
    args.add_argument("--google-credentials-source", "-gcss", help="Amazon or Google service account file.")
    args.add_argument("--google-credentials-destination", "-gcsd", help="Amazon or Google service account file.")
    args.add_argument("--amazon-kms-key", "-kms", help="Amazon KMS key ID for source and/or destination.", default=None)
    args.add_argument("--amazon-kms-key-source", "-kms-source", help="Amazon KMS key ID for source.", default=None)
    args.add_argument("--amazon-kms-key-destination", "-kms-destination",
                      help="Amazon KMS key ID for destination.", default=None)
    args.add_argument("--noprogress", action="store_true", help="Do not show progress bar.", default=False)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args.add_argument("--debug", action="store_true", help="Debug output.", default=False)
    args = args.parse_args()

    RCloneInstallation.verify_installation(progress=not args.noprogress)

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
        destination = args.destination.strip() if args.destination else None
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
        if cloud_path.is_bucket_only(cloud_path.normalize(source)):
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
                usage(f"No source base name found: {source}")  # should not happen
    else:
        destination = os.path.abspath(destination) if destination else None

    # Amazon credentials are split into source and destination because we may
    # specify either/both/none as temporary credentials; and also because we may
    # by copying from one S3 account to another (this is still TODO).
    credentials_source_amazon = None
    credentials_destination_amazon = None

    # Google credentials are split into source and destination because we may
    # by copying from one GCS account to another (this is still TODO).
    credentials_source_google = None
    credentials_destination_google = None

    if is_source_amazon:

        if not args.amazon_credentials_source:
            args.amazon_credentials_source = args.amazon_credentials
        if not args.amazon_kms_key_source:
            args.amazon_kms_key_source = args.amazon_kms_key

        if not (credentials_source_amazon := AmazonCredentials.obtain(args.amazon_credentials_source,
                                                                      kms_key_id=args.amazon_kms_key_source)):
            usage(f"Cannot find AWS credentials.")
        if not credentials_source_amazon.ping():
            usage(f"Given AWS credentials appear to be invalid.")

        if not (temporary_credentials_source_amazon := args.amazon_temporary_credentials_source):
            temporary_credentials_source_amazon = args.amazon_temporary_credentials
        if temporary_credentials_source_amazon == "-":
            # Special case of untargeted (to any bucket/key) temporary credentials.
            temporary_credentials_source_amazon = (
                generate_amazon_temporary_credentials(credentials_source_amazon,
                                                      kms_key_id=args.amazon_kms_key_source))
        elif temporary_credentials_source_amazon:
            bucket = key = None
            if temporary_credentials_source_amazon is True:
                # Default if no argument give for the -tc-source option is to target
                # the temporary credentials to the specified (S3) source bucket/key.
                bucket, key = cloud_path.bucket_and_key(source)
            else:
                # Or allow targeting the temporary credentials to a specified bucket/key.
                bucket, key = cloud_path.bucket_and_key(temporary_credentials_source_amazon)
            if bucket:
                temporary_credentials_source_amazon = (
                    generate_amazon_temporary_credentials(credentials_source_amazon,
                                                          bucket=bucket, key=key,
                                                          kms_key_id=args.amazon_kms_key_source))
            else:
                temporary_credentials_source_amazon = None
        if temporary_credentials_source_amazon:
            credentials_source_amazon = temporary_credentials_source_amazon

    if is_destination_amazon:

        if not args.amazon_credentials_destination:
            args.amazon_credentials_destination = args.amazon_credentials
        if not args.amazon_kms_key_destination:
            args.amazon_kms_key_destination = args.amazon_kms_key

        if not (credentials_destination_amazon := AmazonCredentials.obtain(args.amazon_credentials_destination,
                                                                           kms_key_id=args.amazon_kms_key_destination)):
            usage(f"Cannot find AWS credentials.")
        if not credentials_destination_amazon.ping():
            usage(f"Given AWS credentials appear to be invalid.")

        if not (temporary_credentials_destination_amazon := args.amazon_temporary_credentials_destination):
            temporary_credentials_destination_amazon = args.amazon_temporary_credentials
        if temporary_credentials_destination_amazon == "-":
            # Special case of untargeted (to any bucket/key) temporary credentials.
            temporary_credentials_destination_amazon = (
                generate_amazon_temporary_credentials(credentials_destination_amazon,
                                                      kms_key_id=args.amazon_kms_key_destination))
        elif temporary_credentials_destination_amazon:
            bucket = key = None
            if temporary_credentials_destination_amazon is True:
                # Default if no argument give for the -tc-destination option is to target
                # the temporary credentials to the specified (S3) destination bucket/key.
                bucket, key = cloud_path.bucket_and_key(destination)
            else:
                # Or allow targeting the temporary credentials to a specified bucket/key.
                bucket, key = cloud_path.bucket_and_key(temporary_credentials_destination_amazon)
            if bucket:
                temporary_credentials_destination_amazon = (
                    generate_amazon_temporary_credentials(credentials_destination_amazon,
                                                          bucket=bucket, key=key,
                                                          kms_key_id=args.amazon_kms_key_destination))
            else:
                temporary_credentials_destination_amazon = None
        if temporary_credentials_destination_amazon:
            credentials_destination_amazon = temporary_credentials_destination_amazon

    if is_source_google:

        if not args.google_credentials_source:
            args.google_credentials_source = args.google_credentials

        if ((google_credentials_source := args.google_credentials_source) or
            (google_credentials_source := os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))):  # noqa
            if not (credentials_source_google := GoogleCredentials.obtain(google_credentials_source)):
                usage(f"Cannot create GCS credentials from specified value: {args.google}")
        elif RCloneGoogle.is_google_compute_engine():
            credentials_source_google = GoogleCredentials()
        else:
            usage("No GCP credentials specified.")
        if not credentials_source_google.ping():
            usage(f"Given GCS credentials appear to be invalid.")

    if is_destination_google:

        if not args.google_credentials_destination:
            args.google_credentials_destination = args.google_credentials

        if ((google_credentials_destination := args.google_credentials_destination) or
            (google_credentials_destination := os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))):  # noqa
            if not (credentials_destination_google := GoogleCredentials.obtain(google_credentials_destination)):
                usage(f"Cannot create GCS credentials from specified value: {args.google}")
        elif RCloneGoogle.is_google_compute_engine():
            credentials_destination_google = GoogleCredentials()
        else:
            usage("No GCP credentials specified.")
        if not credentials_destination_google.ping():
            usage(f"Given GCS credentials appear to be invalid.")

    if copy:
        sys.exit(main_copy(source, destination,
                           credentials_source_amazon=credentials_source_amazon,
                           credentials_destination_amazon=credentials_destination_amazon,
                           credentials_source_google=credentials_source_google,
                           credentials_destination_google=credentials_destination_google,
                           copyto=copyto, progress=not args.noprogress,
                           show_temporary_credentials_policy=args.show_temporary_credentials_policy,
                           verbose=args.verbose, debug=args.debug))
    elif info:
        sys.exit(main_info(source, destination,
                           credentials_source_amazon=credentials_source_amazon,
                           credentials_destination_amazon=credentials_destination_amazon,
                           credentials_source_google=credentials_source_google,
                           credentials_destination_google=credentials_destination_google,
                           show_temporary_credentials_policy=args.show_temporary_credentials_policy,
                           verbose=args.verbose))


def main_copy(source: str, destination: str,
              credentials_source_amazon: Optional[AmazonCredentials] = None,
              credentials_destination_amazon: Optional[AmazonCredentials] = None,
              credentials_source_google: Optional[GoogleCredentials] = None,
              credentials_destination_google: Optional[GoogleCredentials] = None,
              copyto: bool = True, progress: bool = False,
              show_temporary_credentials_policy: bool = False,
              verbose: bool = False, debug: bool = False) -> None:

    source_config = None
    if is_amazon_path(source):
        source = cloud_path.normalize(source, preserve_prefix=True)
        if not credentials_source_amazon:
            usage("No AWS credentials specified or found (in environment).")
        source_config = RCloneAmazon(credentials_source_amazon)
    elif is_google_path(source):
        source = cloud_path.normalize(source, preserve_prefix=True)
        if not credentials_source_google:
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
            source_config = RCloneGoogle(credentials_source_google)

    destination_config = None
    if is_amazon_path(destination):
        destination = cloud_path.normalize(destination, preserve_prefix=True)
        if not credentials_destination_amazon:
            usage("No AWS credentials specified or found (in environment).")
        destination_config = RCloneAmazon(credentials_destination_amazon)
    elif is_google_path(destination):
        destination = cloud_path.normalize(destination, preserve_prefix=True)
        if not credentials_destination_google:
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
            destination_config = RCloneGoogle(credentials_destination_google)

    def define_progress_callback(source_target: RCloneStore, source: str) -> None:
        nonlocal source_config, destination_config
        process_info = {}
        def interrupt_stop(bar: ProgressBar):  # noqa
            nonlocal process_info
            if pid := process_info.get("pid"):
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            return False
        nbytes_total = source_target.file_size(source) if source_target else get_file_size(source)
        progress_bar = ProgressBar(total=nbytes_total,
                                   description="Transferring" if source_config and destination_config else "Copying",
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
        if isinstance(source_config, RCloneAmazon):
            print_amazon_credentials_info(source_config, prefix="Source ")
        elif isinstance(source_config, RCloneGoogle):
            print_google_credentials_info(source_config, prefix="Source ")
        if isinstance(destination_config, RCloneAmazon):
            print_amazon_credentials_info(destination_config, prefix="Destination ")
        elif isinstance(destination_config, RCloneGoogle):
            print_google_credentials_info(destination_config, prefix="Destination ")

    if show_temporary_credentials_policy:
        if credentials_source_amazon.policy:
            print("AWS temporary source credentials policy:")
            print_amazon_temporary_credentials_policy(credentials_source_amazon.policy)
        if credentials_destination_amazon.policy:
            print("AWS temporary destination credentials policy:")
            print_amazon_temporary_credentials_policy(credentials_destination_amazon.policy)

    progress_callback = define_progress_callback(source_config, source) if progress is True else None
    rcloner = RCloner(source=source_config, destination=destination_config)
    result = output = None
    try:
        result, output = rcloner.copy(source, destination, copyto=copyto,
                                      nochecksum=True,
                                      progress=progress_callback.function if progress_callback else None,
                                      process_info=progress_callback.process if progress_callback else None,
                                      return_output=True)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    if progress:
        print()

    if result is True:
        if verbose:
            print(f"OK")
        if debug:
            print(f"DEBUG: rclone output below:")
            for line in output:
                print(line)
        else:
            print()
        sys.exit(0)
    else:
        access_denied = len([line for line in output if "accessdenied" in line.lower().replace(" ", "")]) > 0
        if access_denied:
            print(f"ERROR: {'Access Denied' if access_denied else ''}", end="")
        else:
            print(f"ERROR", end="")
        if debug:
            print(f"DEBUG: rclone output below ...")
            for line in output:
                print(line)
        else:
            print()
        sys.exit(1)


def main_info(source: str, destination: Optional[str] = None,
              credentials_source_amazon: Optional[AmazonCredentials] = None,
              credentials_destination_amazon: Optional[AmazonCredentials] = None,
              credentials_source_google: Optional[GoogleCredentials] = None,
              credentials_destination_google: Optional[GoogleCredentials] = None,
              show_temporary_credentials_policy: bool = False,
              verbose: bool = False):

    if source:
        if destination:
            print("")
        print_info(source,
                   credentials_amazon=credentials_source_amazon,
                   credentials_google=credentials_source_google,
                   show_temporary_credentials_policy=show_temporary_credentials_policy)
    if destination:
        if source:
            print("")
        print_info(destination,
                   credentials_amazon=credentials_destination_amazon,
                   credentials_google=credentials_destination_google,
                   show_temporary_credentials_policy=show_temporary_credentials_policy)


def generate_amazon_temporary_credentials(amazon_credentials: AmazonCredentials,
                                          *args, **kwargs) -> Optional[AmazonCredentials]:
    return AwsS3(amazon_credentials).generate_temporary_credentials(*args, **kwargs) if amazon_credentials else None


def is_amazon_path(path: str):
    return RCloneStoreRegistry.lookup(path) == RCloneAmazon


def is_google_path(path: str):
    return RCloneStoreRegistry.lookup(path) == RCloneGoogle


def print_info(target: str,
               credentials_amazon: Optional[AmazonCredentials],
               credentials_google: Optional[GoogleCredentials],
               show_temporary_credentials_policy: bool = False) -> None:

    if not target:
        return
    if is_amazon_path(target):
        if not credentials_amazon:
            usage(f"No AWS credentials specified for: {target}")
        print(f"AWS S3 path: {target}")
        amazon = RCloneAmazon(credentials_amazon)
        print_amazon_credentials_info(amazon)
        if show_temporary_credentials_policy:
            if credentials_amazon.policy:
                print("AWS temporary credentials policy:")
                print_amazon_temporary_credentials_policy(credentials_amazon.policy)
        print_info_via_rclone(target, amazon)
    elif is_google_path(target):
        if not credentials_google:
            usage(f"No GCS credentials specified for: {target}")
        print(f"GCS path: {target}")
        google = RCloneGoogle(credentials_google)
        print_google_credentials_info(google)
        print_info_via_rclone(target, google)


def print_info_via_rclone(target: str, rclone_store: RCloneStore) -> None:

    size = rclone_store.file_size(target)
    checksum = rclone_store.file_checksum(target)
    if isinstance(rclone_store, RCloneAmazon):
        s3 = AwsS3(rclone_store.credentials)
        checksum_via_aws_boto = s3.file_checksum(target)
        checksum_etag_via_boto = s3.file_checksum(target, etag=True)
        kms_key_via_boto = s3.file_kms_key(target)
        metadata_via_boto = s3.file_metadata(target)
    else:
        checksum_via_aws_boto = None
        checksum_etag_via_boto = None
        kms_key_via_boto = None
        metadata_via_boto = None
    modified = rclone_store.file_modified(target, formatted=True)
    formatted_size = format_size(size)
    print(f"Bucket: {cloud_path.bucket(target)}")
    print(f"Key: {cloud_path.basename(target)}")
    print(f"Size: {format_size(size)}{f' ({size} bytes)' if '.' in formatted_size is not None else ''}")
    print(f"Modified: {modified}")
    print(f"Checksum: {checksum}")
    if checksum_via_aws_boto:
        print(f"Checksum (non-rclone): {checksum_via_aws_boto}")
    if checksum_etag_via_boto:
        print(f"Etag (non-rclone): {checksum_etag_via_boto}")
    if kms_key_via_boto:
        print(f"KMS Key (non-rclone): {kms_key_via_boto}")
    if info := rclone_store.file_info(target):
        if metadata := info.get("metadata"):
            print(f"Metadata: [{len(metadata)}]")
            for key in {key: metadata[key] for key in sorted(metadata)}:
                extra_info = ""
                if key in ["mtime", "md5-timestamp"]:
                    try:
                        timestamp = float(metadata_via_boto[key])
                        if (timestamp := format_datetime(datetime.datetime.fromtimestamp(timestamp,
                                                                                         tz=pytz.UTC), ms=True)):
                            extra_info = f" {chars.rarrow} {timestamp}"
                    except Exception:
                        pass
                print(f"- {key}: {metadata[key]}{extra_info}")
    if metadata_via_boto:
        print(f"Metadata (non-rclone): [{len(metadata_via_boto)}]")
        for key in {key: metadata_via_boto[key] for key in sorted(metadata_via_boto)}:
            extra_info = ""
            if key == "md5chksum":
                extra_info = f" {chars.rarrow} {base64_decode(metadata_via_boto[key]).hex()}"
            elif key in ["mtime", "md5-timestamp"]:
                try:
                    timestamp = float(metadata_via_boto[key])
                    if timestamp := format_datetime(datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC), ms=True):
                        extra_info = f" {chars.rarrow} {timestamp}"
                except Exception:
                    pass
            print(f"- {key}: {metadata_via_boto[key]}{extra_info}")


def print_amazon_credentials_info(store: RCloneAmazon, prefix: Optional[str] = "") -> None:
    if isinstance(store, RCloneAmazon) and store.credentials:
        if store.credentials.credentials_file:
            print(f"{prefix}AWS credentials file: {store.credentials.credentials_file}")
        print(f"{prefix}AWS access key ID: {store.credentials.access_key_id}")
        if store.credentials.kms_key_id:
            print(f"{prefix}AWS KMS key ID: {store.credentials.kms_key_id}")


def print_google_credentials_info(store: RCloneGoogle, prefix: Optional[str] = "") -> None:
    if isinstance(store, RCloneGoogle) and store.credentials:
        if store.credentials.service_account_file:
            print(f"{prefix}GCS service account file: {store.credentials.service_account_file}")
            if store.project:
                print(f"{prefix}GCS project ID: {store.project}")


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
    sys.exit(1)


if __name__ == "__main__":
    main()
