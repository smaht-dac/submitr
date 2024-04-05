import argparse
import io
import sys
import webbrowser
from typing import Optional, Tuple
from dcicutils.misc_utils import PRINT
from submitr.utils import get_version, get_most_recent_version_info, print_boxed


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
        if args.version or "version" in sys.argv:
            if version := self._get_version():
                is_most_recent_version, more_recent_version_message = self._get_most_recent_version_info(version)
                PRINT(f"{self._package or 'COMMAND'}: {version}{' ✓' if is_most_recent_version else ''} | {self.COPYRIGHT}")
                if more_recent_version_message:
                    PRINT(f"NOTE ▶ ▶ ▶ ▶ ▶ {more_recent_version_message}")
            else:
                PRINT(f"{self._package or 'COMMAND'}: No version available | {self.COPYRIGHT}")
            exit(0)
        elif args.help_advanced or args.help_web or args.help_raw or "help" in sys.argv:
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
        _, more_recent_version_message = self._get_most_recent_version_info()
        if more_recent_version_message:
            lines.append(more_recent_version_message)
            lines.append("===")
        print_boxed(lines, right_justified_macro=("[VERSION]", self._get_version))

    def _get_version(self) -> str:
        return get_version(self._package)

    def _get_most_recent_version_info(self, this_version: Optional[str] = None) -> Tuple[Optional[bool], Optional[str]]:
        if not this_version:
            this_version = self._get_version()
        is_beta_version = ("a" in this_version or "b" in this_version)
        is_most_recent_version = False
        more_recent_version_message = None
        if most_recent_version_info := get_most_recent_version_info():
            if ((most_recent_version_info.version == this_version) or
                (most_recent_version_info.beta_version == this_version)):  # noqa
                is_most_recent_version = True
        more_recent_version_message = (
            f"{self._package or 'COMMAND'}: {this_version}{' ✓' if is_most_recent_version else ''} | {self.COPYRIGHT}")
        if not is_most_recent_version:
            if is_beta_version and most_recent_version_info.beta_version:
                most_recent_version = most_recent_version_info.beta_version
            else:
                most_recent_version = most_recent_version_info.version
            more_recent_version_message = (
                f"A more recent version of this{' beta' if is_beta_version else ''}"
                f" software is available: {most_recent_version}")
        return (is_most_recent_version, more_recent_version_message)

    def is_pytest(self):
        return "pytest" in sys.modules
