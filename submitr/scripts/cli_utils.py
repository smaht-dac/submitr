import argparse
from functools import lru_cache
import io
import subprocess
import sys
import time
import webbrowser
from typing import List, Optional, Union
from dcicutils.command_utils import yes_or_no
from dcicutils.misc_utils import PRINT
from submitr.utils import get_version, get_most_recent_version_info, print_boxed


class CustomArgumentParser(argparse.ArgumentParser):

    PACKAGE = "smaht-submitr"
    HELP_URL_VERSION = "latest"
    HELP_URL = f"https://submitr.readthedocs.io/en/{HELP_URL_VERSION}"
    COPYRIGHT = "© Copyright 2020-2024 President and Fellows of Harvard College"

    def __init__(self, help: str, help_advanced: Optional[str] = None,
                 help_url: Optional[str] = None,
                 obsolete_options: Optional[List[dict]] = None,
                 package: Optional[str] = None):
        super().__init__()
        if not package:
            package = self.PACKAGE
        self._help = help
        self._help_advanced = help_advanced
        self._help_url = help_url
        self._obsolete_options = obsolete_options
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
        self.add_argument("--version", "-version", "--v", "-v", action="store_true",
                          help="Print version.", default=False)
        if self.is_pytest():
            return super().parse_args(args)
        self._check_obsolete_options()
        self._check_help_options()
        self._check_version_options()
        args = self._parse_args()
        return args

    def _parse_args(self) -> argparse.Namespace:
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
        return args

    def _check_obsolete_options(self) -> None:
        if self._obsolete_options:
            nobsolete_options = 0
            for obsolete_option in self._obsolete_options:
                if obsolete_option["option"] in sys.argv:
                    PRINT(f"Obsolete option: {obsolete_option['option']} ▶ {obsolete_option['message']}")
                    nobsolete_options += 1
            if nobsolete_options > 0:
                exit(1)

    def _check_help_options(self) -> None:
        for arg in sys.argv:
            if arg in ["help", "-help", "--help", "-h", "--h", "?", "-?", "--?",
                       "--help-raw", "--help-advanced", "--help-web"]:
                self.print_help()
                exit(0)

    def _check_version_options(self) -> None:
        for arg in sys.argv:
            if arg in ["version", "-version", "--version", "-v", "--v"]:
                self._print_version(verbose=("-v" not in sys.argv) and ("--v" not in sys.argv))
                exit(0)

    def print_help(self) -> None:
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
        most_recent_version_info = self._get_most_recent_version_info()
        most_recent_version_info = self._get_most_recent_version_info()
        if isinstance(most_recent_version_info, str):
            lines.append(most_recent_version_info)
            lines.append("===")
        print_boxed(lines, right_justified_macro=("[VERSION]", self._get_version))

    def _print_version(self, verbose: bool = False, noupdate: bool = False) -> None:
        if version := self._get_version(with_most_recent_check_mark=False):
            if verbose and (most_recent_version_info := get_most_recent_version_info()):
                has_most_recent_version = (
                    (most_recent_version_info.version == version) or
                    (most_recent_version_info.beta_version == version))
                if most_recent_version_info.this_release_date:
                    version_release_date = f" | {most_recent_version_info.this_release_date}"
                else:
                    version_release_date = ""
                lines = [
                    "===",
                    "smaht-submitr [VERSION]",
                    "===",
                    f"This version: {version}{version_release_date}",
                    f"Most recent version: {most_recent_version_info.version}"
                        f" | {most_recent_version_info.release_date}",  # noqa
                    f"Most recent beta version: {most_recent_version_info.beta_version}"
                        f" | {most_recent_version_info.beta_release_date}"
                            if most_recent_version_info.beta_version else None,  # noqa
                ]
                if not has_most_recent_version and most_recent_version_info.this_release_date:
                    lines += [
                        "===",
                        f"▶ A more recent version is available ▶ See update command below:",
                        f"▶ pip install {self.PACKAGE}=={most_recent_version_info.version}",
                        f"▶ pip install {self.PACKAGE}=={most_recent_version_info.beta_version}"
                            if most_recent_version_info.beta_version else None,  # noqa
                    ]
                lines += [
                    "===",
                    "For all versions see: https://pypi.org/project/smaht-submitr",
                    "===",
                    self.COPYRIGHT,
                    "==="
                ]
                print_boxed(lines, right_justified_macro=("[VERSION]", self._get_version))
                if not noupdate and not has_most_recent_version and most_recent_version_info.this_release_date:
                    is_beta_version = ("a" in most_recent_version_info.this_version or
                                       "b" in most_recent_version_info.this_version)
                    if is_beta_version and most_recent_version_info.beta_version:
                        version_to_update_to = most_recent_version_info.beta_version
                    else:
                        version_to_update_to = most_recent_version_info.version
                    if yes_or_no(f"Do you want to install the newer version ({version_to_update_to})?"):
                        subprocess.run(["pip", "install", f"{self._package}=={version_to_update_to}"])
                        time.sleep(2)
                        subprocess.run(["submit-metadata-bundle", "version"])
                return
            else:
                PRINT(f"{self._package or 'COMMAND'}: {version}")
                return
        PRINT(f"{self._package or 'COMMAND'}: No version available")

    @lru_cache(maxsize=1)
    def _get_version(self, with_most_recent_check_mark: bool = True) -> str:
        version = get_version(self._package)
        if with_most_recent_check_mark and (self._get_most_recent_version_info(version) is True):
            version = f"✓ {version}"
        return version

    @lru_cache(maxsize=1)
    def _get_most_recent_version_info(self, this_version: Optional[str] = None) -> Union[bool, str]:
        if not this_version:
            this_version = self._get_version()
        if this_version.startswith("✓ "):
            this_version = this_version[2:]
        is_beta_version = ("a" in this_version or "b" in this_version)
        is_most_recent_version = False
        more_recent_version_message = None
        if most_recent_version_info := get_most_recent_version_info():
            if ((most_recent_version_info.version == this_version) or
                (most_recent_version_info.beta_version == this_version)):  # noqa
                is_most_recent_version = True
        more_recent_version_message = (
            f"{self._package or 'COMMAND'}: {this_version}{' ✓' if is_most_recent_version else ''}")
        if is_most_recent_version:
            return True
        if is_beta_version and most_recent_version_info.beta_version:
            most_recent_version = most_recent_version_info.beta_version
        else:
            most_recent_version = most_recent_version_info.version
        more_recent_version_message = (
            f"A more recent version of this"
            f"{' beta' if is_beta_version and most_recent_version_info.beta_version else ''}"
            f" software is available: {most_recent_version}")
        return more_recent_version_message

    def is_pytest(self) -> bool:
        return "pytest" in sys.modules
