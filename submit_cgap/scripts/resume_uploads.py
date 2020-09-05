import argparse
from ..submission import resume_uploads


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier', default=None)
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    parser.add_argument('--bundle_filename', '-b', help="location of the original Excel submission file", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    resume_uploads(uuid=args.uuid, server=args.server, env=args.env, bundle_filename=args.bundle_filename)


if __name__ == '__main__':  # noqa - main is tested elsewhere
    main()
