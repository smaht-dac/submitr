import argparse
from dcicutils.common import APP_FOURFRONT, ORCHESTRATED_APPS
from ..submission import show_upload_info
from ..utils import script_catch_errors


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=APP_FOURFRONT,
                        help=f"An application (default {APP_FOURFRONT!r}. Only for debugging."
                             f" Normally this should not be given.")
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        show_upload_info(uuid=args.uuid, server=args.server, env=args.env, app=args.app)


if __name__ == '__main__':
    main()
