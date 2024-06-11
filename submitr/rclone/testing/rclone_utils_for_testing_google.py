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
            if not (isinstance(file, str) and file):
                return False
            bucket, key = cloud_path.bucket_and_key(bucket, key, preserve_suffix=True)
            if not bucket:
                return False
            if not key:
                key = os.path.basename(file)
            elif key.endswith(cloud_path.separator):
                key = cloud_path.join(key, os.path.basename(file))
            self.client.get_bucket(bucket).blob(key).upload_from_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def download_file(self, file: str, bucket: str, key: str, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file := normalize_path(file), str) or not file:
                return False
            bucket, key = cloud_path.bucket_and_key(bucket, key)
            if not (bucket and key):
                return False
            if os.path.isdir(file):
                if cloud_path.separator in key:
                    key_basename = cloud_path.basename(key)
                    file = os.path.join(file, key_basename)
                else:
                    file = os.path.join(file, key)
            self.client.get_bucket(bucket).blob(key).download_to_filename(file)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def create_folder(self, bucket: str, folder: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if folder := cloud_path.normalize(folder):
                bucket = cloud_path.join(bucket, folder)
            bucket, folder = cloud_path.bucket_and_key(bucket)
            if not folder:
                return False
            if not folder.endswith(cloud_path.separator):
                folder += cloud_path.separator
            self.client.get_bucket(bucket).blob(folder).upload_from_string("")
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def delete_file(self, bucket: str, key: Optional[str] = None,
                    check: bool = False, safe: bool = True, raise_exception: bool = True) -> bool:
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

    def delete_folders(self, bucket: str, folder: Optional[str] = None, raise_exception: bool = True) -> bool:
        """
        This delete ONLY folders, within the given folder (within the given bucket) not actual keys
        and this is used ONLY for (integration) testing (see test_rclone_support.py), as is this entire
        module, and is only used to CLEANUP after ourselves after each test. We delete ONLY folders for
        safety, as we don't want this to be accidently (due to some errant testing bug) deleting real data.
        Deleting a folder which contains a key does NOT cause the key to be deleted. And so it is up to
        the caller (the integration tests) to explicitly delete any actual files/keys in the folder
        first, and then call this to cleanup the folder and any sub-folders.
        """
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if folder := cloud_path.normalize(folder):
                bucket = cloud_path.join(bucket, folder)
            bucket, folder = cloud_path.bucket_and_key(bucket)
            if not folder:
                return False
            if not folder.endswith(cloud_path.separator):
                folder += cloud_path.separator
            for blob in self.client.get_bucket(bucket).list_blobs(prefix=folder):
                if not blob.name.endswith(cloud_path.separator):
                    continue
                blob.delete()
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
                if self.download_file(temporary_downloaded_file_name, bucket, key):
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
