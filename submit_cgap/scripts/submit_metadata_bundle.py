import argparse
from dcicutils.common import APP_CGAP
from ..submission import (
    submit_any_ingestion, DEFAULT_INGESTION_TYPE, DEFAULT_SUBMISSION_PROTOCOL, SUBMISSION_PROTOCOLS
)
from ..utils import script_catch_errors


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
    parser.add_argument('--upload_folder', '-u', help="location of the upload files", default=None)
    parser.add_argument('--ingestion_type', '--ingestion-type', '-t', help="the ingestion type",
                        default=DEFAULT_INGESTION_TYPE)
    parser.add_argument('--no_query', '--no-query', '-nq', action="store_true",
                        help="suppress requests for user input", default=False)
    parser.add_argument('--subfolders', '-sf', action="store_true",
                        help="search subfolders of folder for upload files", default=False)
    parser.add_argument('--app', default=APP_CGAP,
                        help=f"An application (default {APP_CGAP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=DEFAULT_SUBMISSION_PROTOCOL,
                        help=f"the submission protocol (default {DEFAULT_SUBMISSION_PROTOCOL!r})")
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        submit_any_ingestion(ingestion_filename=args.bundle_filename, ingestion_type=args.ingestion_type,
                             institution=args.institution, project=args.project,
                             server=args.server, env=args.env,
                             validate_only=args.validate_only, upload_folder=args.upload_folder,
                             no_query=args.no_query, subfolders=args.subfolders, app=args.app,
                             submission_protocol=args.submission_protocol)


if __name__ == '__main__':
    main()
