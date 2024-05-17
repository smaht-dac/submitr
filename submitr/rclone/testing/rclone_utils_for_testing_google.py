from __future__ import annotations
import base64
from google.cloud.storage import Client as GcsClient
import os
from typing import List, Optional
from dcicutils.file_utils import are_files_equal, normalize_path
from dcicutils.tmpfile_utils import temporary_file
from submitr.rclone.rclone_google import GoogleCredentials, RCloneGoogle
from submitr.rclone.rclone_utils import cloud_path


# Module with class/functions to aid in integration testing of smaht-submitr rclone support.

class Gcs:

    def __init__(self, credentials: GoogleCredentials) -> None:
        self._credentials = credentials
        self._client = None

    @property
    def credentials(self) -> GoogleCredentials:
        return self._credentials

    @property
    def client(self) -> GcsClient:
        if not self._client:
            if not RCloneGoogle.is_google_compute_engine():
                self._client = GcsClient.from_service_account_json(self.credentials.service_account_file)
            else:
                # Credentials are implicit on a GCE.
                self._client = GcsClient()
        return self._client

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file, str) or not file:
                return False
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if not (key := cloud_path.normalize(key)):
                key = os.path.basename(file)
            self.client.get_bucket(bucket).blob(key).upload_from_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def download_file(self, bucket: str, key: str, file: str,
                      nodirectories: bool = False, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if not (key := cloud_path.normalize(key)):
                return False
            if not isinstance(file, str) or not file:
                return False
            if os.path.isdir(file):
                if cloud_path.has_separator(key):
                    if nodirectories is True:
                        key_as_file_name = key.replace(cloud_path.separator, "_")
                        file = os.path.join(file, key_as_file_name)
                    else:
                        key_as_file_path = cloud_path.to_file_path(key)
                        directory = normalize_path(os.path.join(file, os.path.dirname(key_as_file_path)))
                        os.makedirs(directory, exist_ok=True)
                        file = os.path.join(directory, os.path.basename(key_as_file_path))
                else:
                    file = os.path.join(file, key)
                """
                if cloud_path.has_separator(key):
                    if nodirectories is True:
                        file = os.path.join(file, key.replace(cloud_path.separator, "_"))
                    else:
                        directory = os.path.join(file, os.path.dirname(key.replace(cloud_path.separator, os.sep)))
                        os.makedirs(directory, exist_ok=True)
                        file = os.path.join(directory, os.path.basename(key.replace(cloud_path.separator, os.sep)))
                else:
                    file = os.path.join(file, key)
                """
            self.client.get_bucket(bucket).blob(key).download_to_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def delete_file(self, bucket: str, key: Optional[str] = None,
                    check: bool = False, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return False
        try:
            if not (check is True) or self.file_exists(bucket, key):
                self.client.get_bucket(bucket).blob(key).delete()
                return True
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def bucket_exists(self, bucket: str, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            return self.client.get_bucket(bucket).exists()
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def file_exists(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if not (key := cloud_path.normalize(key)):
                return False
            return self.client.get_bucket(bucket).blob(key).exists()
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def file_equals(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key or not isinstance(file, str) or not file:
            return False
        try:
            with temporary_file() as temporary_downloaded_file_name:
                if self.download_file(bucket, key, temporary_downloaded_file_name):
                    return are_files_equal(file, temporary_downloaded_file_name)
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def file_size(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[int]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        try:
            # Using list_blobs with the exact key as prefix because when just
            # using the blob directly the size is None; for some reason.
            # return self.client.get_bucket(bucket).blob(key).size
            for blob in self.client.get_bucket(bucket).list_blobs(prefix=key):
                return blob.size
        except Exception as e:
            if raise_exception is True:
                raise e
            return None

    def file_checksum(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[str]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        try:
            # Using list_blobs with the exact key as prefix because when just
            # using the blob directly the md5_hash is None; for some reason.
            # return self.client.get_bucket(bucket).blob(key).md5_hash
            for blob in self.client.get_bucket(bucket).list_blobs(prefix=key):
                return base64.b64decode(blob.md5_hash).hex()
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    def list_files(self, bucket: str,
                   prefix: Optional[str] = None,
                   sort: Optional[str] = None,
                   count: Optional[int] = None, offset: Optional[int] = None,
                   raise_exception: bool = True) -> List[str]:
        pass  # NOT YET NEEDED


class GcpCredentials(GoogleCredentials):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def from_file(service_account_file: str, location: Optional[str] = None) -> Optional[GoogleCredentials]:
        if not (service_account_file := normalize_path(service_account_file, expand_home=True)):
            return None
        if not os.path.isfile(service_account_file):
            return None
        return GcpCredentials(service_account_file=service_account_file, location=location)
