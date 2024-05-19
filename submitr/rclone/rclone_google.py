from __future__ import annotations
import io
import json
import os
import requests
from typing import Callable, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string, PRINT
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_config import RCloneConfig, RCloneCredentials
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_utils import cloud_path


class RCloneGoogle(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[GoogleCredentials, RCloneGoogle]] = None,
                 service_account_file: Optional[str] = None,
                 location: Optional[str] = None,  # analagous to AWS region
                 name: Optional[str] = None,
                 bucket: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneGoogle):
            if isinstance(credentials_or_config.credentials, GoogleCredentials):
                credentials = GoogleCredentials(credentials=credentials_or_config.credentials, location=location)
            else:
                # No credentials allowed/works when running on a GCE instance.
                credentials = None
            name = normalize_string(name) or credentials_or_config.name
            bucket = cloud_path.normalize(bucket) or credentials_or_config.bucket
        elif isinstance(credentials_or_config, GoogleCredentials):
            credentials = GoogleCredentials(credentials=credentials_or_config, location=location)
        elif service_account_file := normalize_path(service_account_file):
            credentials = GoogleCredentials(service_account_file=service_account_file, location=location)
        else:
            # No credentials allowed/works when running on a GCE instance.
            credentials = None
        super().__init__(name=name, bucket=bucket, credentials=credentials)
        self._project = None

    @property
    def credentials(self) -> Optional[GoogleCredentials]:
        return super().credentials

    @property
    def config(self) -> dict:
        # The bucket_policy_only=true option indicates that rclone should enforce a bucket-only access policy,
        # meaning that object-level ACLs are not used to control access to objects within the bucket.
        return create_dict(type="google cloud storage",
                           location=self.location,
                           bucket_policy_only=True,
                           service_account_file=self.service_account_file)

    def ping(self) -> bool:
        # Override from RCloneConfig base class because for some reason with this ping command,
        # for which we actually use rclone lsd, we need to specify the project_number for Google.
        args = ["--gcs-project-number", project] if (project := self.project) else None
        with self.config_file() as config_file:
            return RCloneCommands.ping_command(source=f"{self.name}:", config=config_file, args=args)

    @property
    def service_account_file(self) -> Optional[str]:
        return self.credentials.service_account_file if self.credentials else None

    @property
    def location(self) -> Optional[str]:
        return self.credentials.location if self.credentials else None

    @property
    def project(self) -> Optional[str]:
        """
        Returns the Google project name (or number - either) associated with the account identified
        by the service account file (if any) or with the system (e.g. if running on a GCE instance).
        FYI only place needed was for rclone lsd comment which we use as a ping.
        """
        if self._project:
            return self._project
        try:
            if (service_account_file := self.service_account_file) and os.path.isfile(service_account_file):
                with io.open(service_account_file, "r") as f:
                    service_account_json = json.load(f)
                    if isinstance(project := service_account_json.get("project_id"), str) and project:
                        self._project = project
                        return self._project
        except Exception:
            pass
        # If no service account file specified then maybe we are on a GCE instance.
        if project := RCloneGoogle._get_project_name_if_google_compute_engine():
            self._project = project
            return self._project

    def verify_connectivity(self, printf: Optional[Callable] = None) -> bool:
        if not callable(printf):
            printf = print
        if self.ping():
            printf(f"Google Cloud Storage project"
                   f"{f' ({self.project})' if self.project else ''}"
                   f" connectivity appears to be OK ✓")
            if self.bucket_exists() is False:
                printf(f"WARNING: Google Cloud Storage bucket NOT FOUND: {self.bucket}")
            return False
        else:
            printf(f"Google Cloud Storage project"
                   f"{f' ({self.project})' if self.project else ''}"
                   f" connectivity appears to be problematic ✗")
            return True

    def __eq__(self, other: Optional[RCloneGoogle]) -> bool:
        return isinstance(other, RCloneGoogle) and super().__eq__(other)

    def __ne__(self, other: Optional[RCloneGoogle]) -> bool:
        return not self.__eq__(other)

    @staticmethod
    def is_google_compute_engine() -> Optional[str]:
        return RCloneGoogle._get_project_name_if_google_compute_engine() is not None

    @staticmethod
    def _get_project_name_if_google_compute_engine() -> Optional[str]:
        """
        Returns the name of the Google Compute Engine (GCE) that this code is running on,
        if indeed we are running on a GCE instance; otherwise None.
        """
        try:
            # Just FYI this URL also yields more info on a GCE instance (with proper header below):
            # - http://metadata.google.internal/computeMetadata/v1/instance/?alt=json&recursive=true
            # Just FYI this file on a GCE instance contains the instance ID:
            # - /etc/google_instance_id
            # Just FYI this also gets what we are after (though slower):
            # - gcloud config get-value project
            url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
            response = requests.get(url, headers={"Metadata-Flavor": "Google"})
            if (response.status_code == 200) and isinstance(project := response.text, str) and project:
                return project
        except Exception:
            pass
        return None

    @staticmethod
    def from_command_args(rclone_google_source: Optional[str],
                          rclone_google_credentials: Optional[str] = None,
                          rclone_google_location: Optional[str] = None,
                          verify_installation: bool = True,
                          printf: Optional[Callable] = None) -> Optional[RCloneGoogle]:
        """
        Assumed to be called at the start of command-line utility (i.e. e.g. submit-metadata-bundle).
        The rclone_google_source should be the Google bucket (or bucket/sub-folder is also allowed),
        where the files to be copied can be found. The rclone_google_credentials should be the full path
        to the Google (GCP) service account file; or this can be omitted if running on a GCE instance.
        The rclone_google_location is the location (aka region) to be used for the copy.
        """
        if not isinstance(rclone_google_source, str) or not rclone_google_source:
            return None
        if not callable(printf):
            printf = PRINT
        if not RCloneInstallation.verify_installation():
            printf(f"ERROR: Cannot install rclone for some reason (contact support).")
            exit(1)
        if not isinstance(rclone_google_credentials, str):
            rclone_google_credentials = None
        if rclone_google_credentials and not os.path.isfile(rclone_google_credentials):
            printf(f"ERROR: Google service account file does not exist: {rclone_google_credentials}")
            exit(1)
        return RCloneGoogle(service_account_file=rclone_google_credentials,
                            location=rclone_google_location,
                            bucket=rclone_google_source)


class GoogleCredentials(RCloneCredentials):

    def __init__(self,
                 credentials: Optional[GoogleCredentials] = None,
                 service_account_file: Optional[str] = None,
                 location: Optional[str] = None) -> None:

        if isinstance(credentials, GoogleCredentials):
            self._location = credentials.location
            self._service_account_file = credentials.service_account_file
        else:
            self._location = None
            self._service_account_file = None

        if service_account_file := normalize_path(service_account_file, expand_home=True):
            if not os.path.isfile(service_account_file):
                raise Exception(f"GoogleCredentials service account file not found: {service_account_file}")
            self._service_account_file = service_account_file

        if location := normalize_string(location):
            self._location = location

    @property
    def service_account_file(self) -> Optional[str]:
        return self._service_account_file

    @property
    def location(self) -> Optional[str]:
        return self._location

    def __eq__(self, other: Optional[GoogleCredentials]) -> bool:
        return (isinstance(other, GoogleCredentials) and
                (self.location == other.location) and
                (self.service_account_file == other.service_account_file))

    def __ne__(self, other: Optional[GoogleCredentials]) -> bool:
        return not self.__eq__(other)
