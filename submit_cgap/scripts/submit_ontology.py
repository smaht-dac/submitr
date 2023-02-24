import argparse
from ..submission import submit_any_ingestion
from ..utils import script_catch_errors


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a gene list",
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
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():

        return submit_any_ingestion(
                ingestion_filename=args.ontology_filename,
                ingestion_type='ontology',
                lab=args.lab,
                award=args.award,
                server=args.server,
                env=args.env,
                validate_only=args.validate_only,
                app='fourfront'
        )


if __name__ == '__main__':
    main()
