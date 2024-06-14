from __future__ import annotations
import multiprocessing
import sys
from typing import Optional
from submitr.scripts.check_submission import main as main_check_submission
from submitr.scripts.get_metadata_template import main as main_get_metadata_template
from submitr.scripts.list_submissions import main as main_list_submissions
from submitr.scripts.rcloner import main as main_rcloner
from submitr.scripts.resume_uploads import main as main_resume_uploads
from submitr.scripts.submit_metadata_bundle import main as main_submit_metadata_bundle
from submitr.scripts.view_portal_object import main as main_view_portal_object
from submitr.utils import get_version

# This exists primarily to support pyinstaller method of running smaht-submitr commands.
# where we package a single command (this module) into a self-contained independent
# executable file (via pyinstaller) which can be run WITHOUT Python (and any
# related tools like pyenv) having to be installed.


def usage(message: Optional[str] = None) -> None:
    if isinstance(message, str) and message:
        print(message)
    print("usage: submitr [command] [arguments]")
    print("commands: ")
    for command in supported_commands:
        if command not in supported_commands_hide:
            print(f"- {command}")
    sys.exit(1)


def main_version():
    print(f"{get_version()}")
    sys.exit(0)


supported_commands = {
    "check-submission": main_check_submission,
    "get-metadata-template": main_get_metadata_template,
    "help": usage,
    "list-submissions": main_list_submissions,
    "rcloner": main_rcloner,
    "resume-uploads": main_resume_uploads,
    "submit-metadata": main_submit_metadata_bundle,
    "submit-metadata-bundle": main_submit_metadata_bundle,
    "version": main_version,
    "view-portal-object": main_view_portal_object
}

# Older names for backward compatibility.
supported_commands_hide = ["submit-metadata-bundle"]


def main() -> None:
    multiprocessing.freeze_support()
    if len(sys.argv) < 2:
        usage()
    if (command := sys.argv[1]) not in supported_commands:
        usage(f"Unknown command: {command}")
        sys.exit(1)
    sys.argv = sys.argv[1:]
    supported_commands[command]()
    sys.exit(0)


if __name__ == "__main__":
    main()
