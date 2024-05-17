import argparse
from submitr.rclone import RCloner, RCloneAmazon, RCloneGoogle, cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials
from submitr.rclone.testing.rclone_utils_for_testing_google import GcpCredentials

# Little command-line utility to interactively test out rclone support code in smaht-submitr.


def main() -> None:
    args = argparse.ArgumentParser(description="Test utility for rclone support in smaht-submitr.")
    args.add_argument("source", help="Source file or cloud bucket/key.")
    args.add_argument("destination", help="Destination file/directory or cloud bucket/key.")
    args.add_argument("--amazon", help="AWS environment; for ~/.aws_test.{env}/credentials file.")
    args.add_argument("--google", help="Amazon or Google configuration file.")
    args.add_argument("--kms", help="Amazon KMS key ID.")
    args.add_argument("--temporary-credentials", "-tc", nargs="?", help="Amazon KMS key ID.", const=True)
    args.add_argument("--verbose", action="store_true", help="Verbose output.", default=False)
    args = args.parse_args()

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


def usage(message: str) -> None:
    print(message)
    exit(1)


if __name__ == "__main__":
    main()
