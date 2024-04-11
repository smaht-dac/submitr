from dcicutils.portal_utils import Portal
from submitr.metadata_template import (
    download_hms_metadata_template,
    get_hms_metadata_template_url_from_portal,
    get_hms_metadata_template_version_from_portal
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
--info
  Gets just the version number of the latest HMS DBMI metadata template.
--help
  Prints this documentation.
===
"""


def main():

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument("output_excel_file", nargs="?", help="Output Excel file.", default=None)
    parser.add_argument("--info", action="store_true",
                        help="Get just the version of the latest metadata template.", default=False)
    parser.add_argument('--env',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument("--metadata", help="Metadata template ID or URL (internal use only).")
    args = parser.parse_args(None)

    if args.info:
        portal = Portal(args.env)
        print(f"HMS Metadata Template URL: {get_hms_metadata_template_url_from_portal(portal)}")
        print(f"HMS Metadata Template Version: {get_hms_metadata_template_version_from_portal(portal)}")
    elif not args.output_excel_file:
        print("Must specify the name of an Excel file to write to.")
        exit(1)
    elif args.output_excel_file:
        output_excel_file, version = download_hms_metadata_template(args.output_excel_file,
                                                                    _metadata_template=args.metadata,
                                                                    verbose=True)


if __name__ == "__main__":
    main()
