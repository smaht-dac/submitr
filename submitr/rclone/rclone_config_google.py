from __future__ import annotations
from typing import Optional, Union
from dcicutils.misc_utils import create_dict
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_utils import normalize_string


class RCloneConfigGoogle(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[GoogleCredentials, RCloneConfigGoogle]] = None,
                 location: Optional[str] = None,
                 service_account_file: Optional[str] = None,
                 name: Optional[str] = None, bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneConfigGoogle):
            name = normalize_string(name) or credentials_or_config.name
            bucket = normalize_string(bucket) or credentials_or_config.bucket
            credentials = None
        elif isinstance(credentials_or_config, GoogleCredentials):
            credentials = credentials_or_config
        else:
            credentials = None

        super().__init__(name=name, bucket=bucket)
        self._credentials = GoogleCredentials(credentials=credentials,
                                              location=location,
                                              service_account_file=service_account_file)

    @property
    def credentials(self) -> GoogleCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: GoogleCredentials) -> None:
        if isinstance(value, GoogleCredentials):
            self._credentials = value

    @property
    def location(self) -> Optional[str]:
        return self._credentials.location

    @location.setter
    def location(self, value: str) -> None:
        self._credentials.location = value

    @property
    def service_account_file(self) -> Optional[str]:
        return self._credentials.service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> None:
        self._credentials.service_account_file = value

    def __eq__(self, other: RCloneConfigGoogle) -> bool:
        return ((self.name == other.name) and
                (self.bucket == other.bucket) and
                (self.credentials == other.credentials))

    def __ne__(self, other: RCloneConfigGoogle) -> bool:
        return self.__eq__(other)

    @property
    def config(self) -> dict:
        # The bucket_policy_only=true option indicates that rclone should enforce a bucket-only access policy,
        # meaning that object-level ACLs are not used to control access to objects within the bucket.
        return create_dict(type="google cloud storage",
                           location=self.location,
                           bucket_policy_only=True,
                           service_account_file=self.service_account_file)


class GoogleCredentials:

    @staticmethod
    def create(*args, **kwargs) -> GoogleCredentials:
        return GoogleCredentials(*args, **kwargs)

    def __init__(self,
                 credentials: Optional[GoogleCredentials] = None,
                 location: Optional[str] = None,
                 service_account_file: Optional[str] = None) -> None:

        if isinstance(credentials, GoogleCredentials):
            self._location = credentials.location
            self._service_account_file = credentials.service_account_file
        else:
            self._location = None
            self._service_account_file = None

        if location := normalize_string(location):
            self._location = location
        if service_account_file := normalize_string(service_account_file):
            self._service_account_file = service_account_file

    @property
    def location(self) -> Optional[str]:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if (value := normalize_string(value)) is not None:
            self._location = value or None

    @property
    def service_account_file(self) -> Optional[str]:
        return self._service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> None:
        if (value := normalize_string(value)) is not None:
            self._service_account_file = value or None

    def __eq__(self, other: GoogleCredentials) -> bool:
        return ((self.location == other.location) and
                (self.service_account_file == other.service_account_file))

    def __ne__(self, other: GoogleCredentials) -> bool:
        return self.__eq__(other)
