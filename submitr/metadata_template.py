import io
import requests
from contextlib import contextmanager
from functools import lru_cache
from typing import Callable, Optional, Tuple
from dcicutils.command_utils import yes_or_no
from dcicutils.data_readers import Excel
from dcicutils.misc_utils import get_error_message, PRINT
from dcicutils.portal_utils import Portal
from dcicutils.tmpfile_utils import temporary_file
from submitr.utils import is_excel_file_name, print_boxed


# This module provides functions to get the version of our (HMS DBMI) smaht-submitr
# metadata template file which resides in Google Sheets; as well as to export and
# download this template to a local Excel file; and to get the version from a
# given metadata Excel file. This version of which we speak is simply a convention
# we use of putting a string like "version: 1.2.3" in the first row of the second
# column of the (main Overview/Guidelines sheet of the) spreadsheet.
#
# The main use of all this is to tell the smaht-submitr submit-metadata-bundle
# command user whether or not the template they have based their metadata file
# on (if in fact it they have based their metadata on our HMS template) is the
# latest version. A common model for many users being to manually export and
# download the HMS metadata template from Google Sheets, and modify if it.
#
# Another use, just as a convenience, is to be able to download HMS metadata
# template to a local Excel file (see the get-metadata-template command).

# This is the Google Sheets ID for our HMS metadata template spreadsheet.
HMS_METADATA_TEMPLATE_ID = "1sEXIA3JvCd35_PFHLj2BC-ZyImin4T-TtoruUe6dKT4"
HMS_METADATA_TEMPLATE_URL = f"https://docs.google.com/spreadsheets/d/{HMS_METADATA_TEMPLATE_ID}"

# This URL is used for exporting and downloading the Google Sheets spreadsheet.
# as opposed the the Google API key which is used to access the Google Sheets
# spreadsheet directly for the Google Sheets API in order to get the spreadsheet version.
GOOGLE_SHEETS_EXPORT_URL = "https://spreadsheets.google.com/feeds/download/spreadsheets/Export?exportFormat=xlsx"
HMS_METADATA_TEMPLATE_EXPORT_URL = f"{GOOGLE_SHEETS_EXPORT_URL}&key={HMS_METADATA_TEMPLATE_ID}"

# This is the name of the main tab/sheet in our HMS metadata template;
# this contains the version info (see below).
HMS_METADATA_TEMPLATE_MAIN_SHEET_NAME = "(Overview/Guidelines)"

# These define the location of the version info within our HMS metadata template.
# By convention we put this in a string like "version: 1.2.3." in the first row
# of the second column of the (main Overview/Guidelines sheet of the) spreadsheet;
# this is what is normally considered the "header" row. For an exported/downloaded
# Excel version of the spreadsheet we need the header index column; for reading
# the version directly from Google Sheets using the Google Sheets API we need
# the cell identifer or "range" which is B1:B1.
HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX = 1
HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_CELL = "B1:B1"
HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_LOCATION = (f"{HMS_METADATA_TEMPLATE_MAIN_SHEET_NAME}!"
                                                     f"{HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_CELL}")


def download_hms_metadata_template(output_excel_file: Optional[str],
                                   raise_exception: bool = False,
                                   verbose: bool = False,
                                   printf: Optional[Callable] = None,
                                   _metadata_template: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Downloads (exports) the latest HMS DBMI smaht-submitr metadata template spreadsheet
    from Google Sheets to the given output Excel file name, and returns that given file
    name if successful. If it can not be downloaded, for whatever reason, then returns
    None (or raises an exception if the raise_exception arg is True). If the verbose
    option is given verbose argument is True then prints what is going on, e.g. for
    use by CLI; uses the given print function (printf) to do this or just the print
    builtin if None is specified. The given file must have a .xlsx suffix.

    The Google Sheets ID of our HMS DBMI metadata template in defined by
    the HMS_METADATA_TEMPLATE_ID constant (defined above); and its export
    URL is defined by the HMS_METADATA_TEMPLATE_EXPORT_URL constant (defined above).
    """
    printf = printf if callable(printf) else PRINT
    if not _metadata_template:
        hms_metadata_template_export_url = HMS_METADATA_TEMPLATE_EXPORT_URL
    elif _metadata_template.lower().startswith("https://") or _metadata_template.lower().startswith("http://"):
        hms_metadata_template_export_url = _metadata_template
    else:
        hms_metadata_template_export_url = f"{GOOGLE_SHEETS_EXPORT_URL}&key={_metadata_template}"
    if not (output_excel_file.endswith(".xlsx") or output_excel_file.endswith(".xls")):
        message = "Output file name for metatdata template must have a .xlsx or .xls suffix."
        if raise_exception:
            raise Exception(message)
        if verbose:
            printf(message)
        return (None, None)
    if verbose:
        printf(f"Fetching metadata template from: {hms_metadata_template_export_url}")
    try:
        if (response := requests.get(hms_metadata_template_export_url)).status_code != 200:
            message = f"Cannot find metadata template: {hms_metadata_template_export_url}"
            if raise_exception:
                raise Exception(message)
            if verbose:
                printf(message)
            return (None, None)
    except Exception as e:
        message = f"Cannot fetch metadata template: {hms_metadata_template_export_url}\n{get_error_message(e)}"
        if raise_exception:
            raise Exception(message)
        if verbose:
            printf(message)
        return (None, None)
    if verbose:
        printf(f"Writing metadata template to: {output_excel_file}")
    try:
        with io.open(output_excel_file, "wb") as f:
            f.write(response.content)
    except Exception as e:
        message = f"Cannot save metadata template: {output_excel_file}\n{get_error_message(e)}"
        if raise_exception:
            raise Exception(message)
        if verbose:
            printf(message)
        return (None, None)
    version = get_version_from_hms_metadata_template_based_file(output_excel_file)
    if verbose:
        printf(f"Metadata template file: {output_excel_file}{f' | Version: {version}' if version else ''}")
    return output_excel_file, version


def get_version_from_hms_metadata_template_based_file(excel_file: Optional[str] = None,
                                                      raise_exception: bool = False) -> Optional[str]:
    """
    Returns the version of the given metadata Excel spreadsheet specified by the given Excel
    file name, that is, if this spreadsheet looks like it is based on our HMS DBMI metadata
    template (in Google Sheets). If no file name is given then downloads the latest HMS DBMI
    metadata template from Google Sheets (to a temporary file) and gets/returns its version.
    If the spreadsheet does not look like it is based on the HMS DBMI metadata template,
    then returns None. If the raise_exception arg is True then raises an exception on error;
    but note that not finding a version is NOT considered an error, but not being able to
    load the spreadsheet IS considered an error.
    """
    if not excel_file:
        with _download_hms_metadata_template_to_tmpfile() as excel_file:
            return get_version_from_hms_metadata_template_based_file(excel_file) if excel_file else None
    try:
        excel = Excel(excel_file, include_hidden_sheets=True)
    except Exception as e:
        if raise_exception:
            raise Exception(f"Cannot load Excel file: {excel_file}\n{get_error_message(e)}")
        return None
    hms_metadata_template_main_sheet_name = HMS_METADATA_TEMPLATE_MAIN_SHEET_NAME.replace("/", "")
    if excel and (hms_metadata_template_main_sheet_name in excel.sheet_names):
        # Slash (and who know what else) is removed from tab name on download.
        if sheet_reader := excel.sheet_reader(hms_metadata_template_main_sheet_name):
            if header := sheet_reader.header:
                if HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX < len(header):
                    if version := header[HMS_METADATA_TEMPLATE_MAIN_SHEET_VERSION_HEADER_COLUMN_INDEX]:
                        return _parse_hms_metadata_template_version(version)
    return None


@lru_cache(maxsize=1)
def get_hms_metadata_template_info_from_portal(portal: Portal,
                                               raise_exception: bool = False) -> Tuple[Optional[str], Optional[str]]:
    try:
        if ((metadata_template_info := portal.get("/submitr-metadata-template/version")) and
            (metadata_template_info.status_code == 200) and
            (metadata_template_info := metadata_template_info.json())):  # noqa
            return metadata_template_info.get("url"), metadata_template_info.get("version")
    except Exception as e:
        if raise_exception:
            raise Exception(f"Cannot get HMS metadata template info from portal.\n{get_error_message(e)}")
        pass
    return None, None


def get_hms_metadata_template_version_from_portal(portal: Portal,
                                                  raise_exception: bool = False) -> Optional[str]:
    _, metadata_template_version = get_hms_metadata_template_info_from_portal(portal, raise_exception=raise_exception)
    return metadata_template_version


def get_hms_metadata_template_url_from_portal(portal: Portal, raise_exception: bool = False) -> Optional[str]:
    metadata_template_url, _ = get_hms_metadata_template_info_from_portal(portal, raise_exception=raise_exception)
    return metadata_template_url


def check_metadata_version(file: str, portal: Portal,
                           printf: Optional[Callable] = None,
                           quiet: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Higher level function, to be called from command(s), e.g. submit-metadata-bundle, to check
    metadata latest HMS DBMI smaht-submitr metadata template against the user's metadata file;
    printing a warning if out of date; with option to quit/exit if so.
    """
    printf = printf if callable(printf) else PRINT
    if is_excel_file_name(file) and (version := get_version_from_hms_metadata_template_based_file(file)):
        # Here it looks like the specified metadata Excel file is based on the HMS metadata template.
        # if hms_metadata_template_version := get_hms_metadata_template_version_from_google_sheets():
        hms_metadata_template_url, hms_metadata_template_version = get_hms_metadata_template_info_from_portal(portal)
        if hms_metadata_template_version:
            if version != hms_metadata_template_version:
                if not quiet:
                    print_metadata_version_warning(version,
                                                   hms_metadata_template_version,
                                                   hms_metadata_template_url, printf=printf)
                    if not yes_or_no("Do you want to continue with your metadata file?"):
                        exit(0)
            elif not quiet:
                PRINT(f"Your metadata file is based on the latest HMS metadata template:"
                      f" {hms_metadata_template_version} ✓")
            return version, hms_metadata_template_version
    return None, None


def print_metadata_version_warning(this_metadata_template_version: str,
                                   hms_metadata_template_version: str,
                                   hms_metadata_template_url: str,
                                   printf: Optional[Callable] = None) -> None:
    printf = printf if callable(printf) else PRINT
    if this_metadata_template_version != hms_metadata_template_version:
        print_boxed([
            f"===",
            f"WARNING: The version ({this_metadata_template_version}) of the HMS metadata template that your",
            f"metadata file is based on is out of date with the latest version.",
            f"You may want to update to the latest version: {hms_metadata_template_version}",
            f"===",
            f"You can export/download the latest version from this URL:",
            hms_metadata_template_url,
            f"===",
            f"Or you can use export/download using the get-metadata-template command.",
            f"==="
        ])


@contextmanager
def _download_hms_metadata_template_to_tmpfile(raise_exception: bool = False) -> Optional[str]:
    """
    Same as download_hms_metadata_template but downloads to a local temporary Excel file,
    as a context, so that the file is automatically deleted after usage (within the with).
    """
    with temporary_file(suffix=".xlsx") as filename:
        if download_hms_metadata_template(filename):
            yield filename


def _parse_hms_metadata_template_version(value: str) -> Optional[str]:
    """
    Parses and returns the version from a string like "version: 1.2.3".
    """
    if value.strip().lower().startswith("version:"):
        return value.replace("version:", "").strip()
    return None
