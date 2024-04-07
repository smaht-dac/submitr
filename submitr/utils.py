from collections import namedtuple
from datetime import datetime
from functools import lru_cache
import io
import hashlib
import pkg_resources
import pytz
import re
import requests
import os
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union
from dcicutils.misc_utils import PRINT, str_to_bool
from json import dumps as json_dumps, loads as json_loads


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


def get_s3_bucket_and_key_from_s3_uri(uri: str) -> Tuple[str, str]:
    if match := re.match(r"s3://([^/]+)/(.+)", uri):
        return (match.group(1), match.group(2))
    return None, None


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


def format_duration(seconds: Union[int, float]):
    seconds_actual = seconds
    seconds = round(max(seconds, 0))
    durations = [("year", 31536000), ("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)]
    parts = []
    for name, duration in durations:
        if seconds >= duration:
            count = seconds // duration
            seconds %= duration
            if count != 1:
                name += "s"
            parts.append(f"{count} {name}")
    if len(parts) == 0:
        return f"{seconds_actual:.1f} seconds"
    elif len(parts) == 1:
        return f"{seconds_actual:.1f} seconds"
    else:
        return " ".join(parts[:-1]) + " " + parts[-1]


def format_size(nbytes: Union[int, float], precision: int = 2) -> str:
    UNITS = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    MAX_UNITS_INDEX = len(UNITS) - 1
    ONE_K = 1024
    index = 0
    if (precision := max(precision, 0)) and (nbytes <= ONE_K):
        precision -= 1
    while abs(nbytes) >= ONE_K and index < MAX_UNITS_INDEX:
        nbytes /= ONE_K
        index += 1
    if index == 0:
        nbytes = int(nbytes)
        return f"{nbytes} byte{'s' if nbytes != 1 else ''}"
    unit = UNITS[index]
    return f"{nbytes:.{precision}f} {unit}"


def format_datetime(value: datetime, verbose: bool = False) -> Optional[str]:
    try:
        tzlocal = datetime.now().astimezone().tzinfo
        if verbose:
            return value.astimezone(tzlocal).strftime(f"%A, %B %-d, %Y | %-I:%M %p %Z")
        else:
            return value.astimezone(tzlocal).strftime(f"%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return None


def parse_datetime_string_into_utc_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value).replace(tzinfo=pytz.utc)
    except Exception:
        return None


def format_path(path: str) -> str:
    if isinstance(path, str) and os.path.isabs(path) and path.startswith(os.path.expanduser("~")):
        path = "~/" + Path(path).relative_to(Path.home()).as_posix()
    return path


def get_file_size(file: str) -> int:
    try:
        return os.path.getsize(file) if isinstance(file, str) else ""
    except Exception:
        return -1


def get_file_modified_datetime(file: str) -> str:
    try:
        return format_datetime(datetime.fromtimestamp(os.path.getmtime(file)))
    except Exception:
        return ""


def get_file_checksum(file: str) -> str:
    return get_file_md5_like_aws_s3_etag(file)


def get_file_md5(file: str) -> str:
    if not isinstance(file, str):
        return ""
    try:
        md5 = hashlib.md5()
        with open(file, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception:
        return ""


def get_file_md5_like_aws_s3_etag(file: str) -> Optional[str]:
    try:
        with io.open(file, "rb") as f:
            return _get_file_md5_like_aws_s3_etag(f)
    except Exception:
        return None


def _get_file_md5_like_aws_s3_etag(f: io.BufferedReader) -> str:
    """
    Returns the AWS S3 "Etag" for the given file; this value is md5-like but
    not the same as a normal md5. We use this to compare that a file in S3
    appears to be the exact the same file as a local file. Adapted from:
    https://stackoverflow.com/questions/75723647/calculate-md5-from-aws-s3-etag
    """
    MULTIPART_THRESHOLD = 8388608
    MULTIPART_CHUNKSIZE = 8388608
    # BUFFER_SIZE = 1048576
    # Verify some assumptions are correct
    # assert(MULTIPART_CHUNKSIZE >= MULTIPART_THRESHOLD)
    # assert((MULTIPART_THRESHOLD % BUFFER_SIZE) == 0)
    # assert((MULTIPART_CHUNKSIZE % BUFFER_SIZE) == 0)
    hash = hashlib.md5()
    read = 0
    chunks = None
    while True:
        # Read some from stdin, if we're at the end, stop reading
        bits = f.read(1048576)
        if len(bits) == 0:
            break
        read += len(bits)
        hash.update(bits)
        if chunks is None:
            # We're handling a multi-part upload, so switch to calculating
            # hashes of each chunk
            if read >= MULTIPART_THRESHOLD:
                chunks = b''
        if chunks is not None:
            if (read % MULTIPART_CHUNKSIZE) == 0:
                # Dont with a chunk, add it to the list of hashes to hash later
                chunks += hash.digest()
                hash = hashlib.md5()
    if chunks is None:
        # Normal upload, just output the MD5 hash
        etag = hash.hexdigest()
    else:
        # Multipart upload, need to output the hash of the hashes
        if (read % MULTIPART_CHUNKSIZE) != 0:
            # Add the last part if we have a partial chunk
            chunks += hash.digest()
        etag = hashlib.md5(chunks).hexdigest() + "-" + str(len(chunks) // 16)
    return etag


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
            if line.endswith(macro_name):
                line = line.replace(macro_name, right_justified_macro[1]() + " ")
            lines_tmp.append(line)
        length = max(len(line) for line in lines_tmp)
    else:
        length = max(len(line) for line in lines)
    for line in lines:
        if line is None:
            continue
        if line == "===":
            printf(f"+{'-' * (length - len(line) + 5)}+")
        elif macro_name and line.endswith(macro_name):
            line = line.replace(macro_name, "")
            printf(f"| {line}{' ' * (length - len(line) - len(macro_value) - 1)} {macro_value} |")
        else:
            printf(f"| {line}{' ' * (length - len(line))} |")


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
                    this_release_date = parse_datetime_string_into_utc_datetime(this_release_info.get("upload_time"))
            latest_non_beta_release_date = (
                parse_datetime_string_into_utc_datetime(releases[latest_non_beta_version][0].get("upload_time")))
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
                            parse_datetime_string_into_utc_datetime(latest_beta_info[1][0].get("upload_time")))
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
