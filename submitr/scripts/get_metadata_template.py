from submitr.metadata_template import (
    download_metadata_template,
    get_metadata_template_url_from_portal,
    get_metadata_template_version_from_portal
)
from submitr.scripts.cli_utils import CustomArgumentParser
from submitr.submission import _define_portal

_HELP = f"""
===
get-metadata-template
===
Tool to export and download the latest version of the HMS DBMI
smaht-submitr metadata template spreadsheet as an Excel file.
===
USAGE: get-metadata-template OUTPUT-EXCEL-FILE OPTIONS
       get-metadata-template --list OPTIONS
-----
OUTPUT-EXCEL-FILE: Saves the metadata template to this specified file.
===
OPTIONS:
===
--info
  Gets just the version number of the latest HMS DBMI metadata template.
--env ENVIRONMENT-NAME
  To specify your environment name; from your ~/.smaht-keys.json file.
  Alternatively, set your SMAHT_ENV environment variable.
--keys KEYS-FILE
  To specify an alternate credentials/keys file,
  rather than the default ~/.smaht-keys.json file.
  Alternatively, set your SMAHT_KEYS environment variable.
--help
  Prints this documentation.
===
"""


def main() -> None:

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument("output_excel_file", nargs="?", help="Output Excel file.", default=None)
    parser.add_argument("--info", action="store_true",
                        help="Get just the version of the latest metadata template.", default=False)
    parser.add_argument('--env',
                        help="Portal environment name for server/credentials (e.g. in ~/.smaht-keys.json).")
    parser.add_argument('--keys', help="Path to keys file (rather than default ~/.smaht-keys.json).", default=None)
    parser.add_argument('--verbose', action="store_true", help="Verbose output.", default=False)
    args = parser.parse_args(None)

    def define_portal() -> None:
        nonlocal args
        portal = _define_portal(env=args.env, keys_file=args.keys,
                                report=args.verbose, ping=True, note="Metadata Template")
        return portal

    def print_metadata_template_info() -> None:
        portal = define_portal()
        print(f"HMS Metadata Template URL: {get_metadata_template_url_from_portal(portal)}")
        print(f"HMS Metadata Template Version: {get_metadata_template_version_from_portal(portal)}")

    if args.info:
        if not args.output_excel_file:
            print_metadata_template_info()
        else:
            parser.print_help()
    elif args.output_excel_file and (args.output_excel_file.strip().lower() == "info"):
        print_metadata_template_info()
    elif args.output_excel_file:
        download_metadata_template(define_portal(), args.output_excel_file, verbose=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
