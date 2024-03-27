from datetime import datetime
import io
import os
import pkg_resources
import sys
from typing import Callable, Optional, Tuple
from dcicutils.command_utils import yes_or_no
from dcicutils.misc_utils import PRINT as __PRINT
from .utils import show as __show

# TODO: Cleanup this arbitrary differentiation between
# print and show; but need to fix tests when this happens.


def _print(*args, **kwargs):
    __PRINT(*args, **kwargs)


def _show(*args, **kwargs):
    __show(*args, **kwargs)


PRINT = _print
PRINT_STDOUT = _print
PRINT_OUTPUT = _print
SHOW = _show
ERASE_LINE = "\033[K"

_OUTPUT_FILE = None


def setup_for_output_file_option(output_file: str) -> Tuple[Callable, Callable, Callable, Callable]:
    global SHOW, PRINT, PRINT_STDOUT, PRINT_OUTPUT, _OUTPUT_FILE
    if os.path.exists(output_file):
        PRINT(f"Output file already exists: {output_file}")
        if not yes_or_no("Overwrite this file?"):
            exit(1)
        with io.open(output_file, "w"):
            pass
    _OUTPUT_FILE = output_file  # Assuming this is only called once/globally
    PRINT(f"Logging to output file: {output_file}")
    def append_to_output_file(*args):  # noqa
        string = io.StringIO()
        __PRINT(*args, file=string)
        with io.open(output_file, "a") as f:
            f.write(string.getvalue())
            f.flush()
    def show_and_output_to_file(*args, **kwargs):  # noqa
        append_to_output_file(*args)
        _show(*args, **kwargs)
    def print_and_output_to_file(*args, **kwargs):  # noqa
        append_to_output_file(*args)
        _print(*args, **kwargs)
    def print_to_stdout_only(*args, **kwargs):  # noqa
        __PRINT(*args, **kwargs)
    def print_to_output_file_only(*args, end=None):  # noqa
        append_to_output_file(*args)
    def current_datetime_formatted() -> str:  # noqa
        tzlocal = (now := datetime.now()).astimezone().tzinfo
        return now.astimezone(tzlocal).strftime(f"%Y-%m-%d %H:%M:%S %Z")
    SHOW = show_and_output_to_file
    PRINT = print_and_output_to_file
    PRINT_STDOUT = print_to_stdout_only
    PRINT_OUTPUT = print_to_output_file_only  # if an output file was specified, if not, stdout
    append_to_output_file(f"TIME: {current_datetime_formatted()}")
    append_to_output_file(f"COMMAND: {' '.join(sys.argv)}")
    append_to_output_file(f"VERSION: {get_version()}")
    return PRINT, PRINT_OUTPUT, PRINT_STDOUT, SHOW


def get_output_file() -> Optional[str]:
    return _OUTPUT_FILE


def get_version() -> str:
    try:
        return pkg_resources.get_distribution("smaht-submitr").version
    except Exception:
        return ""
