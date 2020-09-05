import argparse
from ..submission import submit_metadata_bundle


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('bundle_filename', help='a local Excel filename that is the data bundle')
    parser.add_argument('--institution', '-i', help='institution identifier', default=None)
    parser.add_argument('--project', '-p', help='project identifier', default=None)
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    parser.add_argument('--validate-only', '-v', action="store_true",
                        help="whether to stop after validating without submitting", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    return submit_metadata_bundle(bundle_filename=args.bundle_filename, institution=args.institution,
                                  project=args.project, server=args.server, env=args.env,
                                  validate_only=args.validate_only)


if __name__ == '__main__':
    main()  # noQA - main is tested elsewhere
