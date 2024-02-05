import argparse
from dcicutils.command_utils import script_catch_errors
from dcicutils.common import ORCHESTRATED_APPS
from ..base import DEFAULT_APP
from ..submission import _check_submit_ingestion


EPILOG = __doc__


def main(simulated_args_for_testing=None):

    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Check previously submitted submission.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('submission_uuid', help='uuid of previously submitted submission.')
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=DEFAULT_APP,
                        help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--details', action="store_true", help="detailed output", default=False)
    parser.add_argument('--verbose', action="store_true", help="verbose output", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():
        return _check_submit_ingestion(
                args.submission_uuid,
                server=args.server,
                env=args.env,
                app=args.app,
                show_details=(args.verbose or args.details)
        )


if __name__ == '__main__':
    main()
