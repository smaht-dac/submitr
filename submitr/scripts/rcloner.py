import argparse
from submitr.rclone import RClone, RCloneConfigAmazon, RCloneConfigGoogle, cloud_path
from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials
from submitr.rclone.testing.rclone_utils_for_testing_google import GcpCredentials

credentials = AwsCredentials.from_file("smaht-wolf")
config = RCloneConfigAmazon(credentials)
bucket = "smaht-unit-testing-files"
key = "002204d0-0c52-4b56-9924-7392c439f609/SMAFIPIGC8NG.fastq"
rclone = RClone(source=config)
rclone.copy(cloud_path.join(bucket, key), ".")


def main():
    args = argparse.ArgumentParser(description="Test utility for rclone support in smaht-submitr.")
    args.add_argument("source", help="Source file or cloud bucket/key.")
    args.add_argument("destination", help="Destination file/directory or cloud bucket/key.")
    args.add_argument("--amazon", help="AWS environment; for ~/.aws_test.{env}/credentials file.")
    args.add_argument("--google", help="Amazon or Google configuration file.")
    args = args.parse_args()

    rclone_config_amazon = None
    rclone_config_google = None

    if args.amazon:
        credentials_amazon = AwsCredentials.from_file(args.amazon)
        rclone_config_amazon = RCloneConfigAmazon(credentials_amazon)

    if args.google:
        credentials_google = GcpCredentials.from_file(args.google)
        rclone_config_google = RCloneConfigGoogle(credentials_google)

    if args.source.lower().startswith("s3://"):
        source_config = rclone_config_amazon
        source = args.source[5:]
    elif args.source.lower().startswith("gs://"):
        source_config = rclone_config_google
        source = args.source[5:]
    else:
        source_config = None
        source = args.source

    if args.destination.lower().startswith("s3://"):
        destination_config = rclone_config_amazon
        destination = args.destination[5:]
    elif args.destination.lower().startswith("gs://"):
        destination_config = rclone_config_google
        destination = args.destination[5:]
    else:
        destination_config = None
        destination = args.destination

    rclone = RClone(source=source_config, destination=destination_config)
    result = rclone.copy(source, destination)
    print(result)


if __name__ == "__main__":
    main()
