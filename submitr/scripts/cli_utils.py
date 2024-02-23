import argparse
import io
import sys
import webbrowser
from typing import Callable, List, Optional, Tuple
import pkg_resources
from dcicutils.misc_utils import PRINT


class CustomArgumentParser(argparse.ArgumentParser):

    HELP_URL_VERSION = "draft"
    HELP_URL = f"https://submitr.readthedocs.io/en/{HELP_URL_VERSION}"
    COPYRIGHT = "© Copyright 2020-2024 President and Fellows of Harvard College"

    def __init__(self, help: str, help_advanced: Optional[str] = None,
                 help_url: Optional[str] = None, package: Optional[str] = None):
        super().__init__()
        self._help = help
        self._help_advanced = help_advanced
        self._help_url = help_url
        self._package = package

    def parse_args(self, args):
        self.add_argument("--help-advanced", action="store_true",
                          help="Prints more advanced documentation.", default=False)
        self.add_argument("--help-raw", action="store_true",
                          help="Prints the raw version of this help message.", default=False)
        self.add_argument("--help-web", action="store_true",
                          help="Opens your browser to Web based documentation.", default=False)
        self.add_argument("--doc", action="store_true",
                          help="Synonym for --help-web.", default=False)
        self.add_argument("--version", action="store_true", help="Print version.", default=False)
        if self.is_pytest():
            return super().parse_args(args)
        args = None
        error = False
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        captured_output = io.StringIO()
        try:
            sys.stdout = captured_output
            sys.stderr = captured_output
            args = super().parse_args(args)
        except SystemExit:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self.print_help()
            error = True
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        if error:
            exit(2)
        if args.doc:
            args.help_web = True
        if args.version:
            if version := self.get_version():
                PRINT(f"{self._package or 'COMMAND'}: {version} | {self.COPYRIGHT}")
            else:
                PRINT(f"{self._package or 'COMMAND'}: No version available | {self.COPYRIGHT}")
            exit(0)
        elif args.help_advanced or args.help_web or args.help_raw:
            self.print_help()
            exit(0)
        return args

    def print_help(self):
        if "--help-raw" in sys.argv:
            super().print_help()
            return
        if ("--help-web" in sys.argv or "--doc" in sys.argv) and self._help_url:
            webbrowser.open_new_tab(self._help_url + "/usage.html")
            return
        if "--help-advanced" in sys.argv and self._help_advanced:
            help_message = self._help_advanced
        else:
            help_message = self._help
        help_message += f"{self.COPYRIGHT}\n==="
        lines = help_message.split("\n")
        if lines[0] == "":
            lines = lines[1:]
        if lines[len(lines) - 1] == "":
            lines = lines[:len(lines) - 1]
        print_boxed(lines, right_justified_macro=("[VERSION]", self.get_version))

    def get_version(self) -> str:
        try:
            return pkg_resources.get_distribution(self._package).version
        except Exception:
            return ""

    def is_pytest(self):
        return "pytest" in sys.modules


def print_boxed(lines: List[str], right_justified_macro: Optional[Tuple[str, Callable]] = None) -> None:
    length = max(len(line) for line in lines)
    for line in lines:
        if line == "===":
            PRINT(f"+{'-' * (length - len(line) + 5)}+")
        elif right_justified_macro and (len(right_justified_macro) == 2) and line.endswith(right_justified_macro[0]):
            line = line.replace(right_justified_macro[0], len(right_justified_macro[0]) * " ")
            version = right_justified_macro[1]()
            PRINT(f"| {line}{' ' * (length - len(line) - len(version) - 1)} {version} |")
        else:
            PRINT(f"| {line}{' ' * (length - len(line))} |")
