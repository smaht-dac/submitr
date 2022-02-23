import argparse
from ..submission import resume_uploads
from ..base import UsingCGAPKeysFile
from ..utils import script_catch_errors


EPILOG = __doc__


@UsingCGAPKeysFile
def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    parser.add_argument('--bundle_filename', '-b', help="location of the original Excel submission file", default=None)
    parser.add_argument('--upload_folder', '-u', help="location of the upload files", default=None)
    parser.add_argument('--no_query', '-nq', action="store_true",
                        help="suppress requests for user input", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="search subfolders of folder for upload files", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        resume_uploads(uuid=args.uuid, server=args.server, env=args.env, bundle_filename=args.bundle_filename,
                       upload_folder=args.upload_folder, no_query=args.no_query, subfolders=args.subfolders)


if __name__ == '__main__':
    main()
