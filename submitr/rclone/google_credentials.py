from __future__ import annotations
from google.cloud.storage import Client as GcsClient
import os
import requests
from typing import Optional
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import normalize_string


class GoogleCredentials:

    def __init__(self,
                 service_account_file: Optional[str] = None,
                 location: Optional[str] = None) -> None:

        self._location = None
        self._service_account_file = None
        if service_account_file := normalize_path(service_account_file, expand_home=True):
            if not os.path.isfile(service_account_file):
                raise Exception(f"Google service account file not found: {service_account_file}")
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

    def ping(self) -> bool:
        try:
            if GoogleCredentials.is_google_compute_engine():
                client = GcsClient()
            else:
                client = GcsClient.from_service_account_json(self.service_account_file)
            _ = list(client.list_buckets())
            return True
        except Exception:
            return False

    @staticmethod
    def obtain(service_account_file: Optional[str] = None,
               location: Optional[str] = None,
               ignore_environment: bool = False) -> Optional[GoogleCredentials]:

        if service_account_file := normalize_path(service_account_file, expand_home=True):
            if not os.path.isfile(service_account_file):
                return None
        elif ((ignore_environment is not True) and
              (service_account_file :=
               normalize_path(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"), expand_home=True))):
            if not os.path.isfile(service_account_file):
                return None
        else:
            return None
        return GoogleCredentials(service_account_file=service_account_file, location=location)

    @staticmethod
    def is_google_compute_engine() -> Optional[str]:
        return GoogleCredentials._get_project_name_if_google_compute_engine() is not None

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
