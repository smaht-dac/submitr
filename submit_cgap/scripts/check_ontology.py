import argparse
import json
import io
import os
from dcicutils.common import APP_FOURFRONT, ORCHESTRATED_APPS
from dcicutils.command_utils import ScriptFailure
from dcicutils.misc_utils import get_error_message
from ..submission import check_submit_ingestion, SubmissionProtocol, SUBMISSION_PROTOCOLS
from ..utils import script_catch_errors, show


EPILOG = __doc__


def main():
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Check previously submitted ontology",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('submission_uuid', help='uuid of previously submitted ontology')
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=APP_FOURFRONT,
                        help=f"An application (default {APP_FOURFRONT!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    args = parser.parse_args()

    with script_catch_errors():
        return check_submit_ingestion(
                args.submission_uuid,
                server=args.server,
                env=args.env,
                app=args.app
        )


if __name__ == '__main__':
    main()
