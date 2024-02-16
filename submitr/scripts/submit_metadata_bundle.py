import argparse
import json
import os
from typing import Optional
import pkg_resources

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
    parser.add_argument('bundle_filename', nargs="?", help='Local Excel filename that comprises the data bundle.')
    parser.add_argument('--server', '-s',
                        help="HTTP(S) address of Portal server (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--env', '-e',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--consortium', help="Consoritium to use for submission.")
    parser.add_argument('--submission-center', help="Submission center to use for submission.")
    parser.add_argument('--post-only', action="store_true",
                        help="Only perform creates (POST) for submitted data.", default=False)
    parser.add_argument('--patch-only', action="store_true",
                        help="Only perform updates (PATCH) for submitted data.", default=False)
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--validate', '-v', action="store_true",
                        help="Perform both client-side and server-side validation first.", default=False)
    parser.add_argument('--validate-only', action="store_true",
                        help="Only perform validation of submitted data (on server-side).", default=False)
    parser.add_argument('--validate-first', action="store_true",
                        help="Perform validation of submitted data before submitting (on server-side).", default=False)
    parser.add_argument('--validate-local', action="store_true",
                        help="Validate submitted data locally (on client-side).")
    parser.add_argument('--validate-local-only', action="store_true",
                        help="Validate submitted data locally only (on client-side).")
    parser.add_argument('--directory', '-d', help="Directory of the upload files.")
    parser.add_argument('--upload_folder', '-u', help="Synonym for --directory.")
    parser.add_argument('--ingestion_type', '--ingestion-type', '-t',
                        help=f"The ingestion type (default: {DEFAULT_INGESTION_TYPE}).",
                        default=DEFAULT_INGESTION_TYPE)
    parser.add_argument('--no_query', '--no-query', '-nq', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--subdirectories', '-sd', action="store_true",
                        help="Search sub-directories of folder for upload files.", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="Synonym for --subdirectories", default=False)
    parser.add_argument('--app',
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=DEFAULT_SUBMISSION_PROTOCOL,
                        help=f"the submission protocol (default {DEFAULT_SUBMISSION_PROTOCOL!r})")
    parser.add_argument('--noadmin', action="store_true",
                        help="For testing only; assume not admin user.", default=False)
    parser.add_argument('--verbose', action="store_true", help="Debug output.", default=False)
    parser.add_argument('--debug', action="store_true", help="Debug output.", default=False)
    parser.add_argument('--version', action="store_true", help="Print version.", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    if args.version:
        if version := _get_package_version():
            print(f"smaht-submitr: {version}")
        else:
            print("smaht-submitr: No version available.")
        exit(0)
    if not args.bundle_filename:
        print("Missing submission file name.")
        exit(2)

    if args.directory:
        args.upload_folder = args.directory
    if args.subdirectories:
        args.subfolders = True

    _setup_validate_related_options(args)

    if args.keys:
        if not args.keys.endswith(".json") or not os.path.exists(args.keys):
            PRINT("The --keys argument must be the name of an existing .json file.")
            exit(1)

    with script_catch_errors():

        if not _sanity_check_submitted_file(args.bundle_filename):
            exit(1)

        submit_any_ingestion(ingestion_filename=args.bundle_filename, ingestion_type=args.ingestion_type,
                             server=args.server, env=args.env,
                             consortium=args.consortium,
                             submission_center=args.submission_center,
                             no_query=args.no_query, subfolders=args.subfolders, app=args.app,
                             submission_protocol=args.submission_protocol,
                             upload_folder=args.upload_folder,
                             show_details=args.debug,
                             post_only=args.post_only,
                             patch_only=args.patch_only,
                             validate_only=args.validate_only,
                             validate_first=args.validate_first,
                             validate_local=args.validate_local,
                             validate_local_only=args.validate_local_only,
                             keys_file=args.keys,
                             noadmin=args.noadmin,
                             verbose=args.verbose,
                             debug=args.debug)


def _sanity_check_submitted_file(file_name: str) -> bool:
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


def _setup_validate_related_options(args: argparse.Namespace):
    if not (args.validate_only and (args.validate_local or args.validate_local_only)):
        if args.validate_only:
            args.validate_local = False
        elif args.validate_local or args.validate_local_only:
            args.validate_first = False
            args.validate_only = False
    if args.validate_only:
        args.validate_first = False
    if args.validate and not (args.validate_only or args.validate_local_only or
                              args.validate_local_only or args.validate_first):
        # If --validate is specified and no other validate related options are
        # specified, then default to server-side and client-side validation.
        args.validate_local = True
        args.validate_first = True
    # Only need this --validate option to set other more specific validate related options.
    delattr(args, "validate")


def _get_package_version(package_name: str = "smaht-submitr") -> Optional[str]:
    try:
        return pkg_resources.get_distribution(package_name).version
    except Exception:
        return None


if __name__ == '__main__':
    main()
