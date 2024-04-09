from submitr.metadata_template import download_hms_metadata_template
from submitr.scripts.cli_utils import CustomArgumentParser

_HELP = f"""
===
get-metadata-template
===
Tool to fetch the latest version of the HMS DBMI smaht-submitr metadata template.
===
USAGE: get-metadata-template OUTPUT-EXCEL-FILE OPTIONS
-----
OUTPUT-EXCEL-FILE: Saves the metadata template to this specified file.
===
OPTIONS:
===
--metadata METADATA-TEMPLATE-ID or METADATA-TEMPLATE-URL
  Uses the given metadata template ID or URL rather than the default.
--help
  Prints this documentation.
===
"""


def main():

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument("output_excel_file", help="Output Excel file.", default=None)
    parser.add_argument("--metadata", help="Metadata template ID or URL.")
    args = parser.parse_args(None)

    output_excel_file, version = download_hms_metadata_template(args.output_excel_file,
                                                                _metadata_template=args.metadata,
                                                                verbose=True)


if __name__ == "__main__":
    main()
