from re import compile as re_compile, escape as re_escape
from os.path import sep as os_path_separator


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
        return value.replace(cloud_path.separator, os_path_separator)
