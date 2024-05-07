from __future__ import annotations
import io
import json
import os
import requests
import subprocess
from typing import Callable, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string
from submitr.rclone.rclone_config import RCloneConfig, RCloneCredentials
from submitr.rclone.rclone_installation import RCloneInstallation
from submitr.rclone.rclone_utils import cloud_path


class RCloneConfigGoogle(RCloneConfig):

    def __init__(self,
                 credentials_or_config: Optional[Union[GoogleCredentials, RCloneConfigGoogle]] = None,
                 location: Optional[str] = None,
                 service_account_file: Optional[str] = None,
                 name: Optional[str] = None,
                 path: Optional[str] = None) -> None:

        if isinstance(credentials_or_config, RCloneConfigGoogle):
            name = normalize_string(name) or credentials_or_config.name
            path = cloud_path.normalize(path) or credentials_or_config.path
            credentials = credentials_or_config.credentials
        elif isinstance(credentials_or_config, GoogleCredentials):
            credentials = credentials_or_config
        else:
            credentials = None
        credentials = GoogleCredentials(credentials=credentials,
                                        location=location,
                                        service_account_file=service_account_file)
        super().__init__(name=name, path=path, credentials=credentials)
        self._project = None

    @property
    def credentials(self) -> GoogleCredentials:
        return super().credentials

    @credentials.setter
    def credentials(self, value: GoogleCredentials) -> None:
        if isinstance(value, GoogleCredentials):
            super().credentials = value

    @property
    def config(self) -> dict:
        # The bucket_policy_only=true option indicates that rclone should enforce a bucket-only access policy,
        # meaning that object-level ACLs are not used to control access to objects within the bucket.
        return create_dict(type="google cloud storage",
                           location=self.location,
                           bucket_policy_only=True,
                           service_account_file=self.service_account_file)

    @property
    def location(self) -> Optional[str]:
        return self._credentials.location

    @location.setter
    def location(self, value: str) -> None:
        self._credentials.location = value

    @property
    def service_account_file(self) -> Optional[str]:
        return self._credentials.service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> None:
        self._credentials.service_account_file = value

    @property
    def project(self) -> Optional[str]:
        """
        Returns the Google project name (or number associated with the account identifid
        by the service account file (if any) or with the system (e.g. if on a GCE instance).
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
        try:
            # If no service account file specified then maybe we are on a GCE instance.
            command = "gcloud config get-value project".split()
            result = subprocess.run(command, capture_output=True)
            if (result.returncode == 0) and isinstance(project := result.stdout, str) and project:
                self._project = project
                return self._project
        except Exception:
            pass
        try:
            # If for some reason the gcloud command did not work try via URL.
            url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
            response = requests.get(url, headers={"Metadata-Flavor": "Google"})
            if (response.status_code == 200) and isinstance(project := response.text, str) and project:
                self._project = project
                return self._project
        except Exception:
            pass
        return None

    @staticmethod
    def is_google_compute_engine() -> Optional[str]:
        try:
            # Just FYI the file /etc/google_instance_id on a GCE contains the instance ID.
            url = "http://metadata.google.internal/computeMetadata/v1/instance/?alt=json&recursive=true"
            response = requests.get(url, headers={"Metadata-Flavor": "Google"})
            if (response.status_code == 200) and isinstance(instance := response.json().get("name"), str):
                return instance
        except Exception:
            pass
        return None

    @staticmethod
    def create_from_args(rclone_google_source: Optional[str],
                         rclone_google_credentials: Optional[str] = None,
                         verify_installation: bool = False,
                         verbose: bool = False,
                         printf: Optional[Callable] = None) -> Optional[RCloneConfigGoogle]:
        if not isinstance(rclone_google_source, str) or not rclone_google_source:
            return None
        if not RCloneInstallation.verify_installation(verbose=verbose):
            exit(1)
        if not isinstance(rclone_google_credentials, str):
            rclone_google_credentials = None
        if not callable(printf):
            printf = print
        if rclone_google_credentials and not os.path.isfile(rclone_google_credentials):
            printf(f"ERROR: Google service account file does not exist: {rclone_google_credentials}")
            return None
        # TODO: Allow "location" to be passed in (?); not in service account file.
        rclone_google_config = RCloneConfigGoogle(service_account_file=rclone_google_credentials,
                                                  path=rclone_google_source)
        return rclone_google_config

    def verify_connectivity(self, verbose: bool = False, printf: Optional[Callable] = None) -> bool:
        if not callable(printf):
            printf = print
        if not self.ping():
            printf(f"WARNING: Google Cloud Storage project"
                   f"{f' ({self.project})' if self.project else ''} cannot be accessed.")
            return False
        elif verbose:
            printf(f"Google Cloud Storage project ({self.project}) connectivity: OK")
        return True

    def __eq__(self, other: RCloneConfigGoogle) -> bool:
        return isinstance(other, RCloneConfigGoogle) and super().__eq__(other)

    def __ne__(self, other: RCloneConfigGoogle) -> bool:
        return not self.__eq__(other)


class GoogleCredentials(RCloneCredentials):

    @staticmethod
    def create(*args, **kwargs) -> GoogleCredentials:
        return GoogleCredentials(*args, **kwargs)

    def __init__(self,
                 credentials: Optional[GoogleCredentials] = None,
                 location: Optional[str] = None,
                 service_account_file: Optional[str] = None) -> None:

        if isinstance(credentials, GoogleCredentials):
            self._location = credentials.location
            self._service_account_file = credentials.service_account_file
        else:
            self._location = None
            self._service_account_file = None

        if location := normalize_string(location):
            self._location = location
        if service_account_file := normalize_path(service_account_file):
            if not os.path.isfile(service_account_file):
                raise Exception(f"GCS service account file not found: {service_account_file}")
            self._service_account_file = service_account_file

    @property
    def location(self) -> Optional[str]:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if (value := normalize_string(value)) is not None:
            self._location = value or None

    @property
    def service_account_file(self) -> Optional[str]:
        return self._service_account_file

    @service_account_file.setter
    def service_account_file(self, value: str) -> None:
        if (value := normalize_path(value)) is not None:
            self._service_account_file = value or None

    def __eq__(self, other: GoogleCredentials) -> bool:
        return ((self.location == other.location) and
                (self.service_account_file == other.service_account_file))

    def __ne__(self, other: GoogleCredentials) -> bool:
        return not self.__eq__(other)
