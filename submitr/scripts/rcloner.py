import argparse
from submitr.rclone import RCloner, RCloneAmazon, RCloneGoogle, cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials
from submitr.rclone.testing.rclone_utils_for_testing_google import GcpCredentials
from dcicutils.misc_utils import format_size

# Little command-line utility to interactively test out rclone support code in smaht-submitr.


def main() -> None:
    args = argparse.ArgumentParser(description="Test utility for rclone support in smaht-submitr.")
    args.add_argument("action", help="Action: copy or info.")
    args.add_argument("source", help="Source file or cloud bucket/key.")
    args.add_argument("destination", nargs="?", help="Destination file/directory or cloud bucket/key.")
    args.add_argument("--amazon", "-aws", help="AWS environment; for ~/.aws_test.{env}/credentials file.")
    args.add_argument("--google", "-gcs", help="Amazon or Google configuration file.")
    args.add_argument("--kms", help="Amazon KMS key ID.")
    args.add_argument("--temporary-credentials", "-tc", nargs="?", help="Amazon KMS key ID.", const=True)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args = args.parse_args()

    copy = (args.action.lower() == "copy")
    info = (args.action.lower() == "info")

    if args.amazon:
        if not (credentials_amazon := AwsCredentials.from_file(args.amazon)):
            usage(f"Cannot create AWS credentials from specified value: {args.amazon}")
    else:
        credentials_amazon = AwsCredentials.from_environment_variables()

    if args.temporary_credentials:
        # Use temporary AWS credentials like from SMaHT Portal.
        if args.temporary_credentials is True:
            credentials_amazon = credentials_amazon.generate_temporary_credentials(kms_key_id=args.kms)
        else:
            if not cloud_path.has_separator(args.temporary_credentials):
                usage("Given temporary credentials argument must be of the form: bucket/key")
            bucket = cloud_path.bucket(args.temporary_credentials)
            key = cloud_path.key(args.temporary_credentials)
            credentials_amazon = credentials_amazon.generate_temporary_credentials(bucket=bucket, key=key,
                                                                                   kms_key_id=args.kms)

    if args.google:
        if not (credentials_google := GcpCredentials.from_file(args.google)):
            usage(f"Cannot create GCS credentials from specified value: {args.google}")
    else:
        credentials_google = None

    if info:
        exit(main_info(args, credentials_amazon, credentials_google))
    elif copy:
        if not args.destination:
            usage("Destination required for copy.")
        exit(main_copy(args, credentials_amazon, credentials_google))
    else:
        usage("Must specify copy or info.")


def main_copy(args, credentials_amazon, credentials_google):

    if args.source.lower().startswith("s3://"):
        source = args.source[5:]
        if not credentials_amazon:
            usage("No AWS credentials specified or found (in environment).")
        source_config = RCloneAmazon(credentials_amazon)
    elif args.source.lower().startswith("gs://"):
        source = args.source[5:]
        if not credentials_google:
            if not RCloneGoogle.is_google_compute_engine():
                # No Google credentials AND NOT running on a GCE instance.
                usage("No GCP credentials specified.")
            # OK to create RCloneGoogle with no credentials on a GCE instance.
            source_config = RCloneGoogle()
            if args.verbose:
                google_project = source_config.project
                print(f"Running from Google Cloud Engine (GCE){f': {google_project} ✓' if google_project else '.'}")
        else:
            source_config = RCloneGoogle(credentials_google)
    else:
        source = args.source
        source_config = None

    if args.destination.lower().startswith("s3://"):
        destination = args.destination[5:]
        if not credentials_amazon:
            usage("No AWS credentials specified or found (in environment).")
        destination_config = RCloneAmazon(credentials_amazon)
    elif args.destination.lower().startswith("gs://"):
        destination = args.destination[5:]
        if not credentials_google:
            if not RCloneGoogle.is_google_compute_engine():
                # No Google credentials AND NOT running on a GCE instance.
                usage("No GCP credentials specified.")
            # OK to create RCloneGoogle with no credentials on a GCE instance.
            destination_config = RCloneGoogle()
            if args.verbose:
                google_project = destination_config.project
                print(f"Running from Google Cloud Engine (GCE){f': {google_project} ✓' if google_project else '.'}")
        else:
            destination_config = RCloneGoogle(credentials_google)
    else:
        destination = args.destination
        destination_config = None

    rcloner = RCloner(source=source_config, destination=destination_config)
    result, output = rcloner.copy(source, destination, return_output=True)
    if result is True:
        print("OK", end="")
        if args.verbose:
            print(" ▶ rclone output below ...")
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
            args.verbose = True
        if args.verbose:
            print(f" ▶ rclone output below ...")
            for line in output:
                print(line)
        else:
            print()
        exit(1)


def main_info(args, credentials_amazon, credentials_google):
    if not args.source and not args.destination:
        return
    if args.source:
        print_info(args.source, credentials_amazon, credentials_google)
    if args.destination:
        print_info(args.destination, credentials_amazon, credentials_google)
    print("")


def print_info(target, credentials_amazon, credentials_google):
    if not target:
        return
    if target.lower().startswith("s3://"):
        if not credentials_amazon:
            usage(f"No AWS credentials specified for: {target}")
        print("")
        print(f"AWS S3 Target: {target}")
        print_info_via_rclone(target, RCloneAmazon(credentials_amazon))
    elif target.lower().startswith("gs://"):
        if not credentials_google:
            usage(f"No GCS credentials specified for: {target}")
        print("")
        print(f"GCS Target: {target}")
        print_info_via_rclone(target, RCloneGoogle(credentials_google))


def print_info_via_rclone(target, rclone_config):
    size = rclone_config.file_size(target)
    checksum = rclone_config.file_checksum(target)
    modified = rclone_config.file_modified(target, formatted=True)
    # TODO
    # Add RCloneConfig lsjson access point to get modified date,
    # and might as well change path_exists and file_size to use this same call.
    # [{"Path":"SMAFITXIG8HS.fastq","Name":"SMAFITXIG8HS.fastq",
    #   "Size":14,"MimeType":"binary/octet-stream",
    #    "ModTime":"2024-05-09T16:58:30.606505622-04:00",
    #    "IsDir":false,"Tier":"STANDARD"}]
    formatted_size = format_size(size)
    print(f"Bucket: {cloud_path.bucket(target)}")
    print(f"Key: {cloud_path.key(target)}")
    print(f"Size: {format_size(size)}{f' ({size} bytes)' if '.' in formatted_size else ''}")
    print(f"Modified: {modified}")
    print(f"Checksum: {checksum}")
    if info := rclone_config.file_info(target):
        if metadata := info.get("metadata"):
            print(f"Metadata ({len(metadata)}):")
            for key in {key: metadata[key] for key in sorted(metadata)}:
                print(f"- {key}: {metadata[key]}")


def usage(message: str) -> None:
    print(message)
    exit(1)


if __name__ == "__main__":
    main()
