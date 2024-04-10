from submitr.metadata_template import (
    download_hms_metadata_template,
    get_hms_metadata_template_version_from_google_sheets
)
from submitr.scripts.cli_utils import CustomArgumentParser

_HELP = f"""
===
get-metadata-template
===
Tool to export and download the latest version of the HMS DBMI
smaht-submitr metadata template spreadsheet as an Excel file.
===
USAGE: get-metadata-template OUTPUT-EXCEL-FILE OPTIONS
-----
OUTPUT-EXCEL-FILE: Saves the metadata template to this specified file.
===
OPTIONS:
===
--revision
  Gets just the version number of the latest HMS DBMI metadata template.
--help
  Prints this documentation.
===
"""


def main():

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument("output_excel_file", help="Output Excel file.", default=None)
    parser.add_argument("--revision", action="store_true",
                        help="Get just the version of the latest metadata template.", default=False)
    parser.add_argument("--metadata", help="Metadata template ID or URL (internal use only).")
    args = parser.parse_args(None)

    if args.revision:
        print(get_hms_metadata_template_version_from_google_sheets())
    else:
        output_excel_file, version = download_hms_metadata_template(args.output_excel_file,
                                                                    _metadata_template=args.metadata,
                                                                    verbose=True)


if __name__ == "__main__":
    main()
