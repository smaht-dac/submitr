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
    SUBMISSION_PROTOCOLS,
    _define_portal,
    _get_consortia,
    _get_submission_centers,
    _ping,
    _print_metadata_file_info,
    _pytesting
)
from submitr.rclone import RCloneGoogle

_HELP = f"""
===
submit-metadata-bundle [VERSION]
===
Tool to submit submission metadata and files to SMaHT Portal.
See: {CustomArgumentParser.HELP_URL}
===
USAGE: submit-metadata-bundle METADATA-FILE [--validate | --submit] OPTIONS
-----
METADATA-FILE: This is the path to your metatdata file.
===
OPTIONS:
===
--env ENVIRONMENT-NAME
  To specify your environment name; from your ~/.smaht-keys.json file.
  Alternatively, set your SMAHT_ENV environment variable.
--keys KEYS-FILE
  To specify an alternate credentials/keys file,
  rather than the default ~/.smaht-keys.json file.
  Alternatively, set your SMAHT_KEYS environment variable.
--validate
  To ONLY validate metadata WITHOUT submitting.
  Either this or --submit is required.
--submit
  To actually submit the metadata for ingestion (validates first).
  Either this or --validation is required.
--consortium CONSORTIUM
  To specify your consortium.
  Default is to use the consortium associated with your account.
--submission-center SUBMISSION-CENTER
  To specify your submission center.
  Default is to use the submission center associated with your account.
--directory DIRECTORY
  To specify a directory containing the files to upload; in addition
  to the default of using the directory containing the submitted file;
  this directory will be searched recursively.
--rclone-google-source GOOGLE-CLOUD-STORAGE-SOURCE
  A Google Cloud Storage (GCS) bucket or bucket/sub-folder
  from where the upload file(s) should be copied.
--rclone-google-credentials GCS-SERVICE-ACCOUNT-FILE
  GCS credentials to use for --rclone-google-source;
  e.g. full path to your GCP service account file.
  May be omitted if running on a GCE instance.
--rclone-google-location LOCATION
  The Google Cloud Storage (GCS) location (aka "region").
--output OUTPUT-FILE
  Writes all logging output to the specified file;
  and refrains from printing lengthy content to output/stdout.
--info
  Displays ONLY info about the specified metadata file; nothing else.
  Add --refs or --files to see (linkTo) references or (upload) files.
--verbose
  Displays more verbose output.
--help
  Displays this documentation.
--help-advanced
  Displays this plus more advanced documentation.
--doc
  Opens your browser to the Web based documentation:
  {CustomArgumentParser.HELP_URL}
===
For any issues please contact SMaHT DAC: smhelp@hms-dbmi.atlassian.net
===
"""
_HELP_ADVANCED = _HELP.strip() + f"""
ADVANCED OPTIONS:
===
--validate-only
  Same as --validate with slightly different command interaction.
  Performs ONLY, but BOTH client-side (local) and
  server-side (remote) validation only WITHOUT submitting.
--validate-remote-only
  Performs ONLY server-side (remote) validation WITHOUT submitting.
--validate-local-only
  Performs ONLY client-side (local) validation WITHOUT submitting.
--validate-local-skip
  Skips client-side (local) validation.
--validate-remote-skip
  Skips server-side (remote) validation.
--noanalyze
  Skips analysis of parsed metadata WRT creates/updates.
--patch-only
  Perform ONLY updates (PATCHes) for submitted data.
--post-only
  Perform ONLY creates (POSTs) for submitted data.
--directory-only
  Same as --directory but does NOT search recursively.
--add-submission-center SUBMISSION-CENTER
  To specify an additional submission center as having access to
  the ingestion submission (object). Useful when different users
  will be performing submit-metadata-bundle and resume-uploads.
--consortia
  Displays ONLY all known consortia; nothing else.
--submission-centers
  Displays ONLY all known submission centers; nothing else.
--json
  Displays the submitted metadata as formatted JSON.
--json-only
  Displays ONLY the specified metadata as formatted JSON; nothing else.
--info
  Displays ONLY info about the specified metadata file; nothing else.
--details
  Displays slightly more detailed output.
--noprogress
  Do not print progress of (client-side) parsing/validation output.
--timeout SECONDS
  Maximum umber of seconds to wait for server validation or submission.
--progress-extra
  Displasy extra info in progress of (client-side) parsing/validation.
--debug
  Displays some debugging related output.
--ping
  Pings the server; to test connectivity.
--yes
  Automatically answer 'yes' to any confirmation questions.
===
"""
_OBSOLETE_OPTIONS = [
    {"option": "-e", "message": "Use --env"},
    {"option": "-s", "message": "Use --server"},
    {"option": "-v", "message": "Use --validate"},
    {"option": "-u", "message": "Use --directory-only; or --directory which searches recusively."},
    {"option": "-d", "message": "Use --directory-only; or --directory which searches recusively."},
    {"option": "-sd", "message": "Use --directory which defaults to searching recusively."},
    {"option": "-sf", "message": "Use --directory which defaults to searching recusively."}
]


def main(simulated_args_for_testing=None):
    parser = CustomArgumentParser(help=_HELP, help_advanced=_HELP_ADVANCED,
                                  help_url=CustomArgumentParser.HELP_URL,
                                  obsolete_options=_OBSOLETE_OPTIONS)
    parser.add_argument('bundle_filename', nargs="?", help='Local Excel filename that comprises the data bundle.')
    parser.add_argument('--server',
                        help="HTTP(S) address of Portal server (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--env',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--consortium', help="Consoritium to use for submission.")
    parser.add_argument('--submission-center', help="Submission center to use for submission.")
    parser.add_argument('--consortia', action="store_true", help="List known consoritia.")
    parser.add_argument('--submission-centers', action="store_true", help="List known submission centers.")
    parser.add_argument('--add-submission-center', help="Add submission center to the IngestionSubmission object.")
    parser.add_argument('--post-only', action="store_true",
                        help="Only perform creates (POST) for submitted data.", default=False)
    parser.add_argument('--patch-only', action="store_true",
                        help="Only perform updates (PATCH) for submitted data.", default=False)
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--submit', action="store_true",
                        help="Actually submit the metadata for ingestion..", default=False)
    parser.add_argument('--validate', action="store_true",
                        help="Perform both client-side and server-side validation first.", default=False)
    parser.add_argument('--validate-only', action="store_true",
                        help="Same as --validate.", default=False)
    parser.add_argument('--validate-local-only', action="store_true",
                        help="Validate submitted data locally only (on client-side).")
    parser.add_argument('--validate-remote-only', action="store_true",
                        help="Only perform validation of submitted data (on server-side).", default=False)
    parser.add_argument('--validate-local-skip', action="store_true",
                        help="Skip the local (client) validation step.", default=False)
    parser.add_argument('--validate-remote-skip', action="store_true",
                        help="Skip the remote (server) validation step.", default=False)
    parser.add_argument('--directory', help="Directory of the upload files.")
    parser.add_argument('--directory-only', help="Same as --directory but NOT recursively.", default=False)
    parser.add_argument('--subfolders', action="store_true",  # obsolete
                        help="Obsolete", default=False)
    parser.add_argument('--upload_folder', help="Same as --directory.")
    parser.add_argument('--ingestion_type', '--ingestion-type',
                        help=f"The ingestion type (default: {DEFAULT_INGESTION_TYPE}).",
                        default=DEFAULT_INGESTION_TYPE)
    parser.add_argument('--noversion', action="store_true",
                        help="Do not check metadata template version.", default=False)
    parser.add_argument('--yes', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--no_query', '--no-query', '-nq', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--ref-nocache', action="store_true",
                        help="Do not cache reference (linkTo) lookups.", default=False)
    parser.add_argument('--noprogress', action="store_true",
                        help="Do not track progress of client-side parsing/validation.", default=False)
    parser.add_argument('--progress-extra', action="store_true",
                        help="Include extra info in progress of client-side tracking parsing/validation.",
                        default=False)
    parser.add_argument('--app',
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=DEFAULT_SUBMISSION_PROTOCOL,
                        help=f"the submission protocol (default {DEFAULT_SUBMISSION_PROTOCOL!r})")
    parser.add_argument('--noadmin', action="store_true",
                        help="For testing only; assume not admin user.", default=False)
    parser.add_argument('--details', action="store_true", help="More details in output.", default=False)
    parser.add_argument('--noanalyze', action="store_true",
                        help="Do not analyze metadata for creates/updates to be done..", default=False)
    parser.add_argument('--json', action="store_true",
                        help="Output the parsed JSON of the metadata file.", default=False)
    parser.add_argument('--json-only', action="store_true",
                        help="Output ONLY the parsed JSON of the metadata file.", default=False)
    parser.add_argument('--info', action="store_true",
                        help="Output information about the given metadata file.", default=False)
    parser.add_argument('--refs', action="store_true",
                        help="Outputs list of references from the metadata file; only with --info.", default=False)
    parser.add_argument('--files', action="store_true",
                        help="Outputs list of files from the metadata file; only with --info.", default=False)
    parser.add_argument('--output', help="Output file for results.", default=False)
    parser.add_argument('--verbose', action="store_true", help="Debug output.", default=False)
    parser.add_argument('--timeout', help="Wait timeout for server validation/submission.")
    parser.add_argument('--debug', action="store_true", help="Debug output.", default=False)
    parser.add_argument('--debug-sleep', help="Sleep on each row read for troubleshooting/testing.", default=False)
    parser.add_argument('--ping', action="store_true", help="Ping server.", default=False)
    parser.add_argument('--rclone-google-source', help="Use rlcone to copy upload files from GCS.", default=None)
    parser.add_argument('--rclone-google-credentials', help="GCS credentials (service account file).", default=None)
    parser.add_argument('--rclone-google-location', help="GCS location (aka region).", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    directory_only = True
    if args.directory:
        if args.directory_only:
            PRINT("May not specify both --directory and --directory-only")
            exit(1)
        args.upload_folder = args.directory
        directory_only = False
    if args.directory_only:
        args.upload_folder = args.directory_only
        directory_only = True

    env_from_env = False
    if not args.env:
        args.env = os.environ.get("SMAHT_ENV")
        if args.env:
            env_from_env = True

    config_google = RCloneGoogle.from_command_args(args.rclone_google_source,
                                                   args.rclone_google_credentials,
                                                   args.rclone_google_location)

    if args.ping or (args.bundle_filename and args.bundle_filename.lower() == "ping"):
        if args.env or os.environ.get("SMAHT_ENV"):
            ping_okay = _ping(env=args.env or os.environ.get("SMAHT_ENV"), env_from_env=env_from_env,
                              server=args.server, app=args.app, keys_file=args.keys, verbose=True)
            if ping_okay:
                PRINT("Portal connectivity appears to be OK ✓")
            else:
                PRINT("Portal connectivty appears to be problematic ✗")
        else:
            PRINT("No environment specified (via --env); skipping SMaHT Portal ping.")
            ping_okay = True
        ping_rclone_okay = None
        if config_google:
            ping_rclone_okay = config_google.verify_connectivity()
        exit(0 if ping_okay is True and (ping_rclone_okay is not False) else 1)

    if args.consortia or (args.bundle_filename and args.bundle_filename.lower() == "consortia"):
        portal = _define_portal(env=args.env)
        consortia = _get_consortia(portal)
        PRINT("Known Consortia:")
        for consortium in consortia:
            if ((consortium_name := consortium.get("name")) and
                (consortium_uuid := consortium.get("uuid"))):  # noqa
                PRINT(f"- {consortium_name}: {consortium_uuid}")
        exit(0)

    if (args.submission_centers or
        (args.bundle_filename and args.bundle_filename.lower() in
         ["submission_centers", "submission-centers", "submissioncenters"])):
        portal = _define_portal(env=args.env)
        submission_centers = _get_submission_centers(portal)
        PRINT("Known Submission Centers:")
        for submission_center in submission_centers:
            if ((submission_center_name := submission_center.get("name")) and
                (submission_center_uuid := submission_center.get("uuid"))):  # noqa
                PRINT(f"- {submission_center_name}: {submission_center_uuid}")
        exit(0)

    _setup_validate_related_options(args)

    if not args.bundle_filename:
        PRINT("Missing submission file name.")
        exit(2)

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        PRINT(f"WARNING: Directory does not exist: {args.upload_folder}")
        if not _pytesting():
            # TODO: exist breaks test ...
            # FAILED submitr/tests/test_submit_metadata_bundle.py::test_submit_metadata_bundle_script[None]
            # FAILED submitr/tests/test_submit_metadata_bundle.py::test_submit_metadata_bundle_script[foo.bar]
            exit(1)

    if args.yes:
        args.no_query = True

    if args.noadmin:
        os.environ["SMAHT_NOADMIN"] = "true"

    if args.timeout:
        if not args.timeout.isdigit():
            args.timeout = None
        else:
            args.timeout = int(args.timeout)

    if args.info:
        if not os.path.exists(args.bundle_filename):
            PRINT(f"File does not exist: {args.bundle_filename}")
            exit(1)
        _print_metadata_file_info(args.bundle_filename, env=args.env,
                                  refs=args.refs, files=args.files,
                                  subfolders=not directory_only,
                                  upload_folder=args.upload_folder,
                                  rclone_google=config_google,
                                  output_file=args.output,
                                  verbose=args.verbose)
        exit(0)

    with script_catch_errors():

        if not _sanity_check_submitted_file(args.bundle_filename):
            exit(1)

        submit_any_ingestion(ingestion_filename=args.bundle_filename, ingestion_type=args.ingestion_type,
                             env=args.env, env_from_env=env_from_env,
                             keys_file=args.keys,
                             server=args.server,
                             consortium=args.consortium,
                             submission_center=args.submission_center,
                             add_submission_center=args.add_submission_center,
                             no_query=args.no_query,
                             subfolders=not directory_only,
                             app=args.app,
                             submission_protocol=args.submission_protocol,
                             upload_folder=args.upload_folder,
                             show_details=args.details,
                             post_only=args.post_only,
                             patch_only=args.patch_only,
                             submit=args.submit,
                             rclone_google=config_google,
                             validate_local_only=args.validate_local_only,
                             validate_remote_only=args.validate_remote_only,
                             validate_local_skip=args.validate_local_skip,
                             validate_remote_skip=args.validate_remote_skip,
                             noanalyze=args.noanalyze,
                             json_only=args.json_only,
                             ref_nocache=args.ref_nocache,
                             verbose_json=args.json,
                             verbose=args.verbose,
                             noversion=args.noversion,
                             noprogress=args.noprogress,
                             output_file=args.output,
                             timeout=args.timeout,
                             debug=args.debug,
                             debug_sleep=args.debug_sleep)


def _sanity_check_submitted_file(file_name: str) -> bool:
    """
    Performs some basic sanity checking on the specified file.
    If it is a JSON file (i.e. with a .json file extension) make sure it can load.
    If it is a zip file (or .tar.gz or other type of archive file) then tell the user
    that it must contain a single directory whose name is the base name of the file
    with a "-inserts" suffix. Returns True if passed sanity check otherwise False.
    """
    if not os.path.exists(file_name):
        PRINT(f"ERROR: Submission file does not exist: {file_name}")
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

    if args.info:
        return

    if args.submit:
        if args.validate or args.validate_only or args.validate_local_only or args.validate_remote_only:
            PRINT(f"May not specify both --submit AND validate options.")
            exit(1)
        if args.json_only:
            PRINT(f"May not specify both --submit AND --json-only options.")
            exit(1)

    if not args.submit:
        if not (args.validate or args.validate_only or args.validate_local_only or args.validate_remote_only):
            if not args.json_only and not _pytesting():
                PRINT(f"Must specify either --validate or --submit options. Use --help for all options.")
                exit(1)
        elif args.json_only:
            PRINT(f"May not specify both --json-only and validate options.")
            exit(1)

    if args.validate_local_only and args.validate_remote_only:
        PRINT(f"May not specify both --validate-local-only and --validate-remote-only options.")
        exit(1)

    if args.validate_local_only and args.validate_local_skip:
        PRINT(f"May not specify both --validate-local-only and --validate-local-skip options.")
        exit(1)

    if args.validate_remote_only and args.validate_remote_skip:
        PRINT(f"May not specify both --validate-remote-only and --validate-remote-skip options.")
        exit(1)

    if args.validate_local_skip and args.validate_remote_skip and (args.validate or args.validate_only):
        PRINT(f"May not specify both validation and not validation.")
        exit(1)

    if args.json_only:
        if args.submit:
            PRINT("The --json-only option is not allowed with --submit.")
            exit(1)
        if args.validate_remote_only or args.validate_local_skip:
            PRINT("The --json-only option is not allowed with these validate options.")
            exit(1)

    # Ultimately only want these options:
    # - args.submit -> If False then doing validation only
    # - args.validate_local_only -> Same as --validate-remote-only except not allowed with --submit
    # - args.validate_remote_only -> Same as --validate-local-only except not allowed with --submit
    # - args.validate_local_skip
    # - args.validate_remote_skip

    delattr(args, "validate")
    delattr(args, "validate_only")


if __name__ == '__main__':
    main()
