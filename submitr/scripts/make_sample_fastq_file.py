import argparse

from dcicutils.command_utils import script_catch_errors
from dcicutils.data_utils import generate_sample_fastq_file


EPILOG = __doc__


def main(simulated_args_for_testing=None):
    parser = argparse.ArgumentParser(  # noqa - PyCharm wrongly thinks the formatter_class is invalid
        description="Submits a data bundle",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('filename', help='a local Excel filename that is the data bundle')
    parser.add_argument('--number', '-n', help='number of sequences', default=10, type=int)
    parser.add_argument('--length', '-l', help='length of sequences', default=10, type=int)
    args = parser.parse_args(args=simulated_args_for_testing)

    with script_catch_errors():
        generate_sample_fastq_file(filename=args.filename, num=args.number, length=args.length)


if __name__ == '__main__':
    main()
