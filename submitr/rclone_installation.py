import appdirs
from contextlib import contextmanager
import os
import platform
import requests
import shutil
import tempfile
from typing import Optional
import zipfile
from dcicutils.tmpfile_utils import temporary_file

RCLONE_DEFAULT_VERSION = "1.66.0"
RCLONE_COMMAND_NAME = "rclone"
RCLONE_DOWNLOAD_BASE_URL = "https://downloads.rclone.org"


def install_rclone_executable(version: Optional[str] = None, destination_file: Optional[str] = None,
                              raise_exception: bool = True) -> Optional[str]:
    """
    Downloads the rclone executable from the Web into the application specific directory for smaht-submitr.
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr  # noqa
    Returns a the path to the downloaded executable file. FYI see: https://rclone.org/downloads

    For example (on MacOS) we basically do the equivalent of something like this:
    - TMPDIR=/tmp/some-temporary-directory ; rm -rf $TMPDIR ; mkdir -p $TMPDIR
    - curl -o $TMPDIR/rclone-v1.66.0-osx-arm64.zip https://downloads.rclone.org/v1.66.0/rclone-v1.66.0-osx-arm64.zip
    - unzip $TMPDIR/rclone-v1.66.0-osx-arm64.zip rclone-v1.66.0-osx-arm64/rclone -d $TMPDIR
    - mkdir -p ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - mv $TMPDIR/rclone ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - chmod a+x ~/Library/Application Support/edu.harvard.hms/smaht-submitr/rclone
    - rm $TMPDIR/rclone-v1.66.0-osx-arm64.zip
    """
    try:
        rclone_version = version or RCLONE_DEFAULT_VERSION
        if not destination_file:
            destination_file = get_rclone_executable_path()
        rclone_version_name = f"v{rclone_version}"
        rclone_package_name = f"rclone-{rclone_version_name}-{_get_os_name()}-{_get_os_architecture_name()}"
        rclone_package_file_name = f"{rclone_package_name}.zip"
        rclone_download_url = f"{RCLONE_DOWNLOAD_BASE_URL}/{rclone_version_name}/{rclone_package_file_name}"
        with _download(rclone_download_url, suffix=".zip") as downloaded_rclone_package:
            _extract_from_zip(downloaded_rclone_package,
                              f"{rclone_package_name}/{RCLONE_COMMAND_NAME}",
                              destination_file, raise_exception=raise_exception)
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


@contextmanager
def _download(url: str, suffix: Optional[str] = None) -> Optional[str]:
    with temporary_file(suffix=suffix) as file:
        response = requests.get(url, stream=True)
        with open(file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        yield file


def _extract_from_zip(zip_file: str, file_to_extract: str, destination_file: str, raise_exception: bool = True) -> bool:
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


def _get_temporary_file_name(suffix: Optional[str] = None):
    tmpfile_descriptor, tmpfile_path = tempfile.mkstemp(suffix=suffix)
    os.close(tmpfile_descriptor)
    return tmpfile_path


def _get_app_specific_directory() -> str:
    """
    Returns the standard system application specific directory:
    - On MacOS this directory: is: ~/Library/Application Support
    - On Linux this directory is: ~/.local/share
    - On Windows this directory is: %USERPROFILE%\AppData\Local  # noqa
    N.B. This is has been tested on MacOS and Linux but not on Windows.
    """
    return appdirs.user_data_dir()


def _get_smaht_submitr_app_directory() -> str:
    """
    Returns the application specific directory for smaht-submitr:
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr  # noqa
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
