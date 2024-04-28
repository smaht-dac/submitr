from __future__ import annotations
import os
import re
from google.cloud.storage import Client as GcsClient
from typing import List, Optional
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_config_google import GoogleCredentials


# Module with class/functions to aid in integration testing of smaht-submitr rclone support.

class Gcs:

    def __init__(self, credentials: GoogleCredentials) -> None:
        self._credentials = GoogleCredentials(credentials)
        self._client = None

    @property
    def credentials(self) -> GoogleCredentials:
        return self._credentials

    @credentials.setter
    def credentials(self, value: GoogleCredentials) -> None:
        if isinstance(value, GoogleCredentials) and value != self._credentials:
            self._credentials = value

    @property
    def client(self) -> GcsClient:
        if not self._client:
            self._client = GcsClient.from_service_account_json(self.credentials.service_account_file)
        return self._client

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file, str) or not file:
                return False
            if not (bucket := RCloneConfig._normalize_cloud_path(bucket)):
                return False
            if not (key := RCloneConfig._normalize_cloud_path(key)):
                key = os.path.basename(file)
            bucket = self.client.get_bucket(bucket)
            blob = bucket.blob(key)
            blob.upload_from_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def download_file(self, bucket: str, key: str, file: str, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := RCloneConfig._normalize_cloud_path(bucket)):
                return False
            if not (key := RCloneConfig._normalize_cloud_path(key)):
                return False
            if not isinstance(file, str) or not file:
                return False
            if os.path.isdir(file):
                file = f"{file}/{key.replace(os.sep, '_')}"
            bucket = self.client.get_bucket(bucket)
            blob = bucket.blob(key)
            blob.download_to_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def delete_file(self, bucket: str, key: str, check: bool = False, raise_exception: bool = True) -> bool:
        pass

    def file_exists(self, bucket: str, key: str, raise_exception: bool = True) -> bool:
        pass

    def file_equals(self, bucket: str, key: str, file: str, raise_exception: bool = True) -> bool:
        pass

    def list_files(self, bucket: str,
                   prefix: Optional[str] = None,
                   sort: Optional[str] = None,
                   count: Optional[int] = None, offset: Optional[int] = None,
                   raise_exception: bool = True) -> List[str]:
        pass

    @staticmethod
    def _normalize_cloud_path(value: str) -> str:
        if not isinstance(value, str):
            return ""
        return re.compile(rf"({re.escape('/')})+").sub("/", value.strip())
