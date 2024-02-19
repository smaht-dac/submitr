import argparse
import json
import os
from dcicutils.command_utils import script_catch_errors
from dcicutils.misc_utils import PRINT
from .cli_utils import CustomArgumentParser
from ..base import DEFAULT_APP
from ..submission import (
    submit_any_ingestion,
    DEFAULT_INGESTION_TYPE,
    DEFAULT_SUBMISSION_PROTOCOL,
    SUBMISSION_PROTOCOLS
)

_HELP = f"""
===
submit-metadata-bundle [VERSION]
===
Tool to submit submission metadata and files to SMaHT Portal.
See: {CustomArgumentParser.HELP_URL}#submission
===
USAGE: submit-metadata-bundle METADATA-FILE OPTIONS
-----
METADATA-FILE: This is the path to your metatdata file.
===
OPTIONS:
===
--env ENVIRONMENT-NAME
  To specify your environment name; from your ~/.smaht-keys.json file.
--validate
  To validate metadata before submitting.
  This is the DEFAULT behavior for most (non-admin) users.
--consortium CONSORTIUM
  To specify your consortium.
  Default is to use the consortium associated with your account.
--submission-center SUBMISSION-CENTER
  To specify your submission center.
  Default is to use the submission center associated with your account.
--directory DIRECTORY
  To specify a directory containing the files to upload; in addition
  to the default of using the directory containing the submitted file.
--sub-directories
  To specify that any sub-directories of the directory containing
  the upload file(s) should be searched, recursively.
--keys KEYS-FILE
  To specify an alternate credentials/keys
  file to the default ~/.smaht-keys.json file.
--verbose
  For more verbose output.
--help
  Prints this documentation.
--help-advanced
  Prints this plus more advanced documentation.
===
"""
_HELP_ADVANCED = _HELP.strip() + f"""
ADVANCED OPTIONS:
===
--validate-only
  Performs ONLY, but BOTH client-side (local) and
  server-side (remote) validation only WITHOUT submitting.
--validate-local-only
  Performs ONLY client-side (local) validation WITHOUT submitting.
--validate-remote-only
  Performs ONLY server-side (remote) validation WITHOUT submitting.
--validate-local
  Performs only client-side (local) validation before submitting.
--validate-remote
  Performs only server-side (remote) validation before submitting.
--patch-only
  Perform ONLY updates (PATCHes) for submitted data.
--post-only
  Perform ONLY creates (POSTs) for submitted data.
--yes
  Automatically answer 'yes' to any confirmation questions.
--noadmin
  Act like you are not an admin user even you are.
  For testing/troubleshooting only.
--help-raw
  Prints the raw version of this help message.
--help-web
  Opens your browser to the Web based documentation.
  {CustomArgumentParser.HELP_URL}#submission
===
"""


def main(simulated_args_for_testing=None):
    parser = CustomArgumentParser(_HELP, _HELP_ADVANCED, CustomArgumentParser.HELP_URL, package="smaht-submitr")
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
    parser.add_argument('--validate-remote', action="store_true",
                        help="Perform validation of submitted data before submitting (on server-side).", default=False)
    parser.add_argument('--validate-remote-only', action="store_true",
                        help="Only perform validation of submitted data (on server-side).", default=False)
    parser.add_argument('--validate-local', action="store_true",
                        help="Validate submitted data locally (on client-side).")
    parser.add_argument('--validate-local-only', action="store_true",
                        help="Validate submitted data locally only (on client-side).")
    parser.add_argument('--directory', '-d', help="Directory of the upload files.")
    parser.add_argument('--upload_folder', '-u', help="Synonym for --directory.")
    parser.add_argument('--ingestion_type', '--ingestion-type', '-t',
                        help=f"The ingestion type (default: {DEFAULT_INGESTION_TYPE}).",
                        default=DEFAULT_INGESTION_TYPE)
    parser.add_argument('--yes', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--no_query', '--no-query', '-nq', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--sub-directories', '-sd', action="store_true",
                        help="Search sub-directories of folder for upload files.", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="Synonym for --sub-directories", default=False)
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
    args = parser.parse_args(args=simulated_args_for_testing)

    if args.directory:
        args.upload_folder = args.directory
    if args.sub_directories:
        args.subfolders = True

    if args.yes:
        args.no_query = True

    if not args.bundle_filename:
        PRINT("Missing submission file name.")
        exit(2)

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        PRINT(f"WARNING: Directory does not exist: {args.upload_folder}")
        # TODO: exist breaks test ...
        # FAILED submitr/tests/test_submit_metadata_bundle.py::test_submit_metadata_bundle_script[None]
        # FAILED submitr/tests/test_submit_metadata_bundle.py::test_submit_metadata_bundle_script[foo.bar]
        # exit(1)

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
                             validate_local=args.validate_local,
                             validate_local_only=args.validate_local_only,
                             validate_remote_only=args.validate_remote_only,
                             validate_remote=args.validate_remote,
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
    if not os.path.exists(file_name):
        PRINT(f"Submission file does not exist: {file_name}")
        return False

    if file_name.endswith(".json"):
        try:
            with open(file_name, "r") as f:
                json.load(f)
        except Exception:
            PRINT(f"Cannot load JSON from file: {file_name}")
            return False

    return True


def _setup_validate_related_options(args: argparse.Namespace):

    validate_option_count = 0
    if args.validate:
        validate_option_count += 1
    if args.validate_only:
        validate_option_count += 1
    if args.validate_local:
        validate_option_count += 1
    if args.validate_local_only:
        validate_option_count += 1
    if args.validate_remote:
        validate_option_count += 1
    if args.validate_remote_only:
        validate_option_count += 1
    if validate_option_count > 1:
        PRINT("Only specify ONE of the validate options.")
        exit(1)

    if args.validate:
        # L-LO-R-RO = T-F-T-F
        args.validate_local = True
        args.validate_local_only = False
        args.validate_remote = True
        args.validate_remote_only = False
    elif args.validate_only:
        # L-LO-R-RO = T-F-F-T
        args.validate_local = True
        args.validate_local_only = False
        args.validate_remote = False
        args.validate_remote_only = True
    elif args.validate_local:
        # L-LO-R-RO = T-F-F-F
        args.validate_local = True
        args.validate_local_only = False
        args.validate_remote = False
        args.validate_remote_only = False
    elif args.validate_local_only:
        # L-LO-R-RO = F-T-F-F
        args.validate_local = False
        args.validate_local_only = True
        args.validate_remote = False
        args.validate_remote_only = False
    elif args.validate_remote:
        # L-LO-R-RO = F-F-T-F
        args.validate_local = False
        args.validate_local_only = False
        args.validate_remote = True
        args.validate_remote_only = False
    elif args.validate_remote_only:
        # L-LO-R-RO = F-F-F-T
        args.validate_local = False
        args.validate_local_only = False
        args.validate_remote = False
        args.validate_remote_only = True

    delattr(args, "validate")
    delattr(args, "validate_only")


if __name__ == '__main__':
    main()
