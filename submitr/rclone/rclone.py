from contextlib import contextmanager
import os
import re
from shutil import copy as copy_file
import subprocess
from typing import Callable, List, Optional, Union
from dcicutils.command_utils import yes_or_no
from dcicutils.file_utils import normalize_path
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.utils import format_path
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_utils import cloud_path
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
    def config_file(self, persist: bool = False, extra_lines: Optional[List[str]] = None) -> str:
        with temporary_file(suffix=".conf") as temporary_config_file_name:
            self.write_config_file(temporary_config_file_name, extra_lines=extra_lines)
            if persist is True:
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    def write_config_file(self, file: str, extra_lines: Optional[List[str]] = None) -> None:
        RCloneConfig._write_config_file_lines(file, self.config_lines, extra_lines=extra_lines)

    def copy(self, source: str, destination: Optional[str] = None,
             progress: Optional[Callable] = None,
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
                    raise Exception(f"No cloud destination specified.")
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
                    raise Exception(f"No cloud source specified.")
                if not cloud_path.has_separator(source):
                    raise Exception(f"No cloud source key/file specified (only bucket: {source}).")
                with self.config_file(persist=dryrun is True) as source_and_destination_config_file:  # noqa
                    command_args = [f"{source_config.name}:{source}", f"{destination_config.name}:{destination}"]
                    return self._execute_rclone_copy_command(command_args,
                                                             config=source_and_destination_config_file,
                                                             copyto=copyto, progress=progress, dryrun=dryrun)
            else:
                # Here only a destination config cloud configuration has been defined for this RClone
                # object; meaning we are copying from a local file source to some cloud destination;
                # i.e. e.g. from a local file to either Amazon S3 or Google Cloud Storage.
                if not (source := normalize_path(source)):
                    raise Exception(f"No file source specified.")
                with destination_config.config_file(persist=dryrun is True) as destination_config_file:
                    command_args = [source, f"{destination_config.name}:{destination}"]
                    return self._execute_rclone_copy_command(command_args,
                                                             config=destination_config_file,
                                                             copyto=copyto, progress=progress, dryrun=dryrun)
        elif isinstance(source_config := self.source, RCloneConfig):
            # Here only a source cloud configuration has been defined for this RClone object;
            # meaning we are copying from some cloud source to a local file destination;
            # i.e. e.g. from either Amazon S3 or Google Cloud Storage to a local file.
            if source_config.bucket:
                # A bucket in the source RCloneConfig is nothing more than an alternative
                # way of manually placing it at the beginning of the given source argument.
                source = cloud_path.join(source_config.bucket, source)
            if not (source := cloud_path.normalize(source)):
                raise Exception(f"No cloud source specified.")
            if not cloud_path.has_separator(source):
                raise Exception(f"No cloud source key/file specified (only bucket: {source}).")
            if not (destination := normalize_path(destination)):
                raise Exception(f"No file destination specified.")
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
                command_args = [f"{source_config.name}:{source}", destination]
                return self._execute_rclone_copy_command(command_args,
                                                         config=source_config_file,
                                                         copyto=True, progress=progress, dryrun=dryrun)
        else:
            # Here not source or destination cloud configuration has been defined for this RClone;
            # object; meaning this is (degenerate case of a) simple local file to file copy.
            if not (source := normalize_path(source)):
                raise Exception(f"No file source specified.")
            if not (destination := normalize_path(destination)):
                raise Exception(f"No file destination specified.")
            if not os.path.isdir(destination):
                copyto = True
            command_args = [source, destination]
            return self._execute_rclone_copy_command(command_args, copyto=copyto, progress=progress, dryrun=dryrun)

    def exists(self, source: str, config: Optional[RCloneConfig] = None) -> bool:
        if not isinstance(config, RCloneConfig):
            if not isinstance(config := self.source, RCloneConfig):
                if not isinstance(config := self.destination, RCloneConfig):
                    return None
        try:
            with config.config_file() as config_file:
                return self._execute_rclone_exists_command(source=f"{config.name}:{source}", config=config_file)
        except Exception:
            return None

    def size(self, source: str, config: Optional[RCloneConfig] = None) -> Optional[int]:
        if not isinstance(config, RCloneConfig):
            if not isinstance(config := self.source, RCloneConfig):
                if not isinstance(config := self.destination, RCloneConfig):
                    return None
        try:
            with config.config_file() as config_file:
                return self._execute_rclone_size_command(source=f"{config.name}:{source}", config=config_file)
        except Exception:
            return None

    def checksum(self, source: str, config: Optional[RCloneConfig] = None) -> Optional[str]:
        if not isinstance(config, RCloneConfig):
            if not isinstance(config := self.source, RCloneConfig):
                if not isinstance(config := self.destination, RCloneConfig):
                    return None
        try:
            with config.config_file() as config_file:
                return self._execute_rclone_checksum_command(source=f"{config.name}:{source}", config=config_file)
        except Exception:
            return None

    def ping(self, config: Optional[RCloneConfig] = None) -> bool:
        if not isinstance(config, RCloneConfig):
            if not isinstance(config := self.source, RCloneConfig):
                if not isinstance(config := self.destination, RCloneConfig):
                    return None
        try:
            # Use the rclone lsd command as proxy for a "ping".
            # For some reason with this command we need the project_number in the config for Google.
            if hasattr(config, "project") and isinstance(project := config.project, str) and project:
                extra_lines = [f"project_number = {project}"]
            else:
                extra_lines = None
            with config.config_file(extra_lines=extra_lines) as config_file:
                return self._execute_rclone_ping_command(source=f"{config.name}:", config=config_file)
        except Exception:
            return False

    def _execute_rclone_copy_command(self, args: List[str], config: Optional[str] = None, copyto: bool = False,
                                     progress: Optional[Callable] = None,
                                     dryrun: bool = False, raise_exception: bool = False) -> Union[bool, str]:
        # N.B The rclone --ignore-times option forces copy even if the file seems
        # not to have have changed, presumably based on something like a checksum.
        command = [self.executable_path(), "copyto" if copyto is True else "copy", "--progress", "--ignore-times"]
        if isinstance(config, str) and config:
            command += ["--config", config]
        if isinstance(args, list):
            command += args
        if not callable(progress):
            progress = None
        try:
            if dryrun is True:
                if " " in command[0]:
                    command[0] = f"\"{command[0]}\""
                return " ".join(command)
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in process.stdout:
                if progress and (nbytes := RClone._parse_rclone_progress_bytes(line)):
                    progress(nbytes)
            process.stdout.close()
            result = process.wait()
            return True if (result == 0) else False
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    def _execute_rclone_exists_command(self, source: str, config: Optional[str] = None,
                                       raise_exception: bool = False) -> Optional[int]:
        command = [self.executable_path(), "ls", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Example output: "  1234 some_file.fastq" where 1234 is file size.
            nlines = 0
            for line in process.stdout:
                nlines += 1
            process.stdout.close()
            process.wait()
            return nlines == 1
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def _execute_rclone_size_command(self, source: str, config: Optional[str] = None,
                                     raise_exception: bool = False) -> Optional[int]:
        command = [self.executable_path(), "size", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Example output: "Total objects: 1" <CR> "Total size: 64.850 MiB (68000001 Byte)"
            found = False
            for line in process.stdout:
                if line.lower().strip().replace(" ", "") == "totalobjects:1":
                    found = True
                elif (nbytes := RClone._parse_rclone_size_to_bytes(line)) is not None:
                    process.stdout.close()
                    return nbytes if found else None
            process.stdout.close()
            process.wait()
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    def _execute_rclone_checksum_command(self, source: str, config: Optional[str] = None,
                                         raise_exception: bool = False) -> Optional[str]:
        command = [self.executable_path(), "hashsum", "md5", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in process.stdout:
                # Example output: "e0807de443b152ff44d6668959460064  some_file.fastq"
                if len(line_components := line.split()) > 0 and line_components[0]:
                    checksum = line_components[0]
                    process.stdout.close()
                    return checksum
            process.stdout.close()
            process.wait()
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    def _execute_rclone_ping_command(self, source: str, config: Optional[str] = None) -> bool:
        command = [self.executable_path(), "lsd", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            return subprocess.run(command, capture_output=True).returncode == 0
        except Exception:
            return None

    @staticmethod
    def verify_installation(progress: bool = True) -> bool:
        if RClone.is_installed():
            print(f"You have requested an rclone feature; already installed:"
                  f" {format_path(RClone.executable_path())} ✓")
            return True
        print("You have requested an rclone feature; rclone not installed.")
        if yes_or_no("Do you want to install rclone now (should be quick & painless)?"):
            if not (rclone_executable := RClone.install(progress=progress, force_update=False)):
                print("ERROR: Encountered a problem installing rclone. Please seek help (TODO).")
                return False
            print(f"Successfully installed rclone: {format_path(rclone_executable)}")
        return True

    @staticmethod
    def install(progress: bool = False, force_update: bool = True) -> Optional[str]:
        if not rclone_executable_exists() or force_update:
            return rclone_executable_install(progress=progress)
        if RClone.is_installed():
            return RClone.executable_path()
        return None

    @staticmethod
    def is_installed() -> bool:
        return rclone_executable_exists()

    @staticmethod
    def executable_path() -> str:
        return rclone_executable_path()

    _RCLONE_PROGRESS_UNITS = {"KiB": 2**10, "MiB": 2**20, "GiB": 2**30, "TiB": 2**40, "PiB": 2**50, "B": 1}
    _RCLONE_PROGRESS_PATTERN = rf".*Transferred:\s*(\d+(?:\.\d+)?)\s*({'|'.join(_RCLONE_PROGRESS_UNITS.keys())}).*"
    _RCLONE_PROGRESS_REGEX = re.compile(_RCLONE_PROGRESS_PATTERN)
    _RCLONE_SIZE_PATERN = r".*\((\d+) Byte\)"
    _RCLONE_SIZE_REGEX = re.compile(_RCLONE_SIZE_PATERN)

    @staticmethod
    def _parse_rclone_progress_bytes(value: str) -> Optional[str]:
        try:
            if match := RClone._RCLONE_PROGRESS_REGEX.search(value):
                return RClone._parse_rclone_progress_size_to_bytes(match.group(1), match.group(2))
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_rclone_progress_size_to_bytes(size: str, units: Optional[str] = None) -> Optional[int]:
        if isinstance(size, str):
            if isinstance(units, str):
                size += f" {units}"
            try:
                if len(size_string_components := size.split()) >= 2:
                    value = float(size_string_components[0])
                    units_size = RClone._RCLONE_PROGRESS_UNITS[size_string_components[1]]
                elif (size := size.strip()):
                    value = None
                    for units in RClone._RCLONE_PROGRESS_UNITS:
                        if (units_index := size.find(units)) > 0:
                            value = float(size[0:units_index])
                            units_size = RClone._RCLONE_PROGRESS_UNITS[units]
                            break
                    if not value:
                        return None
                return int(value * units_size)
            except Exception:
                pass
        return None

    def _parse_rclone_size_to_bytes(size: str) -> Optional[int]:
        # Parse the relevant output from the rclone size command;
        # for example: Total size: 64.850 MiB (68000001 Byte)
        try:
            if match := RClone._RCLONE_SIZE_REGEX.search(size):
                return int(match.group(1))
        except Exception:
            pass
        return None
