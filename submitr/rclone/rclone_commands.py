import re
import subprocess
from typing import Callable, List, Optional, Tuple, Union
from dcicutils.misc_utils import normalize_string
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.utils import DEBUG


class RCloneCommands:

    @staticmethod
    def copy_command(args: List[str], config: Optional[str] = None, copyto: bool = False,
                     progress: Optional[Callable] = None,
                     dryrun: bool = False,
                     destination_s3: bool = False,
                     return_output: bool = False,
                     raise_exception: bool = False) -> Union[bool, Tuple[bool, List[str]]]:
        command = [RCloneInstallation.executable_path(),
                   "copyto" if copyto is True else "copy", "--progress", "--ignore-times"]
        # The rclone --ignore-times option forces copy even if the file seems
        # not to have have changed, presumably based on something like a checksum.
        command += ["--ignore-times"]
        if destination_s3:
            # The rclone --s3-no-check-bucket option obviates need for s3:CreateBucket in credentials policy.
            # The rclone --s3-no-head-object option obviates need for s3:ListBucket in credentials policy.
            command += ["--s3-no-check-bucket", "--s3-no-head-object"]
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
            DEBUG(f"RCLONE-COPY-COMMAND: {' '.join(command)}")
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if return_output is True:
                lines = []
            for line in process.stdout:
                DEBUG(f"RCLONE-COPY-OUTPUT: {normalize_string(line)}")
                if progress and (nbytes := RCloneCommands._parse_rclone_progress_bytes(line)):
                    progress(nbytes)
                if (return_output is True) and (line := normalize_string(line)):
                    lines.append(line)
            process.stdout.close()
            result = process.wait()
            DEBUG(f"RCLONE-COPY-RESULT: {process.returncode}")
            result = True if (result == 0) else False
            return result if not (return_output is True) else (result, lines)
        except Exception as e:
            if raise_exception is True:
                raise e
            return False if not (return_output is True) else (False, [])

    @staticmethod
    def exists_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[int]:
        command = [RCloneInstallation.executable_path(), "ls", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            # Example output: "  1234 some_file.fastq" where 1234 is file size.
            # Unfortunately if the given source (file) does not exist the return
            # code is 0; though if the bucket does not exist then return code is 1.
            # So even if return code is 0 (implying bucket is OK) it still might
            # not be OK; will regard any output as an indication that it is OK.
            return RCloneCommands._run_okay(command, some_output_required=True)
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
            for line in RCloneCommands._run(command):
                if line.lower().strip().replace(" ", "") == "totalobjects:1":
                    found = True
                elif (nbytes := RCloneCommands._parse_rclone_size_to_bytes(line)) is not None:
                    return nbytes if found else None
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def checksum_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[str]:
        # Note that it is known to be the case that calling rclone hashsum to get the checksum
        # of a file in Google Cloud Storage (GCS) merely retrieves the checksum from GCS,
        # which had previously been computed/stored by GCS for the file within GCS;
        # presumably when the file was originally uploaded to GCS.
        command = [RCloneInstallation.executable_path(), "hashsum", "md5", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            # Example output: "e0807de443b152ff44d6668959460064  some_file.fastq"
            for line in RCloneCommands._run(command):
                if len(line_components := line.split()) > 0 and line_components[0]:
                    checksum = line_components[0]
                    return checksum
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def ping_command(source: str, config: Optional[str] = None, args: Optional[List[str]] = None) -> bool:
        # Use the rclone lsd command as proxy for a "ping".
        command = [RCloneInstallation.executable_path(), "lsd", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        if isinstance(args, list):
            command += [arg for arg in args if isinstance(arg, str) and arg]
        try:
            return RCloneCommands._run_okay(command)
        except Exception:
            return None

    @staticmethod
    def _run(command: List[str], return_code_only: bool = False) -> Union[List[str], int]:
        result = RCloneCommands._execute(command)
        if return_code_only is True:
            return result.returncode
        return result.stdout.split("\n")

    @staticmethod
    def _run_okay(command: List[str], some_output_required: bool = False) -> bool:
        result = RCloneCommands._execute(command)
        if result.returncode == 0:
            if not (some_output_required is True) or (len(result.stdout) > 0):
                return True
        return False

    @staticmethod
    def _execute(command: List[str]) -> subprocess.CompletedProcess:
        DEBUG(f"RCLONE-COMMAND: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, universal_newlines=True)
        DEBUG(f"RCLONE-COMMAND-OUTPUT: {normalize_string(result.stdout)}")
        DEBUG(f"RCLONE-COMMAND-RESULT: {result.returncode}")
        return result

    # All this parsing stuff is so that we can use our dcicutils.progress_bar with the rclone copy.
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

    @staticmethod
    def _parse_rclone_size_to_bytes(size: str) -> Optional[int]:
        # Parse the relevant output from the rclone size command;
        # for example: Total size: 64.850 MiB (68000001 Byte)
        try:
            if match := RCloneCommands._RCLONE_SIZE_REGEX.search(size):
                return int(match.group(1))
        except Exception:
            pass
        return None
