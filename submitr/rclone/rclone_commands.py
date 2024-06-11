import json
import os
import re
import subprocess
from typing import Callable, List, Optional, Tuple, Union
from dcicutils.datetime_utils import format_datetime, parse_datetime
from dcicutils.misc_utils import normalize_string
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.utils import DEBUG


class RCloneCommands:

    @staticmethod
    def copy_command(args: List[str], config: Optional[str] = None, copyto: bool = False,
                     metadata: Optional[dict] = None,
                     progress: Optional[Callable] = None,
                     dryrun: bool = False,
                     source_s3: bool = False,
                     destination_s3: bool = False,
                     process_info: Optional[dict] = None,
                     return_output: bool = False,
                     raise_exception: bool = False) -> Union[bool, Tuple[bool, List[str]]]:
        command = [RCloneInstallation.executable_path(), "copyto" if copyto is True else "copy"]
        #
        # Notes on rclone options:
        #
        # --progress
        #   This enables real-time command-line progress output, which we
        #   parse to allow us to give our own feedback via dcicutils.progress_bar.
        #
        # --ignore-times
        #   This forces a copy even if the file seems not to have have changed,
        #   presumably based on something like a checksum.
        #
        # --s3-no-check-bucket option obviates need for s3:CreateBucket in credentials policy.
        #   This obviates need for s3:CreateBucket in our AWS S3 credentials policy.
        #   See encoded_core.types.file.external_creds function; and see also testing module
        #   submitr.rclone.testing.rclone_utils_for_testing_amazon.AwsS3.generate_temporary_credentials.
        #
        # --s3-no-head-object
        #   This obviates need for s3:ListBucket in our AWS S3 credentials policy.
        #   See encoded_core.types.file.external_creds function; and see also testing module
        #   submitr.rclone.testing.rclone_utils_for_testing_amazon.AwsS3.generate_temporary_credentials.
        #
        # --ignore-size
        #   This is necessary because since we are using --s3-no-head-object rclone (evidently)
        #   cannot get the size (i.e. via s3.head_object) of the target AWS S3 file, and so
        #   without this we get an rclone error like below, and it retries (bad) up to 3 times:
        #   ERROR: SMAFIQ81LMQZ.fastq: corrupted on transfer: sizes differ 2147483648 vs 0
        #   ERROR: Attempt 1/3 failed with 1 errors and: corrupted on transfer: sizes differ 2147483648 vs 0
        #
        # --header-upload
        #   This is to set the metadata for an uploaded (AWS S3) object. Note we need to included any
        #   existing metaadata on the object, if it already exists, otherwise it will get blown away;
        #   this is done in the s3_upload module..
        #
        # Note that when copying to S3 via rclone, rclone seems to also write these metadata for the
        # copied file in S3: x-amz-meta-md5chksum set to the md5 of the copied file; x-amz-meta-mtime
        # set to the time_t (with millisconds e.g. 1718017149.229304173) of the copy.
        #
        # FYI: https://forum.rclone.org/t/copy-to-scality-s3-corrupted-on-transfer-sizes-differ-xxx-vs-0/43281/3
        #
        command += ["--progress", "--ignore-times", "--ignore-size"]
        if destination_s3:
            command += ["--s3-no-check-bucket"]
            if source_s3 is True:
                # See else below; but we sill need --s3-no-head for S3 source.
                command += ["--s3-no-head"]
            else:
                # For some reason if BOTH the source and destination are
                # S3 then --s3-no-head-object prevents this from working.
                command += ["--s3-no-head-object"]
            if isinstance(metadata, dict):
                for metadata_key in metadata:
                    metadata_value = metadata[metadata_key]
                    command += ["--header-upload", f"X-Amz-Meta-{metadata_key}: {metadata_value}"]
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
            # Note the preexec_fn argument here, which is essential to ensure that a
            # keyboard interrupt (CTRL-C), e.g. which we handle for file uploads ourselves
            # in s3_upload, is not passed on to this rclone child subprocess thus killing it.
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       preexec_fn=os.setsid)
            if isinstance(process_info, dict):
                process_info["process"] = process
                process_info["pid"] = process.pid
            if return_output is True:
                lines = []
            output_indicates_success = False
            for line in process.stdout:
                # For some reason if copying a NON-existent file from GCS, AND the destination
                # is NOT an existing file, we do not get an explicit error from rclone, and even
                # the return status code is 0 (indicating success); the only thing it seems the
                # differentiate a success from failure is the presence of "100%" in the output.
                # i.e. e.g. a line like this: Transferred: 1 / 1, 100%
                DEBUG(f"RCLONE-COPY-OUTPUT: {normalize_string(line)}")
                if progress and (nbytes := RCloneCommands._parse_rclone_progress_bytes(line)):
                    progress(nbytes)
                if (return_output is True) and (line := normalize_string(line)):
                    lines.append(line)
                if isinstance(line, str) and "Transferred" in line and "100%" in line:
                    output_indicates_success = True
            process.stdout.close()
            result = process.wait()
            DEBUG(f"RCLONE-COPY-RESULT: {process.returncode}")
            result = True if (result == 0) and output_indicates_success else False
            return result if not (return_output is True) else (result, lines)
        except Exception as e:
            if raise_exception is True:
                raise e
            return False if not (return_output is True) else (False, [])

    @staticmethod
    def exists_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[bool]:
        # Obsolete; see above comments.
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
    def file_exists_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[bool]:
        try:
            return RCloneCommands.info_command(source, config=config,
                                               raise_exception=raise_exception).get("directory") is False
        except Exception:
            return None

    @staticmethod
    def size_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[int]:
        # Use the info_command (which does lsjson --stat) not only because it's a good central way to get
        # size (and other) info, but when getting using rclone size on a key in a bucket with temporary
        # credentials (which are targeted to a bucket/key) we need to have the s3:ListBucket policy on
        # those credentials, but for the entire bucket; the trick we used to get S3-to-S3 copy to work,
        # where we restricted the s3:ListBucket to a prefix condition set to the exact key, does not work;
        # but that's with rclone size command (and even rclone ls fails as well); but using rclone lsjson,
        # as the info_command does) is fine. This permission stuff with rclone and S3 is very finicky indeed.
        try:
            result = RCloneCommands.info_command(source, config=config, raise_exception=raise_exception)
            # N.B. Returns a size of -1 if file/key not found (at least for GCS).
            return size if isinstance(result, dict) and (size := result.get("size")) and (size >= 0) else None
        except Exception:
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
            # TODO
            # Figure out why not checksum sometimes for example with:
            # s3://smaht-wolf-application-files/098fcb63-09ed-45fa-8247-c547c609965b/SMAFIF5DIQ11.gtf
            for line in RCloneCommands._run(command):
                if len(line_components := line.split()) > 0 and line_components[0]:
                    checksum = line_components[0]
                    return checksum
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def info_command(source: str, config: Optional[str] = None, raise_exception: bool = False) -> Optional[dict]:
        command = [RCloneInstallation.executable_path(), "lsjson", "--stat", "--metadata", source]
        if isinstance(config, str) and config:
            command += ["--config", config]
        try:
            # Example output:
            # {
            #     "Path": "SMAFIWTTIQXD.fastq",
            #     "Name": "SMAFIWTTIQXD.fastq",
            #     "Size": 107374182400,
            #     "MimeType": "text/plain",
            #     "ModTime": "2024-05-20T22:09:51.636000000-04:00",
            #     "IsDir": false,
            #     "Tier": "STANDARD",
            #     "Metadata": {
            #         "btime": "2024-05-21T15:21:12Z",
            #         "content-type": "text/plain",
            #         "etag": "cac82084c62847e6acbb22211cff9fd8-9310",
            #         "md5": "e65fced4c4a5f37d63154802fe04e71e",
            #         "md5-source": "google-cloud-storage",
            #         "md5-timestamp": "1716304863.026897",
            #         "modified": "2024-05-21 09:14:27 EDT",
            #         "mtime": "2024-05-20T22:09:51.636-04:00",
            #         "size": "107374182400",
            #         "tier": "STANDARD"
            #     }
            # }
            if not (result := RCloneCommands._run(command)):
                return {}
            elif not (result := "".join(result)):
                return {}
            elif not isinstance(result := json.loads(result), dict):
                return {}
            name = result["Name"]
            size = result["Size"]
            metadata = {"metadata": result["Metadata"]} if "Metadata" in result else {}
            modified = format_datetime(parse_datetime(result["ModTime"]))
            directory = result.get("IsDir") is True
            return {"name": name, "size": size, "modified": modified, **metadata, "directory": directory}
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
            if (not (some_output_required is True)) or (len(result.stdout) > 0):
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
