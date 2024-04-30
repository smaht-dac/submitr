from contextlib import contextmanager
from subprocess import run as subprocess_run
import os
from shutil import copy as copy_file
from typing import List, Optional, Union
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_utils import cloud_path, normalize_path
from submitr.rclone.rclone_installation import (
    rclone_executable_install, rclone_executable_exists, rclone_executable_path
)


class RClone:

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
    def config_file(self, persist: bool = False) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            self.write_config_file(temporary_config_file_name)
            if persist is True:
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    def write_config_file(self, file: str) -> None:
        RCloneConfig._write_config_file_lines(file, self.config_lines)

    def copy(self, source: str, destination: Optional[str] = None,
             nodirectories: bool = False, dryrun: bool = False, raise_exception: bool = True) -> Union[bool, str]:
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
        copyto = False
        # Use copyto instead of copy to copy to specified file name.
        # rclone --config /tmp/rclone.conf copy hello.txt test-src-smaht-wolf:smaht-unit-testing-files
        if isinstance(destination_config := self.destination, RCloneConfig):
            # Here a destination cloud configuration has been defined for this RClone object;
            # meaning we are copying to some cloud destination (and not to a local file destination).
            if destination_config.bucket:
                # A bucket in the destination RCloneConfig is nothing more than an alternative
                # way of manually placing it at the beginning of the given destination argument.
                if not (destination := cloud_path.join(destination_config.bucket, destination)):
                    raise Exception("No cloud destination specified.")
            if cloud_path.has_separator(destination):
                # If the destination has NO slashes it is assumed to be ONLY the bucket;
                # in which case we will rclone copy; otherwise we need to use rclone copyto.
                copyto = True
            if isinstance(source_config := self.source, RCloneConfig):
                # Here both a source and destination cloud configuration have been defined for this RClone
                # object; meaning we are copying from one cloud source to another cloud destination; i.e. e.g.
                # from either Amazon S3 or Google Cloud Storage to either Amazon S3 or Google Cloud Storage.
                if source_config.bucket:
                    # A bucket in the source RCloneConfig is nothing more than an alternative
                    # way of manually placing it at the beginning of the given source argument.
                    source = cloud_path.join(source_config.bucket, source)
                if not (source := cloud_path.normalize(source)):
                    raise Exception("No cloud source specified.")
                if not cloud_path.has_separator(source):
                    raise Exception("No cloud source key/file specified (only bucket: {source)}.")
                with self.config_file(persist=dryrun is True) as source_and_destination_config_file:  # noqa
                    command_args = ["--config", source_and_destination_config_file,
                                    f"{source_config.name}:{source}",
                                    f"{destination_config.name}:{destination}"]
                    return self._execute_rclone_copy_command(command_args, copyto=copyto, dryrun=dryrun)
            else:
                # Here only a destination config cloud configuration has been defined for this RClone
                # object; meaning we are copying from a local file source to some cloud destination;
                # i.e. e.g. from a local file to either Amazon S3 or Google Cloud Storage.
                if not (source := normalize_path(source)):
                    raise Exception("No file source specified.")
                with destination_config.config_file(persist=dryrun is True) as destination_config_file:
                    command_args = ["--config", destination_config_file,
                                    source,
                                    f"{destination_config.name}:{destination}"]
                    return self._execute_rclone_copy_command(command_args, copyto=copyto, dryrun=dryrun)
        elif isinstance(source_config := self.source, RCloneConfig):
            # Here only a source cloud configuration has been defined for this RClone object;
            # meaning we are copying from some cloud source to a local file destination;
            # i.e. e.g. from either Amazon S3 or Google Cloud Storage to a local file.
            if source_config.bucket:
                # A bucket in the source RCloneConfig is nothing more than an alternative
                # way of manually placing it at the beginning of the given source argument.
                source = cloud_path.join(source_config.bucket, source)
            if not (source := cloud_path.normalize(source)):
                raise Exception("No cloud source specified.")
            if not cloud_path.has_separator(source):
                raise Exception("No cloud source key/file specified (only bucket: {source)}.")
            if not (destination := normalize_path(destination)):
                raise Exception("No file destination specified.")
            if os.path.isdir(destination):
                if nodirectories is True:
                    # do i need to get the basename of the cloud source? no, but minus the bucket
                    key_as_file_name = cloud_path.key(source).replace(cloud_path.separator, "_")
                    destination = os.path.join(destination, key_as_file_name)
                else:
                    key_as_file_path = cloud_path.to_file_path(cloud_path.key(source))
                    destination_directory = normalize_path(os.path.join(destination, os.path.dirname(key_as_file_path)))
                    os.makedirs(destination_directory, exist_ok=True)
                    destination = os.path.join(destination, key_as_file_path)
            with source_config.config_file(persist=dryrun is True) as source_config_file:  # noqa
                command_args = ["--config", source_config_file,
                                f"{source_config.name}:{source}",
                                destination]
                return self._execute_rclone_copy_command(command_args, copyto=True, dryrun=dryrun)
        else:
            # Here not source or destination cloud configuration has been defined for this RClone;
            # object; meaning this is (degenerate case of a) simple local file to file copy.
            if not (source := normalize_path(source)):
                raise Exception("No file source specified.")
            if not (destination := normalize_path(destination)):
                raise Exception("No file destination specified.")
            if not os.path.isdir(destination):
                copyto = True
            command_args = [source, destination]
            return self._execute_rclone_copy_command(command_args, copyto=copyto, dryrun=dryrun)

    def _execute_rclone_copy_command(self, args: List[str], copyto: bool = False,
                                     dryrun: bool = False, raise_exception: bool = False) -> Union[bool, str]:
        command = [self.executable_path(), "copyto" if copyto is True else "copy", *(args or [])]
        command.append("--progress")  # command.append("-vv") # TODO
        def command_string(command: List[str]) -> str:  # noqa
            if " " in command[0]:
                command[0] = f"\"{command[0]}\""
            return " ".join(command)
        try:
            if dryrun is True:
                return command_string(command)
            result = subprocess_run(command, capture_output=True, text=True, check=True)
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
