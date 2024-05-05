import re
import subprocess
from typing import Callable, List, Optional, Union
from submitr.rclone.rclone_installation import RCloneInstallation


class RCloneCommands:

    @staticmethod
    def copy_command(args: List[str], config: Optional[str] = None, copyto: bool = False,
                     progress: Optional[Callable] = None,
                     dryrun: bool = False, raise_exception: bool = False) -> Union[bool, str]:
        # N.B The rclone --ignore-times option forces copy even if the file seems
        # not to have have changed, presumably based on something like a checksum.
        command = [RCloneInstallation.executable_path(),
                   "copyto" if copyto is True else "copy", "--progress", "--ignore-times"]
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
                if progress and (nbytes := RCloneCommands._parse_rclone_progress_bytes(line)):
                    progress(nbytes)
            process.stdout.close()
            result = process.wait()
            return True if (result == 0) else False
        except Exception as e:
            if raise_exception is True:
                raise e
            return False

    @staticmethod
    def exists_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[int]:
        command = [RCloneInstallation.executable_path(), "ls", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            result = subprocess.run(command, capture_output=True)
            # Example output: "  1234 some_file.fastq" where 1234 is file size.
            # Unfortunately if the given source (file) does not exist the return
            # code is 0; though if the bucket does not exist  then return code is 1.
            if not (result.returncode == 0):
                return False
            # Here though return code is 0 (implying bucket is OK) it still might
            # not be OK; will regard any output as an indication that it is OK.
            return (result.returncode == 0) or (len(result) > 0)
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    @staticmethod
    def size_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[int]:
        command = [RCloneInstallation.executable_path(), "size", source]
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
                elif (nbytes := RCloneCommands._parse_rclone_size_to_bytes(line)) is not None:
                    process.stdout.close()
                    return nbytes if found else None
            process.stdout.close()
            process.wait()
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def checksum_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[str]:
        command = [RCloneInstallation.executable_path(), "hashsum", "md5", source]
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

    @staticmethod
    def lsd_command(source: str, config: Optional[str] = None) -> bool:
        command = [RCloneInstallation.executable_path(), "lsd", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            return subprocess.run(command, capture_output=True).returncode == 0
        except Exception:
            return None

    _RCLONE_PROGRESS_UNITS = {"KiB": 2**10, "MiB": 2**20, "GiB": 2**30, "TiB": 2**40, "PiB": 2**50, "B": 1}
    _RCLONE_PROGRESS_PATTERN = rf".*Transferred:\s*(\d+(?:\.\d+)?)\s*({'|'.join(_RCLONE_PROGRESS_UNITS.keys())}).*"
    _RCLONE_PROGRESS_REGEX = re.compile(_RCLONE_PROGRESS_PATTERN)
    _RCLONE_SIZE_PATERN = r".*\((\d+) Byte\)"
    _RCLONE_SIZE_REGEX = re.compile(_RCLONE_SIZE_PATERN)

    @staticmethod
    def _parse_rclone_progress_bytes(value: str) -> Optional[str]:
        try:
            if match := RCloneCommands._RCLONE_PROGRESS_REGEX.search(value):
                return RCloneCommands._parse_rclone_progress_size_to_bytes(match.group(1), match.group(2))
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
                    units_size = RCloneCommands._RCLONE_PROGRESS_UNITS[size_string_components[1]]
                elif (size := size.strip()):
                    value = None
                    for units in RCloneCommands._RCLONE_PROGRESS_UNITS:
                        if (units_index := size.find(units)) > 0:
                            value = float(size[0:units_index])
                            units_size = RCloneCommands._RCLONE_PROGRESS_UNITS[units]
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
            if match := RCloneCommands._RCLONE_SIZE_REGEX.search(size):
                return int(match.group(1))
        except Exception:
            pass
        return None
