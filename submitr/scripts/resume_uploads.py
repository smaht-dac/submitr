import argparse
import os
from dcicutils.command_utils import script_catch_errors
from ..base import DEFAULT_APP
from ..submission import resume_uploads


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='IngestionSumission UUID (or upload file UUID or accession ID).')
    parser.add_argument('--server', '-s',
                        help="HTTP(S) address of Portal server (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--env', '-e',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--app',
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--bundle_filename', '-b', help="location of the original Excel submission file")
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--directory', '-d', help="Directory of the upload files.")
    parser.add_argument('--upload_folder', '-u', help="Synonym for --directory.")
    parser.add_argument('--no_query', '-nq', action="store_true",
                        help="Suppress (yes/no) requests for user input.", default=False)
    parser.add_argument('--subdirectories', '-sd', action="store_true",
                        help="Search sub-directories of folder for upload files.", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="Synonym for --subdirectories.", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    if args.directory:
        args.upload_folder = args.directory
    if args.subdirectories:
        args.subfolders = True

    if args.keys:
        if not args.keys.endswith(".json") or not os.path.exists(args.keys):
            print("The --keys argument must be the name of an existing .json file.")
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
