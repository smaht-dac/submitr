from contextlib import contextmanager
import os
from shutil import copy as copy_file
import subprocess
from typing import List, Optional
from dcicutils.file_utils import normalize_file_path
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_installation import (
    rclone_executable_install, rclone_executable_exists, rclone_executable_path
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
        if (isinstance(source_config := self.source_config, RCloneConfig) and
            isinstance(source_config_lines := source_config.config_lines, list)):  # noqa
            lines.extend(source_config_lines)
        if (isinstance(destination_config := self.destination_config, RCloneConfig) and
            isinstance(destination_config_lines := destination_config.config_lines, list)):  # noqa
            if lines:
                lines.append("")  # not necessary but sporting
            lines.extend(destination_config_lines)
        return lines

    @contextmanager
    def config_file(self) -> str:
        with temporary_file(suffix=".conf") as temporary_file_name:
            self.write_config_file(temporary_file_name)
            yield temporary_file_name

    def write_config_file(self, file: str) -> None:
        RCloneConfig._write_config_file_lines(file, self.config_lines)

    def copy(self, source_file: str, destination: Optional[str] = None,
             dryrun: bool = False, raise_exception: bool = True) -> object:
        """
        Uses rclone to copy the given source file to the given destination. All manner of variation is
        encapsulated within this simple statement. Depends on whether or not a source and/or destination
        configuration (RCloneConfig) has been specified and whether or not a bucket is specified in the
        that configuration et cetera. If no configuration is specified then we assume the local file
        system is the source and/or destination. TODO: Expand on these notes.
        """
        # TODO
        # Use copyto instead of copy to copy to specified file name.
        # rclone --config /tmp/rclone.conf copy hello.txt test-src-smaht-wolf:smaht-unit-testing-files
        # source_config = self.source_config
        source_config = self.source_config
        destination_config = self.destination_config
        if isinstance(destination_config, RCloneConfig):
            if isinstance(source_config, RCloneConfig):
                # TODO
                # Here both a source and destination config have been specified.
                with self.config_file() as config_file:  # noqa
                    # TODO
                    pass
                return None
            # Here only a destination config has been specified.
            with destination_config.config_file() as destination_config_file:
                if dryrun is True:
                    destination_config_file_persistent = create_temporary_file_name(suffix=".conf")
                    copy_file(destination_config_file, destination_config_file_persistent)
                    destination_config_file = destination_config_file_persistent
                if isinstance(destination, str) and destination and (destination != ".") and (destination != "/"):
                    # Here the given destination appears to be a file; so we use rclone copyto rather than copy.
                    # The destination bucket must either be specified in the destination_config or as the
                    # first (path-style) component of the given destination.
                    if not (destination_bucket := destination_config.bucket):
                        if (destination := normalize_file_path(destination, home_directory=False)).startswith(os.sep):
                            destination = destination[1:]
                        if len(destination_components := destination.split(os.sep)) >= 2:
                            destination_bucket = destination_components[0]
                            destination = "/".join(destination_components[1:])
                    command = [f"\"{self.executable_path()}\"",
                               "copyto", "--config", destination_config_file,
                               source_file,
                               f"{destination_config.name}:{destination_bucket}/{destination}"]
                else:
                    # Here no given destination was specified (or it was just a dot or slash)
                    # meaning copy the source to the bucket which must have been specified
                    # in the destination_config; so we use rclone copy rather than copyto.
                    if not destination_config.bucket:
                        raise Exception(f"No destination specified for copy and"
                                        f" no bucket specified in destination config.")
                    command = [f"\"{self.executable_path()}\"",
                               "copy", "--config", destination_config_file,
                               source_file,
                               f"{destination_config.name}:{destination_config.bucket}"]
                try:
                    if dryrun is True:
                        destination_config_file
                        return " ".join(command)
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    return result
                except Exception as e:
                    if raise_exception is True:
                        raise e
                return None
        elif isinstance(source_config, RCloneConfig):
            # Here only a source config has been specified.
            # TODO
            with source_config.config_file() as source_config_file:  # noqa
                # TODO
                pass
        return None

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
