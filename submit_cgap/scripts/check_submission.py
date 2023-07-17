import argparse
from dcicutils.common import ORCHESTRATED_APPS
from dcicutils.env_utils import EnvUtils
from ..submission import check_submit_ingestion
from ..utils import script_catch_errors


EPILOG = __doc__


def default_app_for_check_submission():
    EnvUtils.init()
    return EnvUtils.app_name()


def main(simulated_args_for_testing=None):
    default_app = default_app_for_check_submission()

    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Check previously submitted submission.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('submission_uuid', help='uuid of previously submitted submission.')
    parser.add_argument('--app', choices=ORCHESTRATED_APPS, default=default_app,
                        help=f"An application (default {default_app!r}. Only for debugging."
                             f" Normally this should not be given.")
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():
        return check_submit_ingestion(
                args.submission_uuid,
                server=args.server,
                env=args.env,
                app=args.app
        )


if __name__ == '__main__':
    main()
