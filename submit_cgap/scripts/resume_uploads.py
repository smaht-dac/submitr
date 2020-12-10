import argparse
from ..submission import resume_uploads
from ..base import UsingCGAPKeysFile


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
    args = parser.parse_args(args=simulated_args_for_testing)

    resume_uploads(uuid=args.uuid, server=args.server, env=args.env, bundle_filename=args.bundle_filename,
                   upload_folder=args.upload_folder)


if __name__ == '__main__':
    main()
