import argparse
import json
import io
import os

from dcicutils.command_utils import script_catch_errors, ScriptFailure
from dcicutils.common import APP_FOURFRONT, ORCHESTRATED_APPS
from dcicutils.misc_utils import get_error_message
from ..submission import submit_any_ingestion, SubmissionProtocol, SUBMISSION_PROTOCOLS
from ..utils import show


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
    parser.add_argument('--consortium', '-c', default=None,
                        help='consortium identifier (comma-separated if several)')
    parser.add_argument('--submission-center', '-sc', default=None,
                        help='submission center intifier (comma-separated if several)')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--validate-only', '-v', action="store_true",
                        help="whether to stop after validating without submitting", default=False)
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=APP_FOURFRONT,
                        help=f"An application (default {APP_FOURFRONT!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--submission_protocol', '--submission-protocol', '-sp',
                        choices=SUBMISSION_PROTOCOLS, default=SubmissionProtocol.S3,
                        help=f"the submission protocol (default {SubmissionProtocol.S3!r})")
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        verify_ontology_file(args.ontology_filename)

        return submit_any_ingestion(
                ingestion_filename=args.ontology_filename,
                ingestion_type='ontology',
                lab=args.lab,
                award=args.award,
                consortium=args.consortium,
                submission_center=args.submission_center,
                server=args.server,
                env=args.env,
                validate_only=args.validate_only,
                app=args.app,
                submission_protocol=args.submission_protocol,
        )


def verify_ontology_file(ontology_filename: str) -> bool:
    if not os.path.exists(ontology_filename):
        raise ScriptFailure(f"Specified ontology file does not exist: {ontology_filename}")
    try:
        with io.open(ontology_filename, "r") as f:
            ontology_json = json.load(f)
            ontology_term_count = len(ontology_json["ontology_term"])
    except Exception as e:
        raise ScriptFailure(f"Cannot load specified ontology (JSON) file: {ontology_filename} | {get_error_message(e)}")
    show(f"Verified specified ontology (JSON) file: {ontology_filename} (ontology terms: {ontology_term_count})")
    return True


if __name__ == '__main__':
    main()
