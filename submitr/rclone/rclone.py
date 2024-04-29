from contextlib import contextmanager
import subprocess
from typing import List, Optional, Union
from dcicutils.tmpfile_utils import temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_installation import (
    rclone_executable_install, rclone_executable_exists, rclone_executable_path
)


class RClone:

    CLOUD_PATH_SEPARATOR = RCloneConfig.CLOUD_PATH_SEPARATOR

    def __init__(self, source: Optional[RCloneConfig] = None, destination: Optional[RCloneConfig] = None) -> None:
        self._source_config = source if isinstance(source, RCloneConfig) else None
        self._destination_config = destination if isinstance(destination, RCloneConfig) else None

    @property
    def source(self) -> Optional[RCloneConfig]:
        return self._source_config

    @source.setter
    def source(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig) or value is None:
            self._source_config = value

    @property
    def destination(self) -> Optional[RCloneConfig]:
        return self._destination_config

    @destination.setter
    def destination(self, value: RCloneConfig) -> None:
        if isinstance(value, RCloneConfig) or value is None:
            self._destination_config = value

    @property
    def config_lines(self) -> List[str]:
        lines = []
        if (isinstance(source := self.source, RCloneConfig) and
            isinstance(source_config_lines := source.config_lines, list)):  # noqa
            lines.extend(source_config_lines)
        if (isinstance(destination_config := self.destination, RCloneConfig) and
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

    def copy(self, source: str, destination: Optional[str] = None,
             dryrun: bool = False, raise_exception: bool = True) -> Union[bool, str]:
        """
        Uses rclone to copy the given source file to the given destination. All manner of variation is
        encapsulated within this simple statement. Depends on whether or not a source and/or destination
        configuration (RCloneConfig) has been specified and whether or not a bucket is specified in the
        that configuration et cetera. If no configuration is specified then we assume the local file
        system is the source and/or destination. TODO: Expand on these notes.

        If self.source and/or self.destination is None then it means the
        the source and/or destination arguments here refer to local files; i.e. when
        no RCloneConfig is specified we assume the (degenerate) case of local file.
        """
        # TODO
        # Use copyto instead of copy to copy to specified file name.
        # rclone --config /tmp/rclone.conf copy hello.txt test-src-smaht-wolf:smaht-unit-testing-files
        if isinstance(destination_config := self.destination, RCloneConfig):
            # Here a destination cloud configuration has been defined for this RClone object.
            if isinstance(source_config := self.source, RCloneConfig):
                # Here both a source and destination cloud configuration have been defined for this RClone
                # object; meaning we are copying from one cloud source to another cloud destination; i.e.
                # e.g from Amazon S3 or Google Cloud Storage to Amazon S3 or Google Cloud Storage.
                with self.config_file() as source_and_destination_config_file:  # noqa
                    # TODO: check what kind of source/destination etc.
                    command_args = ["copy", "--config", source_and_destination_config_file,
                                    f"{source_config.name}:{source}", f"{destination_config.name}:{destination}"]
                    return self._execute_rclone_command(command_args, dryrun=dryrun)
            # Here only a destination config cloud configuration has been specified for this RClone
            # object; meaning we are copying from a local file source to some cloud destination;
            # i.e. e.g. to Amazon S3 or Google Cloud Storage.
            with destination_config.config_file(persist_file=dryrun is True) as destination_config_file:
                command_args = []
                destination = RCloneConfig.normalize_cloud_path(destination)
                if destination and not (destination in ["."]):
                    # Here the given destination appears to be a file (bucket key); so we use rclone
                    # copyto rather than copy. The destination bucket be specified either in the
                    # destination_config or as the first (path-style) component of the given destination.
                    if not (destination_bucket := destination_config.bucket):
                        if len(destination_components := RCloneConfig.split_cloud_path(destination)) >= 2:
                            destination_bucket = destination_components[0]
                            destination = RCloneConfig.join_cloud_path(destination_components[1:])
                        else:
                            destination_bucket = destination
                            command_args = ["copy", "--config", destination_config_file, source,
                                            f"{destination_config.name}:{destination_bucket}"]
                    if not command_args:
                        destination_path = RCloneConfig.join_cloud_path(destination_bucket, destination)
                        command_args = ["copyto", "--config", destination_config_file, source,
                                        f"{destination_config.name}:{destination_path}"]
                else:
                    # Here the given destination argument was not specified (or it was just a dot or slash),
                    # meaning we are copying the (local file) source to the destination bucket which must
                    # have been specified in the destination_config; we use rclone copy rather than copyto.
                    if not destination_config.bucket:
                        raise Exception(f"No destination given for rclone copy and"
                                        f" no bucket specified in destination config.")
                    command_args = ["copy", "--config", destination_config_file, source,
                                    f"{destination_config.name}:{destination_config.bucket}"]
                return self._execute_rclone_command(command_args, dryrun=dryrun)
        elif isinstance(source_config := self.source, RCloneConfig):
            # Here only a source cloud configuration has been defined for this RClone object;
            # meaning we are copying from some cloud source to a local destination file.
            # TODO
            with source_config.config_file() as source_config_file:  # noqa
                # TODO: check what kind of source/destination etc.
                if source_config.bucket:
                    command_args = ["copy", "--config", source_config_file, source,
                                    f"{source_config.name}:{source_config.bucket}", destination]
                    pass
                else:
                    command_args = ["copy", "--config", source_config_file, source,
                                    f"{source_config.name}:{source_config.bucket}", destination]
                return self._execute_rclone_command(command_args, dryrun=dryrun)
        return False if not (dryrun is True) else None

    def _execute_rclone_command(self, args: List[str], dryrun: bool = False,
                                raise_exception: bool = False) -> Union[bool, str]:
        command = [self.executable_path(), *(args or [])]
        command.append("--progress")  # command.append("-vv")
        def command_string(command: List[str]) -> str:  # noqa
            if " " in command[0]:
                command[0] = f"\"{command[0]}\""
            return " ".join(command)
        try:
            if dryrun is True:
                return command_string(command)
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True if (result.returncode == 0) else False
        except Exception as e:
            if raise_exception is True:
                raise e
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

    @staticmethod
    def normalize_cloud_path(value: str) -> str:
        return RCloneConfig.normalize_cloud_path(value)

    @staticmethod
    def join_cloud_path(*args) -> str:
        return RCloneConfig.join_cloud_path(*args)

    @staticmethod
    def split_cloud_path(value: str) -> List[str]:
        return RCloneConfig.split_cloud_path(value)

    @staticmethod
    def cloud_path_to_file_path(value: str) -> str:
        return RCloneConfig.cloud_path_to_file_path(value)
