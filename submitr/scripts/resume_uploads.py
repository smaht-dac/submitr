import os
from dcicutils.command_utils import script_catch_errors
from dcicutils.misc_utils import PRINT
from submitr.base import DEFAULT_APP
from submitr.rclone import RCloneGoogle
from submitr.submission import resume_uploads
from submitr.scripts.cli_utils import CustomArgumentParser


_HELP = f"""
===
resume-uploads [VERSION]
===
Tool to upload files referenced in a metadata file,
previously submitted using submit-metadata-bundle, to SMaHT Portal.
See: {CustomArgumentParser.HELP_URL}
===
USAGE: resume-uploads UUID OPTIONS
-----
UUID: This is UUID of your submission; or the UUID of an individual file
      referenced; or the accession ID of an individual file referenced.
===
OPTIONS:
===
--env ENVIRONMENT-NAME
  To specify your environment name; from your ~/.smaht-keys.json file.
--KEYS-FILE
  To specify an alternate credentials/keys
  file to the default ~/.smaht-keys.json file.
--validate
  To validate metadata before submitting.
  This is the DEFAULT behavior for most (non-admin) users.
--bundle METADATA-FILE
  To specifiy the path to your metatdata file;
  only the directory of this is used to locate your upload files.
--directory DIRECTORY
  To specify a directory containing the files to upload;
  this directory will be search, recursively.
--directory-only
  Same as --directory but does NOT search recursively.
--rclone-google-source GOOGLE-CLOUD-STORAGE-SOURCE
  A Google Cloud Storage (GCS) bucket or bucket/sub-folder
  from where the upload file(s) should be copied.
--rclone-google-credentials GCS-SERVICE-ACCOUNT-FILE
  GCS credentials to use for --rclone-google-source;
  e.g. full path to your GCP service account file.
  May be omitted if running on a GCE instance.
--rclone-google-location LOCATION
  The Google Cloud Storage (GCS) location (aka "region").
--help
  Prints this documentation.
--help-advanced
  Prints this plus more advanced documentation.
--help-web
  Opens your browser to the Web based documentation.
  {CustomArgumentParser.HELP_URL}
===
"""
_OBSOLETE_OPTIONS = [
    {"option": "-e", "message": "Use --env"},
    {"option": "-s", "message": "Use --server"},
    {"option": "-b", "message": "Use --bundle"},
    {"option": "--bundle_filename", "message": "Use --bundle"},
    {"option": "-u", "message": "Use --directory-only; or --directory which searches recusively."},
    {"option": "-d", "message": "Use --directory-only; or --directory which searches recusively."},
    {"option": "-nq", "message": "Use --no_query"},
    {"option": "-nq", "message": "Use --yes"},
    {"option": "--no_query", "message": "Use --yes"},
    {"option": "-sf", "message": "Use --directory which defaults to searching recusively."},
    {"option": "--subfolders", "message": "Use --directory which defaults to searching recusively."}
]


def main(simulated_args_for_testing=None):
    parser = CustomArgumentParser(help=_HELP, obsolete_options=_OBSOLETE_OPTIONS)
    parser.add_argument('uuid', nargs="?", help='IngestionSumission UUID (or upload file UUID or accession ID).')
    parser.add_argument('--server',
                        help="HTTP(S) address of Portal server (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--env',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--app',
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--bundle', help="location of the original Excel submission file")
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--directory', help="Directory of the upload files.")
    parser.add_argument('--directory-only', help="Same as --directory but NOT recursively.", default=False)
    parser.add_argument('--upload_folder', help="Synonym for --directory.")
    parser.add_argument('--rclone-google-source', help="Use rlcone to copy upload files from GCS.", default=None)
    parser.add_argument('--rclone-google-credentials', help="GCS credentials (service account file).", default=None)
    parser.add_argument('--rclone-google-location', help="GCS location (aka region).", default=None)
    parser.add_argument('--output', help="Output file for results.", default=False)
    parser.add_argument('--verbose', action="store_true", default=False)
    parser.add_argument('--yes', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    directory_only = True
    if args.directory:
        if args.directory_only:
            PRINT("May not specify both --directory and --directory-only")
            exit(1)
        args.upload_folder = args.directory
        args.upload_folder = args.directory
        directory_only = False
    if args.directory_only:
        args.upload_folder = args.directory_only
        directory_only = True

    if args.yes:
        args.no_query = True

    if not args.uuid:
        PRINT("Missing submission UUID or referenced file UUID or accession ID.")
        exit(2)

#   keys_file = args.keys or os.environ.get("SMAHT_KEYS")
#   if keys_file:
#       if not keys_file.endswith(".json") or not os.path.exists(keys_file):
#           PRINT(f"The --keys argument ({keys_file}) must be the name of an existing .json file.")
#           exit(1)

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        PRINT(f"Directory does not exist: {args.upload_folder}")
        exit(1)

    if args.bundle and not os.path.isdir(os.path.normpath(os.path.dirname(args.bundle))):
        PRINT(f"Specified bundle file not found: {args.bundle}")
        exit(1)

    if not args.upload_folder and args.directory:
        args.upload_folder = args.directory

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        PRINT(f"Specified upload directory not found: {args.upload_folder}")
        exit(1)

    config_google = RCloneGoogle.from_command_args(args.rclone_google_source,
                                                   args.rclone_google_credentials,
                                                   args.rclone_google_location)

    env_from_env = False
    if not args.env:
        args.env = os.environ.get("SMAHT_ENV")
        if args.env:
            env_from_env = True

    with script_catch_errors():

        resume_uploads(uuid=args.uuid,
                       env=args.env,
                       env_from_env=env_from_env,
                       keys_file=args.keys,
                       bundle_filename=args.bundle,
                       server=args.server,
                       upload_folder=args.upload_folder,
                       no_query=args.yes,
                       subfolders=not directory_only,
                       rclone_google=config_google,
                       output_file=args.output,
                       app=args.app,
                       verbose=args.verbose)


if __name__ == '__main__':
    main()
