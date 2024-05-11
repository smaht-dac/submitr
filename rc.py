from submitr.rclone.testing.rclone_utils_for_testing_amazon import AwsCredentials, AwsS3
from submitr.rclone import AmazonCredentials, RClone, RCloneConfigAmazon, cloud_path
from dcicutils.misc_utils import create_short_uuid

bucket = "smaht-unit-testing-files"
key = f"testfolder/test-hello-{create_short_uuid(8)}.txt"
destination = f"{bucket}/{key}"
print(key)

main_credentials = AwsCredentials.get_credentials_from_file("smaht-wolf")


policy = {"Version": "2012-10-17",
          "Statement": [{"Action": [
                            "s3:PutObject",
                            "s3:GetObject",
                            "s3:CreateBucket",
                            "s3:ListBucket",
                       ],
                       #"Resource": [f"arn:aws:s3:::{destination}", f"arn:aws:s3:::{destination}/*"],
                       "Resource": [f"arn:aws:s3:::{destination}", f"arn:aws:s3:::{bucket}"], # OK (with s3:*)
                       #"Resource": [f"*"],
                       "Effect": "Allow"}]}

print(policy)

temporary_credentials = main_credentials.generate_temporary_credentials(policy=policy, name="test-hello.txt")
print(f"access_key_id = {temporary_credentials.access_key_id}")
print(f"secret_access_key = {temporary_credentials.secret_access_key}")
print(f"session_token = {temporary_credentials.session_token}")

credentials = temporary_credentials

rclone_config_amazon = RCloneConfigAmazon(credentials)
rclone = RClone(destination=rclone_config_amazon)
result = rclone.copy("/tmp/hello.txt", destination, raise_exception=True, dryrun=False)
print(result)
