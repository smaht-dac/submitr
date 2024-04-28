from contextlib import contextmanager
import subprocess
from typing import List, Optional, Union
from dcicutils.tmpfile_utils import temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_installation import (
    rclone_executable_install, rclone_executable_exists, rclone_executable_path
)


class RClone:

    def __init__(self, source: Optional[RCloneConfig] = None, destination: Optional[RCloneConfig] = None) -> None:
        self._source_config = source if isinstance(source, RCloneConfig) else None
        self._destination_config = destination if isinstance(destination, RCloneConfig) else None

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

    def upload(self, source_file: str, destination: Optional[str] = None,
               dryrun: bool = False, raise_exception: bool = True) -> Union[bool, str]:
        # TODO
        pass

    def download(self, source: str, destination_file: Optional[str] = None,
                 dryrun: bool = False, raise_exception: bool = True) -> Union[bool, str]:
        # TODO
        pass

    def copy(self, source_file: str, destination: Optional[str] = None,
             dryrun: bool = False, raise_exception: bool = True) -> Union[bool, str]:
        """
        Uses rclone to copy the given source file to the given destination. All manner of variation is
        encapsulated within this simple statement. Depends on whether or not a source and/or destination
        configuration (RCloneConfig) has been specified and whether or not a bucket is specified in the
        that configuration et cetera. If no configuration is specified then we assume the local file
        system is the source and/or destination. TODO: Expand on these notes.

        If self.source_config and/or self.destination_config is None then it means the
        the source and/or destination arguments here refer to local files; i.e. when
        no RCloneConfig is specified we assume the (degenerate) case of local file.
        """
        # TODO
        # Use copyto instead of copy to copy to specified file name.
        # rclone --config /tmp/rclone.conf copy hello.txt test-src-smaht-wolf:smaht-unit-testing-files
        # source_config = self.source_config
        source_config = self.source_config
        destination_config = self.destination_config
        if isinstance(destination_config, RCloneConfig):
            if isinstance(source_config, RCloneConfig):
                # Here both a source and destination config have been specified; meaning we
                # are copying from some cloud source to some cloud destination; i.e. e.g from
                # Amazon S3 or Google Cloud Storage to Amazon S3 or Google Cloud Storage.
                with self.config_file() as config_file:  # noqa
                    # TODO
                    pass
                return None
            # Here only a destination config has been specified; meaning we
            # are copying from the (local file) source to some cloud destination;
            # i.e. e.g. to Amazon S3 or Google Cloud Storage.
            with destination_config.config_file(persist_file=dryrun is True) as destination_config_file:
                command = None
                destination = RCloneConfig.normalize_cloud_path(destination)
                if destination and not (destination in [".", "/"]):
                    # Here the given destination appears to be a file (bucket key); so we use rclone
                    # copyto rather than copy. The destination bucket be specified either in the
                    # destination_config or as the first (path-style) component of the given destination.
                    if not (destination_bucket := destination_config.bucket):
                        if destination.startswith("/"):
                            destination = destination[1:]
                        if len(destination_components := destination.split("/")) >= 2:
                            destination_bucket = destination_components[0]
                            destination = "/".join(destination_components[1:])
                        else:
                            destination_bucket = destination
                            command = [self.executable_path(),
                                       "copy", "--config", destination_config_file, source_file,
                                       f"{destination_config.name}:{destination_bucket}"]
                    if not command:
                        command = [self.executable_path(),
                                   "copyto", "--config", destination_config_file, source_file,
                                   f"{destination_config.name}:{destination_bucket}/{destination}"]
                else:
                    # Here the given destination argument was not specified (or it was just a dot or slash),
                    # meaning we are copying the (local file) source to the destination bucket which must
                    # have been specified in the destination_config; we use rclone copy rather than copyto.
                    if not destination_config.bucket:
                        raise Exception(f"No destination given for rclone copy and"
                                        f" no bucket specified in destination config.")
                    command = [self.executable_path(),
                               "copy", "--config", destination_config_file, source_file,
                               f"{destination_config.name}:{destination_config.bucket}"]
                command.append("--progress")
                command.append("-vv")
                try:
                    if dryrun is True:
                        if " " in command[0]:
                            command[0] = f"\"{command[0]}\""
                        return " ".join(command)
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    return True if (result.returncode == 0) else False
                except Exception as e:
                    if raise_exception is True:
                        raise e
                return False if not (dryrun is True) else None
        elif isinstance(source_config, RCloneConfig):
            # Here only a source config has been specified.
            # TODO
            with source_config.config_file() as source_config_file:  # noqa
                # TODO
                pass
        return False if not (dryrun is True) else None

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
