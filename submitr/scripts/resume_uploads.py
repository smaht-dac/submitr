import argparse
import os
from dcicutils.command_utils import script_catch_errors
from ..submission import resume_uploads


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--bundle_filename', '-b', help="location of the original Excel submission file", default=None)
    parser.add_argument('--upload_folder', '-u', help="location of the upload files", default=None)
    parser.add_argument('--directory', '-d', help="location of the upload files", default=None)
    parser.add_argument('--no_query', '-nq', action="store_true",
                        help="suppress requests for user input", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="search subfolders of folder for upload files", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

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
                       upload_folder=args.upload_folder, no_query=args.no_query, subfolders=args.subfolders)


if __name__ == '__main__':
    main()
