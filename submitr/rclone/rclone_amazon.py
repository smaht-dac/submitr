from __future__ import annotations
import os
from typing import Callable, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string, PRINT
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_target import RCloneTarget
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import chars


class RCloneAmazon(RCloneTarget):

    def __init__(self,
                 credentials_or_config: Optional[Union[AmazonCredentials, RCloneAmazon, str]] = None,
                 region: Optional[str] = None,
                 access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None,
                 kms_key_id: Optional[str] = None,
                 name: Optional[str] = None,
                 bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneAmazon):
            name = normalize_string(name) or credentials_or_config.name
            bucket = cloud_path.normalize(bucket) or credentials_or_config.bucket
            credentials = credentials_or_config.credentials
        elif isinstance(credentials_or_config, AmazonCredentials):
            credentials = credentials_or_config
        elif (isinstance(credentials_or_config, str) and
              (credentials_file := normalize_path(credentials_or_config, expand_home=True))):
            credentials = credentials_file
        else:
            credentials = None
        credentials = AmazonCredentials(credentials=credentials,
                                        region=region,
                                        access_key_id=access_key_id,
                                        secret_access_key=secret_access_key,
                                        session_token=session_token,
                                        kms_key_id=kms_key_id)
        super().__init__(name=name, bucket=bucket, credentials=credentials)

    @property
    def credentials(self) -> AmazonCredentials:
        return super().credentials

    @property
    def config(self) -> dict:
        return create_dict(provider="AWS",
                           type="s3",
                           region=self.region,
                           access_key_id=self.access_key_id,
                           secret_access_key=self.secret_access_key,
                           session_token=self.session_token,
                           sse_kms_key_id=self.kms_key_id,
                           server_side_encryption="aws:kms" if self.kms_key_id else None)

    @property
    def region(self) -> Optional[str]:
        return self._credentials.region

    @property
    def access_key_id(self) -> Optional[str]:
        return self._credentials.access_key_id

    @property
    def secret_access_key(self) -> Optional[str]:
        return self._credentials.secret_access_key

    @property
    def session_token(self) -> Optional[str]:
        return self._credentials.session_token

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._credentials.kms_key_id

    def __eq__(self, other: Optional[RCloneAmazon]) -> bool:
        return isinstance(other, RCloneAmazon) and super().__eq__(other)

    def __ne__(self, other: Optional[RCloneAmazon]) -> bool:
        return not self.__eq__(other)

    def verify_connectivity(self, printf: Optional[Callable] = None) -> bool:
        if not callable(printf):
            printf = print
        if self.ping():
            printf(f"Amazon Cloud Storage project"
                   f" connectivity appears to be OK {chars.check}")
                   # f"{f' ({self.project})' if self.project else ''}" # TODO  # noqa
            if self.bucket_exists() is False:
                printf(f"WARNING: AWS S3 bucket/path NOT FOUND or EMPTY: {self.bucket}")
            return False
        else:
            printf(f"AWS S3 project"
            #      f"{f' ({self.project})' if self.project else ''}" # TODO  # noqa
                   f" connectivity appears to be problematic {chars.xmark}")
            return True

    @staticmethod
    def from_command_args(rclone_cloud_source: Optional[str],
                          rclone_cloud_credentials: Optional[str] = None,
                          rclone_cloud_location: Optional[str] = None,
                          verify_installation: bool = True,
                          printf: Optional[Callable] = None) -> Optional[RCloneAmazon]:
        """
        Assumed to be called at the start of command-line utility (i.e. e.g. submit-metadata-bundle).
        The rclone_cloud_source should be the Amazon bucket (or bucket/sub-folder is also allowed),
        where the files to be copied can be found. The rclone_cloud_credentials should be the full path to
        the Amazon (AWS S3) credentiasl file. The rclone_cloud_location is the region to be used for the copy.
        """
        if not isinstance(rclone_cloud_source, str) or not rclone_cloud_source:
            return None
        if not callable(printf):
            printf = PRINT
        if not RCloneInstallation.verify_installation():
            printf(f"ERROR: Cannot install rclone for some reason (contact support).")
            exit(1)
        if not isinstance(rclone_cloud_credentials, str):
            if not (rclone_cloud_credentials := normalize_path(os.environ.get("AWS_SHARED_CREDENTIALS_FILE"),
                                                               expand_home=True)):
                rclone_cloud_credentials = None
        if rclone_cloud_credentials and not os.path.isfile(rclone_cloud_credentials):
            printf(f"ERROR: Amazon service account file does not exist: {rclone_cloud_credentials}")
            exit(1)
        return RCloneAmazon(rclone_cloud_credentials,
                            region=rclone_cloud_location,
                            bucket=rclone_cloud_source)
