from contextlib import contextmanager
import subprocess
from typing import List, Optional
from dcicutils.tmpfile_utils import temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_installation import (
    rclone_executable_install,
    rclone_executable_exists,
    rclone_executable_path
)


class RClone:

    def __init__(self) -> None:
        self._source_config = None
        self._destination_config = None

    @property
    def source_config(self) -> Optional[RCloneConfig]:
        return self._source_config

    @source_config.setter
    def source_config(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig) or value is None:
            self._source_config = value

    @property
    def destination_config(self) -> Optional[RCloneConfig]:
        return self._destination_config

    @destination_config.setter
    def destination_config(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig) or value is None:
            self._destination_config = value

    @property
    def config_lines(self) -> List[str]:
        lines = []
        if isinstance(source_config := self.source_config, RCloneConfig):
            if isinstance(source_config_lines := source_config.config_lines, list):
                lines.extend(source_config_lines)
        if isinstance(destination_config := self.destination_config, RCloneConfig):
            if isinstance(destination_config_lines := destination_config.config_lines, list):
                lines.extend(destination_config_lines)
        return lines

    @contextmanager
    def config_file(self) -> str:
        with temporary_file(suffix=".conf") as temporary_file_name:
            self.write_config_file(temporary_file_name)
            yield temporary_file_name

    def write_config_file(self, file: str) -> None:
        RCloneConfig._write_config_file_lines(file, self.config_lines)

    def copy(self, source_file: str, destination: Optional[str] = None, raise_exception: bool = False) -> bool:
        # TODO
        # Use copyto instead of copy to copy to specified file name.
        # rclone --config /tmp/rclone.conf copy hello.txt test-src-smaht-wolf:smaht-unit-testing-files
        # source_config = self.source_config
        source_config = self.destination_config
        destination_config = self.destination_config
        if isinstance(destination_config, RCloneConfig):
            if isinstance(source_config, RCloneConfig):
                # TODO
                # Here both a source and destination config was specified.
                return None
            with destination_config.config_file() as destination_config_file:
                if isinstance(destination, str) and destination and (destination != ".") and (destination != "/"):
                    # Here the given destination appears to be a file; so we use rclone copyto rather than copy.
                    command = [self.executable_path(),
                               "copyto", "--config", destination_config_file,
                               source_file,
                               f"{destination_config.name}:{destination_config.bucket}/{destination}"]
                else:
                    # Here no given destination was specified (or it was just a dot or slash)
                    # meaning copy the source to the bucket which must have been specified
                    # in the destination_config; so we use rclone copy rather than copyto.
                    if not destination_config.bucket:
                        raise Exception(f"No destination specified for copy and"
                                        f" no bucket specified in destination config.")
                    command = [self.executable_path(),
                               "copy", "--config", destination_config_file,
                               source_file,
                               f"{destination_config.name}:{destination_config.bucket}"]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                return result
        elif isinstance(source_config, RCloneConfig):
            # TODO
            pass
        return False

    @staticmethod
    def install(force_update: bool = True) -> Optional[str]:
        if not rclone_executable_exists() or force_update:
            return rclone_executable_install()
        return None

    @staticmethod
    def is_installed() -> bool:
        return rclone_executable_exists()

    @staticmethod
    def executable_path() -> str:
        return rclone_executable_path()
