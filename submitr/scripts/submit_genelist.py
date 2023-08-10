import argparse

from dcicutils.command_utils import script_catch_errors
from ..submission import submit_any_ingestion


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a gene list",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('genelist_filename', help='a local Excel or txt filename that is the gene list')
    parser.add_argument('--institution', '-i', help='institution identifier', default=None)
    parser.add_argument('--project', '-p', help='project identifier', default=None)
    parser.add_argument('--server', '-s', help="an http or https address of the server to use", default=None)
    parser.add_argument('--env', '-e', help="a portal environment name for the server to use", default=None)
    parser.add_argument('--validate-only', '-v', action="store_true",
                        help="whether to stop after validating without submitting", default=False)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        return submit_any_ingestion(
                ingestion_filename=args.genelist_filename,
                ingestion_type='genelist',
                institution=args.institution,
                project=args.project,
                server=args.server,
                env=args.env,
                validate_only=args.validate_only,
        )


if __name__ == '__main__':
    main()
