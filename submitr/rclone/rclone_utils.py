from __future__ import annotations
import os
from re import compile as re_compile, escape as re_escape
from typing import Optional, Tuple
# from submitr.rclone.rclone_store_registry import RCloneStoreRegistry


class cloud_path:

    separator = "/"
    google_prefix = "gs://"
    amazon_prefix = "s3://"
    normalize_separator_regex = re_compile(rf"({re_escape(separator)})+")

    @staticmethod
    def normalize(value: str, preserve_prefix: bool = False, preserve_suffix: bool = False) -> str:
        if not (isinstance(value, str) and (value := value.strip())):
            return ""
        value, prefix = cloud_path._remove_prefix(value)
        if not (preserve_prefix is True):
            prefix = None
        value = cloud_path.normalize_separator_regex.sub(cloud_path.separator, value)
        if value.startswith(cloud_path.separator):
            value = value[1:]
        if preserve_suffix is not True:
            if value.endswith(cloud_path.separator):
                value = value[:-1]
        if prefix:
            value = prefix + value
        return value if value != "." else ""

    @staticmethod
    def join(*args, preserve_prefix: bool = False, preserve_suffix: bool = False) -> str:
        prefix = suffix = None
        if preserve_prefix is True:
            if len(args) > 0:
                _, prefix = cloud_path._remove_prefix(args[0])
            pass
        if preserve_suffix is True:
            for arg in reversed(args):
                if isinstance(arg, str):
                    if arg.strip().endswith(cloud_path.separator):
                        suffix = True
                    break
        path = ""
        for arg in args:
            if arg := cloud_path.normalize(arg):
                if path:
                    path += cloud_path.separator
                path += arg
        if prefix:
            path = prefix + path
        if suffix:
            path = path + cloud_path.separator
        return path

    @staticmethod
    def has_separator(value: str) -> bool:
        if value := cloud_path.normalize(value):
            return cloud_path.separator in value
        return False

    @staticmethod
    def to_file_path(value: str) -> str:
        if not (value := cloud_path.normalize(value)):
            return ""
        return value.replace(cloud_path.separator, os.sep)

    @staticmethod
    def basename(value: str) -> str:
        # Returns the basename of the given cloud path (like os.path.basename).
        if not (value := cloud_path.normalize(value)):
            return ""
        return os.path.basename(cloud_path.to_file_path(value))

    @staticmethod
    def bucket(value: str) -> str:
        # Returns the bucket portion of the given cloud path assuming it consists of
        # a bucket (a single name followed by a separator, i.e. a slash) followed
        # by an optional key. If no bucket is found then returns and empty string.
        if value := cloud_path.normalize(value):
            if (separator_index := value.find(cloud_path.separator)) > 0:
                value = value[:separator_index]
            return value
        return ""

    @staticmethod
    def key(value: str) -> str:
        # Returns the key portion of the given cloud path assuming it consists of
        # a bucket (a single name followed by a separator, i.e. a slash) followed
        # by an optional key. If no key is found then returns and empty string.
        if value := cloud_path.normalize(value):
            if (separator_index := value.find(cloud_path.separator)) > 0:
                return value[separator_index + 1:]
        return ""

    @staticmethod
    def bucket_and_key(bucket: str, key: Optional[str] = None,
                       preserve_suffix: bool = False) -> Tuple[Optional[str], Optional[str]]:
        if not (bucket := cloud_path.normalize(bucket, preserve_suffix=preserve_suffix)):
            return None, None
        if preserve_suffix is True:
            key = cloud_path.normalize(key, preserve_suffix=True)
            trailing_separator_bucket = isinstance(bucket, str) and bucket.endswith(cloud_path.separator)
            trailing_separator_key = key.endswith(cloud_path.separator) if key else False
            folder = trailing_separator_key or ((not key) and trailing_separator_bucket)
        else:
            folder = False
        if not (bucket_and_key := cloud_path.join(bucket, key)):
            return None, None
        if cloud_path.has_separator(bucket_and_key):
            bucket = cloud_path.bucket(bucket_and_key)
            key = cloud_path.key(bucket_and_key)
            return (bucket, key + cloud_path.separator) if folder else (bucket, key)
        else:
            return bucket_and_key, None

    @staticmethod
    def is_bucket_only(path: str) -> bool:
        return not cloud_path.has_separator(cloud_path.normalize(path))

    @staticmethod
    def is_folder(path: str) -> bool:
        return cloud_path.normalize(path, preserve_suffix=True).endswith(cloud_path.separator)

    @staticmethod
    def is_amazon(path: str) -> bool:
        return isinstance(path, str) and path.lower().startswith(cloud_path.amazon_prefix)

    @staticmethod
    def is_google(path: str) -> bool:
        return isinstance(path, str) and path.lower().startswith(cloud_path.google_prefix)

    @staticmethod
    def _remove_prefix(path: str) -> Tuple[str, Optional[str]]:
        if not (isinstance(path, str) and (path := path.strip())):
            return "", None
        if (path_lower := path.lower()).startswith(cloud_path.amazon_prefix):
            return path[len(cloud_path.amazon_prefix):], cloud_path.amazon_prefix
        elif path_lower.startswith(cloud_path.google_prefix):
            return path[len(cloud_path.google_prefix):], cloud_path.google_prefix
        else:
            return path, None
