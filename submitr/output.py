from __future__ import annotations
from datetime import datetime
import io
import os
import pkg_resources
import sys
from typing import Callable, Optional, Tuple
from dcicutils.command_utils import yes_or_no
from dcicutils.misc_utils import PRINT as __PRINT
from submitr.utils import chars, show as __show

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


class Question:
    """
    Supports the asking the user (via stdin) a yes/no question, possibly repeatedly; and
    after some maximum number times of the same answer in a row (consecutively), then asks
    them if they want to automatically give that same answer to any/all subsequent questions.
    Supports static/global list of such Question instances, hashed (only) by the question text.
    """
    _static_instances = {}

    @staticmethod
    def instance(question: Optional[str] = None,
                 max: Optional[int] = None, printf: Optional[Callable] = None) -> Question:
        question = question if isinstance(question, str) else ""
        if not (instance := Question._static_instances.get(question)):
            Question._static_instances[question] = (instance := Question(question, max=max, printf=printf))
        return instance

    @staticmethod
    def yes(question: Optional[str] = None,
            max: Optional[int] = None, printf: Optional[Callable] = None) -> bool:
        return Question.instance(question, max=max, printf=printf).ask()

    def __init__(self, question: Optional[str] = None,
                 max: Optional[int] = None, printf: Optional[Callable] = None) -> None:
        self._question = question if isinstance(question, str) else ""
        self._max = max if isinstance(max, int) and max > 0 else None
        self._print = printf if callable(printf) else print
        self._yes_consecutive_count = 0
        self._no_consecutive_count = 0
        self._yes_automatic = False
        self._no_automatic = False

    def ask(self, question: Optional[str] = None) -> bool:

        def question_automatic(value: str) -> bool:
            nonlocal self
            if yes_or_no(f"{chars.rarrow}{chars.rarrow}{chars.rarrow}"
                         f" Do you want to answer {value} to all such questions?"
                         f" {chars.larrow}{chars.larrow}{chars.larrow}"):
                return True
            self._yes_consecutive_count = 0
            self._no_consecutive_count = 0

        if self._yes_automatic:
            return True
        elif self._no_automatic:
            return False
        elif yes_or_no((question if isinstance(question, str) else "") or self._question or "Undefined question"):
            self._yes_consecutive_count += 1
            self._no_consecutive_count = 0
            if (self._no_consecutive_count == 0) and self._max and (self._yes_consecutive_count >= self._max):
                # Have reached the maximum number of consecutive YES answers; ask if YES to all subsequent.
                if question_automatic("YES"):
                    self._yes_automatic = True
            return True
        else:
            self._no_consecutive_count += 1
            self._yes_consecutive_count = 0
            if (self._yes_consecutive_count == 0) and self._max and (self._no_consecutive_count >= self._max):
                # Have reached the maximum number of consecutive NO answers; ask if NO to all subsequent.
                if question_automatic("NO"):
                    self._no_automatic = True
            return False
