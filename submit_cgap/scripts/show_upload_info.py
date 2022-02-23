import argparse
from ..submission import show_upload_info
from ..base import UsingCGAPKeysFile
from ..utils import script_catch_errors


EPILOG = __doc__


@UsingCGAPKeysFile
def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle part",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('uuid', help='uuid identifier')
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a CGAP beanstalk environment name for the server to use", default=None)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        show_upload_info(uuid=args.uuid, server=args.server, env=args.env)


if __name__ == '__main__':
    main()
