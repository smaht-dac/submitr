from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
import io
from json import dumps as json_dumps, loads as json_loads
import os
from pathlib import Path
import pkg_resources
import requests
from signal import signal, SIGINT
import string
from typing import Any, Callable, List, Optional, Tuple
from dcicutils.datetime_utils import format_datetime, parse_datetime
from dcicutils.function_cache_decorator import function_cache
from dcicutils.misc_utils import PRINT, str_to_bool
from dcicutils.structured_data import Portal


ERASE_LINE = "\033[K"
TIMESTAMP_PATTERN = "%H:%M:%S"
TIMESTAMP_REGEXP = "[0-2][0-9]:[0-5][0-9]:[0-5][0-9]"


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time: bool = False, same_line: bool = False):
    """
    Prints its args space-separated, as 'print' would, possibly with an hh:mm:ss timestamp prepended.

    :param args: an object to be printed
    :param with_time: a boolean specifying whether to prepend a timestamp
    :param same_line: a boolean saying whether to do this output in a way that erases the current line
        and returns to the start of the line without advancing vertically so that subsequent same_line=True
        requests will erase (and so replace) the current line.
    """
    output = io.StringIO()
    if with_time:
        hh_mm_ss = str(datetime.now().strftime(TIMESTAMP_PATTERN))
        print(hh_mm_ss, *args, end="", file=output)
    else:
        print(*args, end="", file=output)
    output = output.getvalue()
    if same_line:
        PRINT(f"{ERASE_LINE}{output}\r", end="", flush=True)
    else:
        PRINT(output)


def keyword_as_title(keyword):
    """
    Given a dictionary key or other token-like keyword, return a prettier form of it use as a display title.

    Example:
        keyword_as_title('foo') => 'Foo'
        keyword_as_title('some_text') => 'Some Text'

    :param keyword:
    :return: a string which is the keyword in title case with underscores replaced by spaces.
    """

    return keyword.replace("_", " ").title()


class FakeResponse:

    def __init__(self, status_code, json=None, content=None):
        self.status_code = status_code
        if json is not None and content is not None:
            raise Exception("FakeResponse cannot have both content and json.")
        elif content is not None:
            self.content = content
        elif json is None:
            self.content = ""
        else:
            self.content = json_dumps(json)

    def __str__(self):
        if self.content:
            return "<FakeResponse %s %s>" % (self.status_code, self.content)
        else:
            return "<FakeResponse %s>" % (self.status_code,)

    def json(self):
        return json_loads(self.content)

    def raise_for_status(self):
        if self.status_code >= 300:
            raise Exception(f"{self} raised for status.")


def tobool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        try:
            return str_to_bool(value)
        except Exception:
            return fallback
    else:
        return fallback


def format_path(path: str) -> str:
    if isinstance(path, str) and os.path.isabs(path) and path.startswith(os.path.expanduser("~")):
        path = "~/" + Path(path).relative_to(Path.home()).as_posix()
    return path


def print_boxed(lines: List[str], right_justified_macro: Optional[Tuple[str, Callable]] = None,
                printf: Optional[Callable] = PRINT) -> None:
    macro_name = None
    macro_value = None
    if right_justified_macro and (len(right_justified_macro) == 2):
        macro_name = right_justified_macro[0]
        macro_value = right_justified_macro[1]()
        lines_tmp = []
        for line in lines:
            if line is None:
                continue
            elif not isinstance(line, str):
                line = str(line)
            if line.endswith(macro_name):
                line = line.replace(macro_name, right_justified_macro[1]() + " ")
            lines_tmp.append(line)
        length = max(len(line) for line in lines_tmp)
    else:
        length = max(len(line) for line in lines if line)
    for line in lines:
        if line is None:
            continue
        elif not isinstance(line, str):
            line = str(line)
        if line == "===":
            printf(f"+{'-' * (length - len(line) + 5)}+")
        elif macro_name and line.endswith(macro_name):
            line = line.replace(macro_name, "")
            printf(f"| {line}{' ' * (length - len(line) - len(macro_value) - 1)} {macro_value} |")
        else:
            printf(f"| {line}{' ' * (length - len(line))} |")


def is_excel_file_name(file_name: str) -> bool:
    return file_name.endswith(".xlsx") or file_name.endswith(".xls")


@lru_cache(maxsize=1)
def get_version(package_name: str = "smaht-submitr") -> str:
    try:
        return pkg_resources.get_distribution(package_name).version
    except Exception:
        return ""


@lru_cache(maxsize=2)
def get_most_recent_version_info(package_name: str = "smaht-submitr", beta: bool = True) -> object:
    pypi_url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        if (response := requests.get(pypi_url)).status_code == 200 and (response := response.json()):
            latest_non_beta_version = response["info"]["version"]
            this_version = get_version(package_name=package_name)
            this_release_date = None
            releases = response["releases"]
            if releases and isinstance(this_release_info := releases.get(this_version), list) and this_release_info:
                if isinstance(this_release_info := this_release_info[0], dict):
                    this_release_date = (
                        parse_datetime(this_release_info.get("upload_time")))
            latest_non_beta_release_date = (
                parse_datetime(releases[latest_non_beta_version][0].get("upload_time")))
            latest_beta_version = None
            latest_beta_release_date = None
            if beta:
                # Return the latest beta version but only if it
                # is more recent than the latest non-beta version.
                try:
                    releases_reverse_sorted_by_time = (
                        sorted(releases.items(), key=lambda item: item[1][0]["upload_time"], reverse=True))
                    latest_beta_info = next(iter(releases_reverse_sorted_by_time))
                    if (latest_beta_version := latest_beta_info[0]) == latest_non_beta_version:
                        latest_beta_version = None
                    else:
                        latest_beta_release_date = (
                            parse_datetime(latest_beta_info[1][0].get("upload_time")))
                        if latest_non_beta_release_date > latest_beta_release_date:
                            latest_beta_version = None
                            latest_beta_release_date = None
                except Exception:
                    pass
            return (namedtuple("most_recent_pypi_package_version",
                               ["version", "release_date",
                                "beta_version", "beta_release_date", "this_version", "this_release_date"])
                    (latest_non_beta_version, format_datetime(latest_non_beta_release_date),
                     latest_beta_version, format_datetime(latest_beta_release_date),
                     this_version, format_datetime(this_release_date)))
    except Exception:
        pass
    return None


def remove_punctuation_and_space(value: str) -> str:
    return "".join(c for c in value if c not in string.punctuation + " ") if isinstance(value, str) else ""


@contextmanager
def catch_interrupt(on_interrupt: Optional[Callable] = None):
    if not callable(on_interrupt):
        on_interrupt = None
    def interrupt_handler(signum, frame):  # noqa
        if on_interrupt:
            if on_interrupt() is False:
                exit(1)
    try:
        previous_interrupt_handler = signal(SIGINT, interrupt_handler)
        yield
    finally:
        signal(SIGINT, previous_interrupt_handler)


@function_cache(serialize_key=True)
def get_health_page(key: dict) -> dict:
    return Portal(key).get_health().json()


def DEBUGGING():
    return isinstance(debug := os.environ.get("SMAHT_DEBUG"), str) and (debug.lower() == "true" or debug == "1")


def DEBUG(*args, **kwargs):
    if DEBUGGING():
        PRINT(*args, **kwargs)
