import appdirs
from typing import Optional
import os
import platform
import requests
import shutil
import tempfile
import zipfile
from dcicutils.tmpfile_utils import temporary_directory, remove_temporary_directory

RCLONE_DEFAULT_VERSION = "1.66.0"
RCLONE_COMMAND_NAME = "rclone"


def download_rclone_executable(version: Optional[str] = None, destination_file: Optional[str] = None,
                               raise_exception: bool = False) -> Optional[str]:
    """
    Downloads the rclone executable from the Web into the standard application
    specific directory for smaht-submitr.
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr
    """
    try:
        rclone_version = version or RCLONE_DEFAULT_VERSION
        if not destination_file:
            destination_directory = _get_smaht_submitr_app_directory()
            destination_file = os.path.join(destination_directory, RCLONE_COMMAND_NAME)
        os_name = _get_os_name()
        os_architecture_name = _get_os_architecture_name()
        rclone_version_name = f"v{rclone_version}"
        rclone_package_name = f"rclone-{rclone_version_name}-{os_name}-{os_architecture_name}"
        rclone_package_file_name = f"{rclone_package_name}.zip"
        rclone_download_base_url = f"https://downloads.rclone.org/"
        rclone_download_url = f"{rclone_download_base_url}/{rclone_version_name}/{rclone_package_file_name}"
        downloaded_rclone_package_file_name = _download_url_to_file(rclone_download_url)
        _extract_from_zip_file(downloaded_rclone_package_file_name,
                               f"{rclone_package_name}/{RCLONE_COMMAND_NAME}",
                               destination_file, executable=True)
        remove_temporary_directory(downloaded_rclone_package_file_name)
        return destination_file
    except Exception as e:
        if raise_exception:
            raise e
    return None


def _download_url_to_file(url: str, file: Optional[str] = None, raise_exception: bool = False) -> Optional[str]:
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
                           destination_file: str, executable: bool = False,
                           raise_exception: bool = False) -> bool:
    try:
        if not (destination_directory := os.path.dirname(destination_file)):
            destination_directory = os.getcwd()
            destination_file = os.path.join(destination_directory, destination_file)
        with temporary_directory() as tmp_directory_name:
            with zipfile.ZipFile(zip_file, "r") as zipf:
                if file_to_extract not in zipf.namelist():
                    return False
                zipf.extract(file_to_extract, path=tmp_directory_name)
                os.makedirs(destination_directory, exist_ok=True)
                shutil.move(os.path.join(tmp_directory_name, file_to_extract), destination_file)
                if executable is True:
                    os.chmod(destination_file, 0o755)
            return True
    except Exception as e:
        if raise_exception:
            raise e
    return False


def _get_temporary_file_name():
    tmpfile_descriptor, tmpfile_path = tempfile.mkstemp()
    os.close(tmpfile_descriptor)
    return tmpfile_path


def _get_app_specific_data_directory() -> str:
    return appdirs.user_data_dir()


def _get_smaht_submitr_app_directory() -> str:
    return os.path.join(_get_app_specific_data_directory(), "edu.harvard.hms", "smaht-submitr")


def _get_os_name() -> str:
    if os_name := platform.system():
        if os_name == "Darwin": return "osx"  # noqa
        elif os_name == "Linux": return "linux"  # noqa
        elif os_name == "Windows": return "windows"  # noqa
    return "s"


def _get_os_architecture_name() -> str:
    return platform.machine() or ""


downloaded_rclone = download_rclone_executable()
print(downloaded_rclone)
