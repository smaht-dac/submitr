import argparse
import io
import sys
import webbrowser
from typing import Optional
import pkg_resources


class CustomArgumentParser(argparse.ArgumentParser):

    HELP_URL_VERSION = "dmichaels-20240205"
    HELP_URL = f"https://submitr.readthedocs.io/en/{HELP_URL_VERSION}/usage.html"
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
        if args.version:
            if version := self.get_package_version():
                print(f"{self._package or 'COMMAND'}: {version} | {self.COPYRIGHT}")
            else:
                print(f"{self._package or 'COMMAND'}: No version available | {self.COPYRIGHT}")
            exit(0)
        elif args.help_advanced or args.help_web or args.help_raw:
            self.print_help()
            exit(0)
        return args

    def print_help(self):
        if "--help-raw" in sys.argv:
            super().print_help()
            return
        if "--help-web" in sys.argv and self._help_url:
            webbrowser.open_new_tab(self._help_url)
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
        length = max(len(line) for line in lines)
        for line in lines:
            if line == "===":
                print(f"+{'-' * (length - len(line) + 5)}+")
            elif line.endswith("[VERSION]"):
                line = line.replace("[VERSION]", len("[VERSION]") * " ")
                version = self.get_package_version()
                print(f"| {line}{' ' * (length - len(line) - len(version) - 1)} {version} |")
            else:
                print(f"| {line}{' ' * (length - len(line))} |")

    def get_package_version(self) -> Optional[str]:
        try:
            return pkg_resources.get_distribution(self._package).version
        except Exception:
            return None

    def is_pytest(self):
        return "pytest" in sys.modules
