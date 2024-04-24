from typing import Optional
import boto3
import os
import random
import string
from botocore.client import BaseClient as BotoClient
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file


def create_s3_client(aws_region: str,
                     aws_access_key_id: str,
                     aws_secret_access_key: str,
                     aws_session_token: Optional[str] = None,
                     aws_kms_key_id: Optional[str] = None) -> BotoClient:
    s3_session = boto3.Session(
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token)
    return s3_session.client("s3")


def aws_file_exists(s3: BotoClient, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
            return False
        raise e


def aws_download_file(s3: BotoClient, bucket: str, key: str, file: str) -> bool:
    try:
        s3.download_file(bucket, key, file)
        return True
    except Exception as e:
        if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
            return False
        raise e


def aws_upload_file(s3: BotoClient, file: str, bucket: str, key: Optional[str] = None) -> bool:
    try:
        if not key:
            key = os.path.basename(file)
        s3.upload_file(file, bucket, key)
        return True
    except Exception as e:
        raise e


def aws_delete_file(s3: BotoClient, bucket: str, key: str) -> bool:
    # TODO
    pass


def aws_file_equals(s3: BotoClient, bucket: str, key: str, file: str) -> bool:
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
        with open(filea, "r") as fa:
            with open(fileb, "r") as fb:
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
