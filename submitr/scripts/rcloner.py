import argparse
from submitr.rclone import RClone, RCloneConfigAmazon, RCloneConfigGoogle, cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials, AwsS3
from submitr.rclone.testing.rclone_utils_for_testing_google import GcpCredentials


def main():
    args = argparse.ArgumentParser(description="Test utility for rclone support in smaht-submitr.")
    args.add_argument("source", help="Source file or cloud bucket/key.")
    args.add_argument("destination", help="Destination file/directory or cloud bucket/key.")
    args.add_argument("--amazon", help="AWS environment; for ~/.aws_test.{env}/credentials file.")
    args.add_argument("--google", help="Amazon or Google configuration file.")
    args.add_argument("--kms", help="Amazon KMS key ID.")
    args.add_argument("--temporary-credentials", "-tc", nargs="?", help="Amazon KMS key ID.", const=True)
    args = args.parse_args()

    if args.amazon:
        credentials_amazon = AwsCredentials.from_file(args.amazon)
    else:
        credentials_amazon = AwsCredentials.from_environment_variables()

    if args.temporary_credentials:
        s3 = AwsS3(credentials_amazon)
        if args.temporary_credentials is True:
            credentials_amazon = s3.generate_temporary_credentials(kms_key_id=args.kms)
        else:
            if not cloud_path.has_separator(args.temporary_credentials):
                print("Given temporary credentials argument must be of the form: bucket/key")
            bucket = cloud_path.bucket(args.temporary_credentials)
            key = cloud_path.key(args.temporary_credentials)
            credentials_amazon = s3.generate_temporary_credentials(bucket=bucket, key=key, kms_key_id=args.kms)

    if args.google:
        credentials_google = GcpCredentials.from_file(args.google)

    if args.source.lower().startswith("s3://"):
        source = args.source[5:]
        if not credentials_amazon:
            usage("No AWS credentials specified or found (in environment).")
        source_config = RCloneConfigAmazon(credentials_amazon)
    elif args.source.lower().startswith("gs://"):
        source = args.source[5:]
        if not credentials_google:
            usage("No GCP credentials specified.")
        source_config = RCloneConfigGoogle(credentials_google)
    else:
        source = args.source
        source_config = None

    if args.destination.lower().startswith("s3://"):
        destination = args.destination[5:]
        if not credentials_amazon:
            usage("No AWS credentials specified or found (in environment).")
        destination_config = RCloneConfigAmazon(credentials_amazon)
    elif args.destination.lower().startswith("gs://"):
        destination = args.destination[5:]
        if not credentials_google:
            usage("No GCP credentials specified.")
        destination_config = RCloneConfigGoogle(credentials_google)
    else:
        destination = args.destination
        destination_config = None

    rclone = RClone(source=source_config, destination=destination_config)
    result, output = rclone.copy(source, destination, return_output=True)
    if result is True:
        print("OK")
    else:
        print("ERROR")
        print(output)


def usage(message: str) -> None:
    print(message)
    exit(1)


if __name__ == "__main__":
    main()
