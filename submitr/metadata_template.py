import io
import requests
from contextlib import contextmanager
from functools import lru_cache
from itertools import islice
from typing import Optional, Tuple
from dcicutils.command_utils import yes_or_no
from dcicutils.data_readers import Excel
from dcicutils.misc_utils import get_error_message, PRINT
from dcicutils.portal_utils import Portal
from dcicutils.tmpfile_utils import temporary_file
from submitr.utils import is_excel_file_name, print_boxed, remove_punctuation_and_space


# This module provides functions to get the version of our (HMS DBMI) smaht-submitr metadata
# template file which resides in Google Sheets; as well as to export and download this template
# to a local Excel file; and to get the version from a given metadata Excel file. This version
# of which we speak is simply a convention we use of putting a string like "version: 1.2.3" in
# the first row of the second column of the (main Overview/Guidelines sheet of the) spreadsheet.
#
# The main use of all this is to tell the smaht-submitr submit-metadata-bundle command user
# whether or not the template they have based their metadata file on, if in fact they have based
# their metadata on our HMS template, is the latest version. A common model for many users being
# to manually export and download the HMS metadata template from Google Sheets, and modify it.
#
# Another use, just as a convenience, is to be able to download HMS metadata
# template to a local Excel file (see the get-metadata-template command).

# This URL is used for exporting/downloading the Google Sheets spreadsheet.
GOOGLE_SHEETS_EXPORT_BASE_URL = "https://spreadsheets.google.com/feeds/download/spreadsheets/Export?exportFormat=xlsx"


def check_metadata_version(file: str, portal: Portal,
                           quiet: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Higher level function, to be called from command(s), e.g. submit-metadata-bundle, to check
    metadata latest HMS DBMI smaht-submitr metadata template against the user's metadata file;
    printing a warning if out of date; with option to quit/exit if so.
    """
    if is_excel_file_name(file) and (version := _get_version_from_metadata_template_based_file(portal, file)):
        # Here it looks like the specified metadata Excel file is based on the HMS metadata template.
        metadata_template_url = get_metadata_template_url_from_portal(portal)
        metadata_template_version = get_metadata_template_version_from_portal(portal)
        if metadata_template_version:
            if version != metadata_template_version:
                if not quiet:
                    print_metadata_version_warning(
                        version, metadata_template_version, metadata_template_url)
                    if not yes_or_no("Do you want to continue with your metadata file?"):
                        exit(0)
            elif not quiet:
                PRINT(f"Your metadata file is based on the latest HMS metadata template:"
                      f" {metadata_template_version} ✓")
            return version, metadata_template_version
    return None, None


@lru_cache(maxsize=1)
def get_metadata_template_info_from_portal(portal: Portal) -> dict:
    try:
        if ((metadata_template_info := portal.get("/submitr-metadata-template/version")) and
            (metadata_template_info.status_code == 200) and
            (metadata_template_info := metadata_template_info.json())):  # noqa
            return metadata_template_info
    except Exception:
        pass
    return {}


def get_metadata_template_version_from_portal(portal: Portal) -> Optional[str]:
    return get_metadata_template_info_from_portal(portal).get("version")


def get_metadata_template_url_from_portal(portal: Portal) -> Optional[str]:
    return get_metadata_template_info_from_portal(portal).get("url")


def get_metadata_template_sheet_id_from_portal(portal: Portal) -> Optional[str]:
    return get_metadata_template_info_from_portal(portal).get("sheet_id")


def get_metadata_template_version_sheet_from_portal(portal: Portal) -> Optional[str]:
    return get_metadata_template_info_from_portal(portal).get("version_sheet")


def get_metadata_template_version_cell_from_portal(portal: Portal) -> Optional[str]:
    return get_metadata_template_info_from_portal(portal).get("version_cell")


def print_metadata_version_warning(this_metadata_template_version: str,
                                   metadata_template_version: str,
                                   metadata_template_url: Optional[str] = None) -> None:
    if this_metadata_template_version != metadata_template_version:
        print_boxed([
            f"===",
            f"WARNING: The version ({this_metadata_template_version}) of the HMS metadata template that your",
            f"metadata file is based on is out of date with the latest version.",
            f"You may want to update to the latest version: {metadata_template_version}",
            f"===",
            f"You can export/download the latest version from this URL:",
            metadata_template_url if metadata_template_url else None,
            f"===" if metadata_template_url else None,
            f"Or you can use export/download using the get-metadata-template command.",
            f"==="
        ])


def _get_version_from_metadata_template_based_file(portal: Portal, excel_file: str) -> Optional[str]:
    """
    Returns the version of the given metadata Excel spreadsheet specified by the given Excel
    file name, that is, if this spreadsheet looks like it is based on our HMS DBMI metadata
    template (in Google Sheets). If no file name is given then downloads the latest HMS DBMI
    metadata template from Google Sheets (to a temporary file) and gets/returns its version.
    If the spreadsheet does not look like it is based on the HMS DBMI metadata template,
    then returns None. Note that not finding a version is NOT considered an error,
    but not being able to load the spreadsheet IS considered an error.
    """
    def get_cell_value_from_excel(excel: Excel, sheet_name: str, cell: str) -> Optional[str]:  # noqa
        def get_sheet_row_column_from_cell(cell: str) -> Tuple[int, int]:  # noqa
            row_column_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if (len(cell) == 2) and ((c := row_column_names.find(cell[0])) >= 0) and cell[1].isdigit():
                return int(cell[1]) - 1, c
            return -1, -1
        def parse_metadata_template_version(value: str) -> Optional[str]:  # noqa
            # Parses and returns the version from a string like "version: 1.2.3".
            if value.strip().lower().startswith("version:"):
                return value.replace("version:", "").strip()
            return None
        def find_excel_sheet() -> Optional[str]:  # noqa
            nonlocal excel, sheet_name
            # Slash (and who know what else) is removed from tab name on download.
            normalized_sheet_name = remove_punctuation_and_space(sheet_name)
            for excel_sheet_name in excel.sheet_names:
                if remove_punctuation_and_space(excel_sheet_name) == normalized_sheet_name:
                    return excel_sheet_name
        try:
            if not (sheet_name := find_excel_sheet()):
                return None
            if sheet_reader := excel.sheet_reader(sheet_name):
                row_index, column_index = get_sheet_row_column_from_cell(cell)
                if (row_index == 0) and (header := sheet_reader.header):
                    if (column_index < len(header)) and (version := header[column_index]):
                        return parse_metadata_template_version(version)
                elif (row_index > 0) and (row := next(islice(sheet_reader, row_index - 1, None))):
                    if (row_column_values := list(row.values())) and (column_index < len(row_column_values)):
                        if version := row_column_values[column_index]:
                            return parse_metadata_template_version(version)
        except Exception:
            return None
    try:
        if not (excel := Excel(excel_file, include_hidden_sheets=True)):
            return None
    except Exception:
        return None
    metadata_template_version_sheet = get_metadata_template_version_sheet_from_portal(portal)
    metadata_template_version_cell = get_metadata_template_version_cell_from_portal(portal)
    return get_cell_value_from_excel(excel, metadata_template_version_sheet, metadata_template_version_cell)


def download_metadata_template(portal: Portal,
                               output_excel_file: Optional[str],
                               verbose: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Downloads (exports) the latest HMS DBMI smaht-submitr metadata template spreadsheet
    from Google Sheets to the given output Excel file name, and returns that given file
    name if successful. If it can not be downloaded, for whatever reason, then returns
    None. If the verbose option is given verbose argument is True then prints what is
    going on, e.g. for use by CLI. The given file must have a .xlsx suffix.
    """
    metadata_template_sheet_id = get_metadata_template_sheet_id_from_portal(portal)
    metadata_template_export_url = f"{GOOGLE_SHEETS_EXPORT_BASE_URL}&key={metadata_template_sheet_id}"
    if not (output_excel_file.endswith(".xlsx")):
        if verbose:
            PRINT("Output file name for metatdata template must have a .xlsx suffix.")
        return None, None
    if verbose:
        PRINT(f"Fetching metadata template from: {metadata_template_export_url}")
    try:
        if (response := requests.get(metadata_template_export_url)).status_code != 200:
            if verbose:
                PRINT(f"Cannot find metadata template: {metadata_template_export_url}")
            return None, None
    except Exception as e:
        if verbose:
            PRINT(f"Cannot fetch metadata template: {metadata_template_export_url}\n{get_error_message(e)}")
        return None, None
    if verbose:
        PRINT(f"Writing metadata template to: {output_excel_file}")
    try:
        with io.open(output_excel_file, "wb") as f:
            f.write(response.content)
    except Exception as e:
        if verbose:
            PRINT(f"Cannot save metadata template: {output_excel_file}\n{get_error_message(e)}")
        return None, None
    version = _get_version_from_metadata_template_based_file(portal, output_excel_file)
    if verbose:
        PRINT(f"Metadata template file: {output_excel_file}{f' | Version: {version}' if version else ''}")
    return output_excel_file, version


@contextmanager
def _download_metadata_template_to_tmpfile(portal: Portal) -> Optional[str]:
    """
    Same as download_metadata_template but downloads to a local temporary Excel file,
    as a context, so that the file is automatically deleted after usage (within the with).
    """
    with temporary_file(suffix=".xlsx") as filename:
        if download_metadata_template(portal, filename):
            yield filename
