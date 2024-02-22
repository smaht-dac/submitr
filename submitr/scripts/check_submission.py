import argparse
import os
from dcicutils.command_utils import script_catch_errors
from dcicutils.common import ORCHESTRATED_APPS
from ..base import DEFAULT_APP
from ..submission import _check_submit_ingestion, _pytesting


EPILOG = __doc__


def main(simulated_args_for_testing=None):

    args = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Check previously submitted submission.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    args.add_argument('submission_uuid', nargs="?", help='UUID of previously submitted submission.')
    args.add_argument('--app', choices=ORCHESTRATED_APPS, default=DEFAULT_APP,
                      help=f"An application (default {DEFAULT_APP!r}. Only for debugging."
                           f" Normally this should not be given.")
    args.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    args.add_argument("--env", "-e",
                      help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    args.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    args.add_argument('--details', action="store_true", help="More detailed output.", default=False)
    args.add_argument('--verbose', action="store_true", help="More verbose output.", default=False)
    args = args.parse_args(args=simulated_args_for_testing)

    if not args.submission_uuid:
        if _pytesting():
            exit(2)
        args.submission_uuid = "dummy"

    with script_catch_errors():
        return _check_submit_ingestion(
                args.submission_uuid,
                env=args.env or os.environ.get("SMAHT_ENV"),
                keys_file=args.keys or os.environ.get("SMAHT_KEYS"),
                server=args.server,
                show_details=(args.verbose or args.details)
        )


if __name__ == '__main__':
    main()
