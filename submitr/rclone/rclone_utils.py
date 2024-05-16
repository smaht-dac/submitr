from re import compile as re_compile, escape as re_escape
import os


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
    def basename(value: str) -> str:
        # Returns the basename of the given cloud path (just like os.path.basename).
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
