import appdirs
from typing import Optional
import os
import platform
import requests
import shutil
import tempfile
import zipfile

RCLONE_DEFAULT_VERSION = "1.66.0"
RCLONE_COMMAND_NAME = "rclone"
RCLONE_DOWNLOAD_BASE_URL = "https://downloads.rclone.org/"


def download_rclone_executable(version: Optional[str] = None, destination_file: Optional[str] = None,
                               raise_exception: bool = False) -> Optional[str]:
    """
    Downloads the rclone executable from the Web into the application specific directory for smaht-submitr.
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr  # noqa
    Returns a the path to the downloaded executatble file.
    """
    try:
        rclone_version = version or RCLONE_DEFAULT_VERSION
        if not destination_file:
            destination_file = get_rclone_executable_path()
        rclone_version_name = f"v{rclone_version}"
        rclone_package_name = f"rclone-{rclone_version_name}-{_get_os_name()}-{_get_os_architecture_name()}"
        rclone_package_file_name = f"{rclone_package_name}.zip"
        rclone_download_url = f"{RCLONE_DOWNLOAD_BASE_URL}/{rclone_version_name}/{rclone_package_file_name}"
        downloaded_rclone_package = _download_to_file(rclone_download_url)
        _extract_from_zip_file(downloaded_rclone_package, f"{rclone_package_name}/{RCLONE_COMMAND_NAME}",
                               destination_file)
        os.remove(downloaded_rclone_package)
        os.chmod(destination_file, 0o755)
        return destination_file
    except Exception as e:
        if raise_exception:
            raise e
    return None


def get_rclone_executable_path():
    return f"{_get_smaht_submitr_app_directory()}/{RCLONE_COMMAND_NAME}"


def rclone_executable_exists():
    return os.path.isfile(get_rclone_executable_path())


def _download_to_file(url: str, file: Optional[str] = None, raise_exception: bool = False) -> Optional[str]:
    try:
        if not file:
            file = _get_temporary_file_name()
        response = requests.get(url, stream=True)
        with open(file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return file
    except Exception as e:
        if raise_exception:
            raise e
    return None


def _extract_from_zip_file(zip_file: str, file_to_extract: str,
                           destination_file: str, raise_exception: bool = False) -> bool:
    try:
        if not (destination_directory := os.path.dirname(destination_file)):
            destination_directory = os.getcwd()
            destination_file = os.path.join(destination_directory, destination_file)
        with tempfile.TemporaryDirectory() as tmp_directory_name:
            with zipfile.ZipFile(zip_file, "r") as zipf:
                if file_to_extract not in zipf.namelist():
                    return False
                zipf.extract(file_to_extract, path=tmp_directory_name)
                os.makedirs(destination_directory, exist_ok=True)
                shutil.move(os.path.join(tmp_directory_name, file_to_extract), destination_file)
            return True
    except Exception as e:
        if raise_exception:
            raise e
    return False


def _get_temporary_file_name():
    tmpfile_descriptor, tmpfile_path = tempfile.mkstemp()
    os.close(tmpfile_descriptor)
    return tmpfile_path


def _get_app_specific_directory() -> str:
    """
    Returns the standard system application specific directory:
    - On MacOS this directory: is: ~/Library/Application Support
    - On Linux this directory is: ~/.local/share
    - On Windows this directory is: %USERPROFILE%\AppData\Local  # noqa
    """
    return appdirs.user_data_dir()


def _get_smaht_submitr_app_directory() -> str:
    """
    Returns the application specific directory for smaht-submitr:
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr  # noqa
    N.B. This is has been test on MacOS and Linux but not on Windows.
    """
    return os.path.join(_get_app_specific_directory(), "edu.harvard.hms", "smaht-submitr")


def _get_os_name() -> str:
    if os_name := platform.system():
        if os_name == "Darwin": return "osx"  # noqa
        elif os_name == "Linux": return "linux"  # noqa
        elif os_name == "Windows": return "windows"  # noqa
    return ""


def _get_os_architecture_name() -> str:
    if os_architecture_name := platform.machine():
        if os_architecture_name == "x86_64": return "amd64"  # noqa
        return os_architecture_name
    return ""
