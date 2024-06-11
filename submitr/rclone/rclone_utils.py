from __future__ import annotations
import os
from re import compile as re_compile, escape as re_escape
from typing import Optional, Tuple
from submitr.rclone.rclone_store_registry import RCloneStoreRegistry


class cloud_path:

    separator = "/"
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
    def basename(value: str) -> str:
        # Returns the basename of the given cloud path (like os.path.basename).
        if not (value := cloud_path.normalize(value)):
            return ""
        return os.path.basename(value.replace(cloud_path.separator, os.sep))

    @staticmethod
    def bucket(value: str) -> str:
        # Returns the bucket portion of the given cloud path assuming it consists of
        # a bucket (a single name followed by a separator, i.e. a slash) followed
        # by an optional key. If no bucket is found then returns an empty string.
        if value := cloud_path.normalize(value):
            if (separator_index := value.find(cloud_path.separator)) > 0:
                value = value[:separator_index]
            return value
        return ""

    @staticmethod
    def key(value: str) -> str:
        # Returns the key portion of the given cloud path assuming it consists of
        # a bucket (a single name followed by a separator, i.e. a slash) followed
        # by an optional key. If no key is found then returns an empty string.
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
            is_folder = trailing_separator_key or ((not key) and trailing_separator_bucket)
        else:
            is_folder = False
        if not (bucket_and_key := cloud_path.join(bucket, key)):
            return None, None
        if cloud_path.separator in bucket_and_key:
            bucket = cloud_path.bucket(bucket_and_key)
            key = cloud_path.key(bucket_and_key)
            return (bucket, key + cloud_path.separator) if is_folder else (bucket, key)
        else:
            return bucket_and_key, None

    @staticmethod
    def is_bucket_only(path: str) -> bool:
        return cloud_path.separator not in cloud_path.normalize(path)

    @staticmethod
    def is_folder(path: str) -> bool:
        return cloud_path.normalize(path, preserve_suffix=True).endswith(cloud_path.separator)

    @staticmethod
    def _remove_prefix(path: str) -> Tuple[str, Optional[str]]:
        if cloud_store := RCloneStoreRegistry.lookup(path):
            return path[len(cloud_store.prefix):], cloud_store.prefix
        return path, None
