from __future__ import annotations
import io
import json
import os
from typing import Callable, Optional, Union
from dcicutils.file_utils import normalize_path
from dcicutils.misc_utils import create_dict, normalize_string, PRINT
from submitr.rclone.google_credentials import GoogleCredentials
from submitr.rclone.rclone_commands import RCloneCommands
from submitr.rclone.rclone_store import RCloneStore
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import chars


@RCloneStore.register
class RCloneGoogle(RCloneStore):

    prefix = cloud_path.google_prefix
    proper_name = "GCS"
    proper_name_title = "Google Cloud Storage"
    proper_name_label = "google-cloud-storage"

    def __init__(self,
                 credentials_or_config: Optional[Union[GoogleCredentials, RCloneGoogle, str]] = None,
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
        elif (isinstance(credentials_or_config, str) and
              (service_account_file := normalize_path(credentials_or_config, expand_home=True))):
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
        # Override from RCloneStore base class because for some reason with this ping command,
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
        if project := GoogleCredentials._get_project_name_if_google_compute_engine():
            self._project = project
            return self._project

    def __eq__(self, other: Optional[RCloneGoogle]) -> bool:
        return isinstance(other, RCloneGoogle) and super().__eq__(other)

    def __ne__(self, other: Optional[RCloneGoogle]) -> bool:
        return not self.__eq__(other)

    @staticmethod
    def is_google_compute_engine() -> Optional[str]:
        return GoogleCredentials.is_google_compute_engine()

    def verify_connectivity(self, usage: Optional[Callable] = None, printf: Optional[Callable] = None) -> None:
        if not callable(usage):
            usage = print
        if not callable(printf):
            printf = print
        if self.ping():
            printf(f"{self.proper_name_title}"
                   f"{f' (project: {self.project})' if self.project else ''}"
                   f" connectivity appears to be OK {chars.check}")
            if self.bucket_exists() is False:
                printf(f"WARNING: Google Cloud Storage bucket/path NOT FOUND or EMPTY: {self.bucket}")
        else:
            usage(f"{self.proper_name_title}"
                  f"{f' (project: {self.project})' if self.project else ''}"
                  f" connectivity appears to be problematic {chars.xmark}")

    @classmethod
    def from_args(cls,
                  cloud_source: str,
                  cloud_credentials: Optional[str],
                  cloud_location: Optional[str],
                  verify_connectivity: bool = True,
                  usage: Optional[Callable] = None,
                  printf: Optional[Callable] = None) -> Optional[RCloneGoogle]:
        """
        Assumed to be called at the start of command-line utility (i.e. e.g. submit-metadata-bundle).
        The cloud_source should be the Google bucket (or bucket/sub-folder is also allowed),
        where the files to be copied can be found. The cloud_credentials should be the full path
        to the Google (GCP) service account file; or this can be omitted if running on a GCE instance.
        The cloud_location is the location (aka region) to be used for the copy.
        """
        if not (isinstance(cloud_source, str) and cloud_source):  # should never happen
            return None
        if not callable(printf):
            printf = PRINT
        if not (cloud_credentials := normalize_path(cloud_credentials, expand_home=True)):
            if not (cloud_credentials := normalize_path(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
                                                        expand_home=True)):
                printf(f"ERROR: No Google service account file specified.")
                return None
        if not os.path.isfile(cloud_credentials):
            printf(f"ERROR: Google service account file does not exist: {cloud_credentials}")
            exit(1)
        cloud_store = RCloneGoogle(cloud_credentials, location=cloud_location, bucket=cloud_source)
        if verify_connectivity is True:
            cloud_store.verify_connectivity(usage=usage, printf=printf)
        return cloud_store
