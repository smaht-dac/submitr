import argparse
import json
import os
from typing import Optional

from dcicutils.command_utils import script_catch_errors
from dcicutils.misc_utils import PRINT
from ..base import DEFAULT_APP
from ..submission import (
    submit_any_ingestion, DEFAULT_INGESTION_TYPE, DEFAULT_SUBMISSION_PROTOCOL, SUBMISSION_PROTOCOLS
)


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('bundle_filename', help='a local Excel filename that is the data bundle')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--post-only', action="store_true",
                        help="Only perform creates (POST) for submitted data.", default=False)
    parser.add_argument('--patch-only', action="store_true",
                        help="Only perform updates (PATCH) for submitted data.", default=False)
    parser.add_argument('--validate-only', '-v', action="store_true",
                        help="Only perform validation of submitted data.", default=False)
    parser.add_argument('--sheet-utils', action="store_true",
                        help="Used sheet_utils rather than the new structured_data to data parsing.", default=False)
    parser.add_argument('--upload_folder', '-u', help="location of the upload files", default=None)
    parser.add_argument('--ingestion_type', '--ingestion-type', '-t', help="the ingestion type",
                        default=DEFAULT_INGESTION_TYPE)
    parser.add_argument('--no_query', '--no-query', '-nq', action="store_true",
                        help="suppress requests for user input", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="search subfolders of folder for upload files", default=False)
    parser.add_argument('--app', default=None,
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=DEFAULT_SUBMISSION_PROTOCOL,
                        help=f"the submission protocol (default {DEFAULT_SUBMISSION_PROTOCOL!r})")
    parser.add_argument('--details', '-d', action="store_true",
                        help="retrieve and display detailed info", default=False)
    parser.add_argument('--verbose', action="store_true", help="verbose output", default=False)
    parser.add_argument('--validate-local', action="store_true",
                        help="validate file locally before submission", default=False)
    parser.add_argument('--validate-local-only', action="store_true",
                        help="validate file locally only (no submission)", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    if args.validate_local_only:
        args.validate_local = True

    with script_catch_errors():

        if not sanity_check_submitted_file(args.bundle_filename):
            exit(1)

        submit_any_ingestion(ingestion_filename=args.bundle_filename, ingestion_type=args.ingestion_type,
                             server=args.server, env=args.env,
                             no_query=args.no_query, subfolders=args.subfolders, app=args.app,
                             submission_protocol=args.submission_protocol,
                             upload_folder=args.upload_folder,
                             show_details=(args.verbose or args.details),
                             post_only=args.post_only,
                             patch_only=args.patch_only,
                             validate_only=args.validate_only,
                             validate_local=args.validate_local,
                             validate_local_only=args.validate_local_only,
                             sheet_utils=args.sheet_utils)


def sanity_check_submitted_file(file_name: str) -> bool:
    """
    Performs some basic sanity checking on the specified file.
    If it is a JSON file (i.e. with a .json file extension) make sure it can load.
    If it is a zip file (or .tar.gz or other type of archive file) then tell the user
    that it must contain a single directory whose name is the base name of the file
    with a "-inserts" suffix. Returns True if passed sanity check otherwise False.
    """

    def get_unpackable_file_extension(file_name: str) -> Optional[str]:
        UNPACKABLE_EXTENSIONS = [".tar.gz", ".tar", ".tgz", ".gz", ".zip"]
        for extension in UNPACKABLE_EXTENSIONS:
            if file_name.endswith(extension):
                return extension
        return None

    def is_unpackable_file(file_name: str) -> bool:
        return False
        return get_unpackable_file_extension(file_name) is not None

    def is_properly_named_unpackable_file(file_name: str) -> bool:
        unpackable_extension = get_unpackable_file_extension(file_name)
        if not unpackable_extension:
            return False
        base_file_name = file_name[:-len(unpackable_extension)]
        return base_file_name.endswith("-inserts") or base_file_name.endswith("_inserts")

    if not os.path.exists(file_name):
        PRINT(f"File does not exist: {file_name}")
        return False

    if file_name.endswith(".json"):
        try:
            with open(file_name, "r") as f:
                json.load(f)
        except Exception:
            PRINT(f"Cannot load JSON from file: {file_name}")
            return False

    sanity_check_passed = True
    if is_unpackable_file(file_name):
        extension = get_unpackable_file_extension(file_name)
        PRINT(f"NOTE: If this archive ({extension[1:]}) file is intended to contain multiple files then: ")
        PRINT(f"- The archive file must be named like: ANYNAME-inserts{extension}", end="")
        if not is_properly_named_unpackable_file(file_name):
            PRINT(f" -> And it is NOT.")
            sanity_check_passed = False
        else:
            PRINT(f" -> And it is.")
        PRINT(f"- The archive file must contain ONLY a directory with your files directly within it.")
        PRINT(f"- And that directory name must be named for the base name")
        PRINT(f"  of your file with a -inserts suffix, e.g. ANYNAME-inserts.")

    return sanity_check_passed


if __name__ == '__main__':
    main()
