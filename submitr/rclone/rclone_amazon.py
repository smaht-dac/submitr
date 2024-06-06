from __future__ import annotations
import os
from typing import Callable, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string, PRINT
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.rclone_store import RCloneStore
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import chars


@RCloneStore.register
class RCloneAmazon(RCloneStore):

    prefix = "s3://"
    proper_name = "AWS S3"
    proper_name_title = "Amazon S3"
    proper_name_label = "s3-cloud-store"

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

    def copy(self) -> RCloneAmazon:
        return RCloneAmazon(name=self.name,
                            credentials=self.credentials.copy() if self.credentials else None,
                            bucket=self.bucket)

    def __eq__(self, other: Optional[RCloneAmazon]) -> bool:
        return isinstance(other, RCloneAmazon) and super().__eq__(other)

    def __ne__(self, other: Optional[RCloneAmazon]) -> bool:
        return not self.__eq__(other)

    def verify_connectivity(self, quiet: bool = False,
                            usage: Optional[Callable] = None, printf: Optional[Callable] = None) -> None:
        if not callable(usage):
            usage = print
        if not callable(printf):
            printf = print
        if self.ping():
            if quiet is not True:
                printf(f"{self.proper_name_title} connectivity appears to be OK {chars.check}")
            if self.bucket_exists() is False:
                printf(f"WARNING: AWS S3 bucket/path NOT FOUND or EMPTY: {self.bucket}")
        else:
            usage(f"{self.proper_name_title} connectivity appears to be problematic {chars.xmark}")

    @classmethod
    def from_args(cls,
                  cloud_source: str,
                  cloud_credentials: Optional[str],
                  cloud_location: Optional[str],
                  verify_connectivity: bool = True,
                  usage: Optional[Callable] = None,
                  printf: Optional[Callable] = None) -> Optional[RCloneAmazon]:
        """
        Assumed to be called at the start of command-line utility (i.e. e.g. submit-metadata-bundle).
        The cloud_source should be the Amazon bucket (or bucket/sub-folder is also allowed),
        where the files to be copied can be found. The cloud_credentials should be the full path to
        the Amazon (AWS S3) credentials file. The cloud_location is the region to be used for the copy.
        """
        if not (isinstance(cloud_source, str) and cloud_source):  # should never happen
            return None
        if not callable(usage):
            usage = PRINT
        if not callable(printf):
            printf = PRINT
        if not (cloud_credentials := normalize_path(cloud_credentials, expand_home=True)):
            if not (cloud_credentials := normalize_path(os.environ.get("AWS_SHARED_CREDENTIALS_FILE"),
                                                        expand_home=True)):
                usage(f"ERROR: No Amazon credentials file specified.")
                return None
        if not os.path.isfile(cloud_credentials):
            usage(f"ERROR: Amazon credentials file does not exist: {cloud_credentials}")
            return None
        cloud_store = RCloneAmazon(cloud_credentials, region=cloud_location, bucket=cloud_source)
        if verify_connectivity is True:
            cloud_store.verify_connectivity(quiet=True, usage=usage, printf=printf)
        return cloud_store
