import argparse

from dcicutils.command_utils import script_catch_errors
from dcicutils.common import APP_SMAHT, ORCHESTRATED_APPS
from ..submission import _show_upload_info


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=APP_SMAHT,
                        help=f"An application (default {APP_SMAHT!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--details', '-d', action="store_true", help="retrieve and display detailed info", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        _show_upload_info(uuid=args.uuid, server=args.server, env=args.env, app=args.app, show_details=args.details)


if __name__ == '__main__':
    main()
