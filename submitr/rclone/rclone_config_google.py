from __future__ import annotations
from typing import Optional
from dcicutils.misc_utils import create_dict
from submitr.rclone.rclone_config import RCloneConfig


class RCloneConfigGoogle(RCloneConfig):

    def __init__(self,
                 credentials: Optional[GoogleCredentials] = None,
                 location: Optional[str] = None,
                 service_account_file: Optional[str] = None,
                 name: Optional[str] = None, bucket: Optional[str] = None) -> None:
        super().__init__(name=name, bucket=bucket)
        self._credentials = GoogleCredentials(credentials=credentials,
                                              location=location,
                                              service_account_file=service_account_file)

    @property
    def credentials(self) -> Optional[GoogleCredentials]:
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

    @property
    def config(self) -> dict:
        return create_dict(type="google cloud storage",
                           location=self.location,
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

        if location := RCloneConfig._normalize_string_value(location):
            self._location = location
        if service_account_file := RCloneConfig._normalize_string_value(service_account_file):
            self._service_account_file = service_account_file

    @property
    def location(self) -> Optional[str]:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._location = value or None

    @property
    def service_account_file(self) -> Optional[str]:
        return self._service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> None:
        if (value := RCloneConfig._normalize_string_value(value)) is not None:
            self._service_account_file = value or None
