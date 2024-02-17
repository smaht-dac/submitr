import os
from dcicutils.command_utils import script_catch_errors
from .cli_utils import CustomArgumentParser
from ..base import DEFAULT_APP
from ..submission import resume_uploads


_HELP = f"""
===
resume-uploads [VERSION]
===
Tool to submit (and validate) submission metadata and files to SMaHT Portal.
See: {CustomArgumentParser.HELP_URL}#resuming-uploads
===
USAGE: resume-uploads UUID OPTIONS
-----
UUID: This is UUID of your submission; or the UUID of an individual file
      referenced; or the accession ID of an individual file referenced.
===
OPTIONS:
===
--env ENVIRONMENT
  To specify your environment name; from your ~/.smaht-keys.json file.
--validate
  To validate metadata before submitting.
  This is the DEFAULT behavior for most (non-admin) users.
--bundle METADATA-FILE
  To specifiy the path to your metatdata file;
  only the directory of this is used to locate your upload files.
--directory DIRECTORY
  To specify the directory containing files to upload;
  in addition to the directory containing the submitted metadata file.
--sub-directories
  To specify that any sub-directories of the upload
  file(s) directory should be searched, recursively.
--keys KEYS-FILE
  To specify an alternate credentials/keys file to ~/.smaht-keys.json.
--help
  Print this documentation.
--help-advanced
  Print more advanced documentation.
--help-web
  Opens your browser to the Web based documentation.
  {CustomArgumentParser.HELP_URL}#resuming-uploads
===
"""


def main(simulated_args_for_testing=None):
    parser = CustomArgumentParser(_HELP, package="smaht-submitr")
    parser.add_argument('uuid', help='IngestionSumission UUID (or upload file UUID or accession ID).')
    parser.add_argument('--server', '-s',
                        help="HTTP(S) address of Portal server (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--env', '-e',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--app',
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--bundle', help="location of the original Excel submission file")
    parser.add_argument('--bundle_filename', '-b', help="Synonym for --bundle.")
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--directory', '-d', help="Directory of the upload files.")
    parser.add_argument('--upload_folder', '-u', help="Synonym for --directory.")
    parser.add_argument('--yes', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--no_query', '-nq', action="store_true",
                        help="Synonym for --yes.", default=False)
    parser.add_argument('--sub-directories', '-sd', action="store_true",
                        help="Search sub-directories of folder for upload files.", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="Synonym for --sub-directories.", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    if args.directory:
        args.upload_folder = args.directory
    if args.sub_directories:
        args.subfolders = True
    if args.bundle:
        args.bundle_filename = args.bundle

    if args.yes:
        args.no_query = True

    if args.keys:
        if not args.keys.endswith(".json") or not os.path.exists(args.keys):
            print("The --keys argument must be the name of an existing .json file.")
            exit(1)

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        print(f"WARNING: Directory does not exist: {args.upload_folder}")
        exit(1)

    if args.bundle_filename and not os.path.isdir(os.path.normpath(os.path.dirname(args.bundle_filename))):
        print(f"Specified bundle file not found: {args.bundle_filename}")
        exit(1)

    if not args.upload_folder and args.directory:
        args.upload_folder = args.directory

    if args.upload_folder and not os.path.isdir(args.upload_folder):
        print(f"Specified upload directory not found: {args.upload_folder}")
        exit(1)

    with script_catch_errors():

        resume_uploads(uuid=args.uuid, server=args.server, env=args.env, bundle_filename=args.bundle_filename,
                       upload_folder=args.upload_folder, no_query=args.no_query,
                       subfolders=args.subfolders, app=args.app, keys_file=args.keys)


if __name__ == '__main__':
    main()
