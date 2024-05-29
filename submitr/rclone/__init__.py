# See rcloner.py for some notes on the basic structure of the rclone support code.
from submitr.rclone.rcloner import RCloner  # noqa
from submitr.rclone.rclone_target import RCloneTarget, RCloneCredentials  # noqa
from submitr.rclone.rclone_amazon import AmazonCredentials, RCloneAmazon  # noqa
from submitr.rclone.rclone_google import GoogleCredentials, RCloneGoogle  # noqa
from submitr.rclone.rclone_utils import cloud_path  # noqa
