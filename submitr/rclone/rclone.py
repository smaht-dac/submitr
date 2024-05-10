from contextlib import contextmanager
import os
from shutil import copy as copy_file
from typing import Callable, List, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.tmpfile_utils import create_temporary_file_name, temporary_file
from submitr.rclone.rclone_config import RCloneConfig
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_utils import cloud_path


class RClone(RCloneCommands, RCloneInstallation):

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
            RCloneConfig.write_config_file_lines(temporary_config_file_name, self.config_lines)
            if persist is True:
                pass
                # This is just for dryrun for testing/troubleshooting.
                persistent_config_file_name = create_temporary_file_name(suffix=".conf")
                copy_file(temporary_config_file_name, persistent_config_file_name)
                yield persistent_config_file_name
            else:
                yield temporary_config_file_name

    def copy(self, source: str, destination: Optional[str] = None, progress: Optional[Callable] = None,
             nodirectories: bool = False, dryrun: bool = False, copyto: bool = True,
             raise_exception: bool = True) -> Union[bool, str]:
        """
        Uses rclone to copy the given source file to the given destination. All manner of variation is
        encapsulated within this simple statement. Depends on whether or not a source and/or destination
        configuration (RCloneConfig) has been specified and whether or not a bucket is specified in the
        that configuration et cetera. If no configuration is specified then we assume the local file
        system is the source and/or destination. TODO: Expand on these notes.

        If self.source and/or self.destination is None then it means the the source and/or
        destination arguments here refer to local files; i.e. when no RCloneConfig is
        specified we assume the (degenerate) case of local file.

        Note the we assume (by default) that the destination path is to a *file*, not a "directory" (such
        as they are in cloud storage); and we therefore use the rclone 'copyto' command rather than 'copy'.
        This keeps it simple (otherwise it gets surprisingly confusing with 'copy' WRT whether or not the
        destination is a file or "directory" et cetera); and in any case this is our only actual use-case.
        Can force to use 'copy' by passing False as the copyto argument.
        """
        # Just FYI WRT copy/copyto:
        # - Using 'copy' when the cloud destination is a file gives error: "is a file not a directory".
        # - Using 'copyto' when the cloud destination is a "directory" creates a *file* of that name;
        #   along side the "directory" of the same name (which is odd and alomst certainly undesireble).
        # - So we want to do if is_directory(destination) then 'copy' else 'copyto'.
        if isinstance(destination_config := self.destination, RCloneConfig):
            # Here a destination cloud configuration has been defined for this RClone object;
            # meaning we are copying to some cloud destination (and not to a local file destination).
            if not (destination := destination_config.path(destination)):
                raise Exception(f"No cloud destination specified.")
            if isinstance(source_config := self.source, RCloneConfig):
                # Here both a source and destination cloud configuration have been defined for this RClone
                # object; meaning we are copying from one cloud source to another cloud destination; i.e. e.g.
                # from either Amazon S3 or Google Cloud Storage to either Amazon S3 or Google Cloud Storage.
                if not (source := source_config.path(source)):
                    raise Exception(f"No cloud source specified.")
                with self.config_file(persist=True or dryrun is True) as source_and_destination_config_file:  # noqa
                    command_args = [f"{source_config.name}:{source}", f"{destination_config.name}:{destination}"]
                    return RCloneCommands.copy_command(command_args,
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
                    return RCloneCommands.copy_command(command_args,
                                                       config=destination_config_file,
                                                       copyto=copyto, progress=progress, dryrun=dryrun)
        elif isinstance(source_config := self.source, RCloneConfig):
            # Here only a source cloud configuration has been defined for this RClone object;
            # meaning we are copying from some cloud source to a local file destination;
            # i.e. e.g. from either Amazon S3 or Google Cloud Storage to a local file.
            if source_config.bucket:
                # A path/bucket in the source RCloneConfig is nothing more than an alternative
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
                return RCloneCommands.copy_command(command_args,
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
            return RCloneCommands.copy_command(command_args, copyto=copyto, progress=progress,
                                               dryrun=dryrun, raise_exception=raise_exception)
