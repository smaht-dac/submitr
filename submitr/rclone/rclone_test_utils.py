from __future__ import annotations
from typing import Optional
import boto3
import os
import random
import string
from botocore.client import BaseClient as BotoClient
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file


class S3:

    @staticmethod
    def create(aws_region: str,
               aws_access_key_id: str,
               aws_secret_access_key: str,
               aws_session_token: Optional[str] = None,
               aws_kms_key_id: Optional[str] = None) -> S3:
        return S3(
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            aws_kms_key_id=aws_kms_key_id)

    def __init__(self,
                 aws_region: str,
                 aws_access_key_id: str,
                 aws_secret_access_key: str,
                 aws_session_token: Optional[str] = None,
                 aws_kms_key_id: Optional[str] = None) -> None:
        self._client = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token)
        self._kms_key_id = aws_kms_key_id

    @property
    def client(self) -> BotoClient:
        return self._client

    @property
    def kms_key_id(self) -> Optional[str]:
        return self._kms_key_id

    @property
    def extra_args(self) -> Optional[dict]:
        if self.kms_key_id:
            return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": self.kms_key_id}
        return None


def aws_upload_file(s3: S3, file: str, bucket: str, key: Optional[str] = None) -> bool:
    try:
        if not key:
            key = os.path.basename(file)
            s3.client.upload_file(file, bucket, key, ExtraArgs=s3.extra_args)
        return True
    except Exception as e:
        raise e


def aws_download_file(s3: S3, bucket: str, key: str, file: str) -> bool:
    try:
        s3.client.download_file(bucket, key, file)
        return True
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
            return False
        raise e


def aws_delete_file(s3: S3, bucket: str, key: str) -> bool:
    try:
        s3.client.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def aws_file_exists(s3: S3, bucket: str, key: str) -> bool:
    try:
        s3.client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
            return False
        raise e


def aws_file_equals(s3: S3, bucket: str, key: str, file: str) -> bool:
    try:
        with temporary_file() as temporary_downloaded_file_name:
            if aws_download_file(s3, bucket, key, temporary_downloaded_file_name):
                return are_files_equal(file, temporary_downloaded_file_name)
        return True
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
            return False
        raise e


def are_files_equal(filea: str, fileb: str) -> bool:
    try:
        with open(filea, "rb") as fa:
            with open(fileb, "rb") as fb:
                chunk_size = 4096
                while True:
                    chunka = fa.read(chunk_size)
                    chunkb = fb.read(chunk_size)
                    if chunka != chunkb:
                        return False
                    if not chunka:
                        break
        return True
    except Exception:
        return False


def create_random_file(file: Optional[str] = None,
                       prefix: Optional[str] = None, suffix: Optional[str] = None,
                       nbytes: int = 1024, binary: bool = False) -> str:
    if not file:
        file = create_temporary_file_name(prefix=prefix, suffix=suffix)
    with open(file, "wb" if binary is True else "w") as f:
        if binary is True:
            f.write(os.urandom(nbytes))
        else:
            f.write(''.join(random.choices(string.ascii_letters + string.digits, k=nbytes)))
    return file
