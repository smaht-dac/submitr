from base64 import b64decode as base64_decode
from boto3 import client as BotoClient
from typing import Optional
from submitr.utils import format_datetime


def get_s3_key_metadata(aws_credentials: dict, s3_bucket: str, s3_key: str) -> Optional[dict]:
    if not (isinstance(aws_credentials, dict) and
            isinstance(aws_credentials.get("aws_access_key_id"), str) and
            isinstance(aws_credentials.get("aws_secret_access_key"), str) and
            isinstance(s3_bucket, str) and s3_bucket and
            isinstance(s3_key, str) and s3_key):
        return None
    try:
        # Note that we do not need to use any KMS key for head_object.
        s3 = BotoClient("s3", **aws_credentials)
        if not isinstance(s3_file_head := s3.head_object(Bucket=s3_bucket, Key=s3_key), dict):
            return None
        result = {
            "modified": format_datetime(s3_file_head.get("LastModified")),
            "size": s3_file_head.get("ContentLength")
        }
        # Try getting the md5 that we ourselves wrote if/when uploading via this module.
        if isinstance(s3_file_metadata := s3_file_head.get("Metadata"), dict):
            if isinstance(s3_file_md5 := s3_file_metadata.get("md5"), str):
                result["md5"] = s3_file_md5
                if isinstance(s3_file_md5_timestamp := s3_file_metadata.get("md5-timestamp"), str):
                    result["md5_timestamp"] = s3_file_md5_timestamp
                if isinstance(s3_file_md5_source := s3_file_metadata.get("md5-source"), str):
                    result["md5_source"] = s3_file_md5_source
        # As a backup check if there is an md5 written directly by rclone copy.
        if not result.get("md5") and isinstance(s3_file_metadata, dict):
            if s3_file_md5 := s3_file_metadata.get("md5chksum"):
                result["md5"] = base64_decode(s3_file_md5).hex()
                if isinstance(s3_file_md5_timestamp := s3_file_metadata.get("mtime"), str):
                    result["md5_timestamp"] = s3_file_md5_timestamp
        if not result.get("md5") and isinstance(s3_file_metadata := s3_file_head.get("ResponseMetadata"), dict):
            if isinstance(s3_file_http_headers := s3_file_metadata.get("HTTPHeaders"), dict):
                if isinstance(s3_file_md5 := s3_file_http_headers.get("x-amz-meta-md5chksum"), str):
                    result["md5"] = base64_decode(s3_file_md5).hex()
                    if isinstance(s3_file_md5_timestamp := s3_file_http_headers.get("x-amz-meta-mtime"), str):
                        result["md5_timestamp"] = s3_file_md5_timestamp
        # Just for completeness and FYI get get the etag (not actually needed/used right now).
        if isinstance(s3_file_etag := s3_file_head.get("ETag", ""), str):
            result["etag"] = s3_file_etag.strip("\"")
        return result
    except Exception:
        # Ignore error for now because (1) verification usage not absolutely necessary,
        # and (2) portal permission change for this not yet deployed everywhere.
        return None
