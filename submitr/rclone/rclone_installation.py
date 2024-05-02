import os
from typing import Optional
from dcicutils.http_utils import download
from dcicutils.misc_utils import get_app_specific_directory, get_cpu_architecture_name, get_os_name
from dcicutils.progress_bar import ProgressBar
from dcicutils.zip_utils import extract_file_from_zip

RCLONE_VERSION = "1.66.0"
RCLONE_COMMAND_NAME = "rclone"
RCLONE_DOWNLOAD_BASE_URL = "https://downloads.rclone.org"


def rclone_executable_install(version: Optional[str] = None, destination_file: Optional[str] = None,
                              progress: bool = False, raise_exception: bool = True) -> Optional[str]:
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
    - rm $TMPDIR/rclone-v1.66.0-osx-arm64.zip
    - mkdir -p ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - mv $TMPDIR/rclone ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - chmod a+x ~/Library/Application Support/edu.harvard.hms/smaht-submitr/rclone
    """
    progress_bar = ProgressBar(description=f"Installing rclone ({RCLONE_VERSION})",
                               use_byte_size_for_rate=True) if progress else None
    def progress_callback(nbytes: int, nbytes_total: Optional[int] = None) -> bool:  # noqa
        nonlocal progress_bar
        if not progress_bar.total and nbytes_total is not None:
            progress_bar.set_total(nbytes_total)
        progress_bar.set_progress(nbytes)
    try:
        rclone_version = version or RCLONE_VERSION
        if not destination_file:
            destination_file = rclone_executable_path()
        rclone_package_name = f"rclone-v{rclone_version}-{get_os_name()}-{get_cpu_architecture_name()}"
        rclone_download_url = f"{RCLONE_DOWNLOAD_BASE_URL}/v{rclone_version}/{rclone_package_name}.zip"
        with download(rclone_download_url, suffix=".zip", progress=progress_callback) as downloaded_rclone_package:
            extract_file_from_zip(downloaded_rclone_package,
                                  f"{rclone_package_name}/{RCLONE_COMMAND_NAME}",
                                  destination_file, raise_exception=raise_exception)
            os.chmod(destination_file, 0o755)
        if progress_bar:
            progress_bar.done(f"Installed rclone ({RCLONE_VERSION})")
        return destination_file
    except Exception as e:
        if raise_exception:
            raise e
    return None


def rclone_executable_path():
    return f"{_get_smaht_submitr_app_directory()}/{RCLONE_COMMAND_NAME}"


def rclone_executable_exists():
    return os.path.isfile(rclone_executable_path())


def _get_smaht_submitr_app_directory() -> str:
    """
    Returns the application specific directory for smaht-submitr:
    - On MacOS this directory: is: ~/Library/Application Support/edu.harvard.hms/smaht-submitr
    - On Linux this directory is: ~/.local/share/edu.harvard.hms/smaht-submitr
    - On Windows this directory is: %USERPROFILE%\AppData\Local\edu.harvard.hms\smaht-submitr  # noqa
    """
    return os.path.join(get_app_specific_directory(), "edu.harvard.hms", "smaht-submitr")
