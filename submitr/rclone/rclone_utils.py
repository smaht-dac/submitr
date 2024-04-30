from re import compile as re_compile, escape as re_escape
import os
from typing import Optional


class cloud_path:

    separator = "/"

    @staticmethod
    def normalize(value: str) -> str:
        if not isinstance(value, str):
            return ""
        regex = re_compile(rf"({re_escape(cloud_path.separator)})+")
        value = regex.sub(cloud_path.separator, value.strip())
        if value.startswith(cloud_path.separator):
            value = value[1:]
        if value.endswith(cloud_path.separator):
            value = value[:-1]
        return value if value != "." else ""

    @staticmethod
    def join(*args) -> str:
        path = ""
        for arg in args:
            if isinstance(arg, list):
                if arg := cloud_path.join(*arg):
                    if path:
                        path += cloud_path.separator
                    path += arg
            elif arg := cloud_path.normalize(arg):
                if path:
                    path += cloud_path.separator
                path += arg
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
    def key(value: str) -> str:
        # If the value looks like a cloud path which has an initial component (i.e.
        # before the first slash), then assume that this first componentn is a bucket name,
        # and return the part of the value (i.e the key) after this first (bucket) component.
        # If the value does not have multiple component (i.e. no slash) then return just the value.
        if value := cloud_path.normalize(value):
            if (separator_index := value.find(cloud_path.separator)) > 0:
                value = value[separator_index + 1:]
        return value


def normalize_path(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return os.path.normpath(value := value.strip())


def normalize_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return ""
    elif isinstance(value, str):
        return value.strip()
    return None
