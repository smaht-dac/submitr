import argparse
import json
import io
import os
from dcicutils.common import APP_FOURFRONT, ORCHESTRATED_APPS
from ..submission import submit_any_ingestion, SubmissionProtocol, SUBMISSION_PROTOCOLS
from ..utils import script_catch_errors, show


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits an ontology",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('ontology_filename', help='a file of ontology data')
    parser.add_argument('--lab', '-l', '-L', help='lab identifier', default=None)
    parser.add_argument('--award', '-a', help='award identifier', default=None)
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    parser.add_argument('--validate-only', '-v', action="store_true",
                        help="whether to stop after validating without submitting", default=False)
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=APP_FOURFRONT,
                        help=f"An application (default {APP_FOURFRONT!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=SubmissionProtocol.S3,
                        help=f"the submission protocol (default {SubmissionProtocol.S3!r})")
    parser.add_argument('--verbose', default=False, action='store_true', help='Include verbose output.')
    parser.add_argument('--debug', default=False, action='store_true', help='Include debug output.')


    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        if not verify_ontology_file(args.ontology_filename):
            return

        return submit_any_ingestion(
                ingestion_filename=args.ontology_filename,
                ingestion_type='ontology',
                lab=args.lab,
                award=args.award,
                server=args.server,
                env=args.env,
                validate_only=args.validate_only,
                app=args.app,
                submission_protocol=args.submission_protocol,
                verbose=args.verbose, debug=args.debug)


def verify_ontology_file(ontology_filename: str) -> bool:
    if not os.path.exists(ontology_filename):
        show(f"ERROR: Cannot find specified ontology (JSON) file: {ontology_filename}")
        return False
    try:
        with io.open(ontology_filename, "r") as f:
            ontology_json = json.load(f)
            ontology_term_count = len(ontology_json["terms"])
    except Exception:
        show(f"ERROR: Cannot load specified ontology (JSON) file: {ontology_filename}")
        return False
    show(f"Verified specified ontology (JSON) file: {ontology_filename} (ontology terms: {ontology_term_count})")
    return True


if __name__ == '__main__':
    main()
