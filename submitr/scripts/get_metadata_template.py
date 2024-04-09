import requests
from typing import Optional
from dcicutils.data_readers import Excel
from submitr.metadata_template import download_metadata_template  # noqa TODO use this
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
--verbose
  For more verbose output.
--help
  Prints this documentation.
===
"""

GOOGLE_SHEETS_EXPORT_URL = "https://spreadsheets.google.com/feeds/download/spreadsheets/Export?exportFormat=xlsx"
METADATA_TEMPLATE_ID = "1sEXIA3JvCd35_PFHLj2BC-ZyImin4T-TtoruUe6dKT4"  # original
METADATA_TEMPLATE_ID = "1KeggqUjLvodYmmy52tYLYOP0g7Z3wey02zXbsP0elEY"  # my copy
METADATA_TEMPLATE_URL = f"{GOOGLE_SHEETS_EXPORT_URL}&key={METADATA_TEMPLATE_ID}"
METADATA_TEMPLATE_FILE = "/tmp/hms_dbmi_metadata_template.xlsx"
METADATA_TEMPLATE_MAIN_SHEET_NAME = "(OverviewGuidelines)"
METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX = 1

# https://spreadsheets.google.com/feeds/download/spreadsheets/Export?key=1sEXIA3JvCd35_PFHLj2BC-ZyImin4T-TtoruUe6dKT4&exportFormat=xlsx
# https://spreadsheets.google.com/feeds/download/spreadsheets/Export?key=1KeggqUjLvodYmmy52tYLYOP0g7Z3wey02zXbsP0elEY&exportFormat=xlsx


def main():

    parser = CustomArgumentParser(help=_HELP, help_url=CustomArgumentParser.HELP_URL)
    parser.add_argument("output_excel_file", help="Output Excel file.", default=None)
    parser.add_argument("--metadata", help="Metadata template ID or URL.")
    parser.add_argument("--verbose", action="store_true", help="More verbose output.")
    args = parser.parse_args(None)

    metadata_template_url = METADATA_TEMPLATE_URL
    if args.metadata:
        if args.metadata.lower().startswith("https://") or args.metadata.lower().startswith("http://"):
            metadata_template_url = args.metadata
        elif args.metadata:
            metadata_template_url = f"{GOOGLE_SHEETS_EXPORT_URL}&key={args.metadata}"

    if not (args.output_excel_file.endswith(".xlsx") or args.output_excel_file.endswith(".xls")):
        print("File name must have a .xlsx or .xls suffix.")
        exit(1)

    if args.verbose:
        print(f"Fetching metadata template from: {metadata_template_url}")

    response = requests.get(metadata_template_url)

    if args.verbose:
        print(f"Writing metadata template to: {args.output_excel_file}")

    with open(args.output_excel_file, "wb") as f:
        f.write(response.content)

    version = _get_metadata_template_version(args.output_excel_file)
    print(f"Metadata template file: {args.output_excel_file}{f' | Version: {version}' if version else ''}")


def _get_metadata_template_version(file: str) -> Optional[str]:
    excel = Excel(file, include_hidden_sheets=True)
    if METADATA_TEMPLATE_MAIN_SHEET_NAME in excel.sheet_names:
        if sheet_reader := excel.sheet_reader(METADATA_TEMPLATE_MAIN_SHEET_NAME):
            if header := sheet_reader.header:
                if METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX < len(header):
                    if version := header[METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX]:
                        if version.strip().lower().startswith("version:"):
                            return version.replace("version:", "").strip()
    return None


if __name__ == "__main__":
    main()
