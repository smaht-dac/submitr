from typing import Optional
from dcicutils.misc_utils import create_dict
from submitr.rclone.rclone_config import RCloneConfig


class RCloneConfigGoogle(RCloneConfig):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._location = None
        self._service_account_file = None
        self._bucket = None

    @property
    def location(self) -> Optional[str]:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._location = value or None

    @property
    def service_account_file(self) -> Optional[str]:
        return self._service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> RCloneConfig:
        if (value := self._normalize_string_value(value)) is not None:
            self._service_account_file = value or None

    @property
    def bucket(self) -> Optional[str]:
        return self._bucket

    @bucket.setter
    def bucket(self, value: str) -> None:
        if (value := self._normalize_string_value(value)) is not None:
            self._bucket = value or None

    @property
    def config(self) -> dict:
        return create_dict(type="google cloud storage",
                           location=self.location,
                           service_account_file=self.service_account_file)
