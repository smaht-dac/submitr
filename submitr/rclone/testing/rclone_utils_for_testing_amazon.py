from __future__ import annotations
from base64 import b64decode as base64_decode
from boto3 import client as BotoClient
from datetime import timedelta
from json import dumps as dump_json
import os
import requests
from typing import List, Optional, Tuple, Union
from dcicutils.file_utils import are_files_equal, normalize_path
from dcicutils.misc_utils import create_short_uuid, normalize_string
from dcicutils.tmpfile_utils import temporary_file
from dcicutils.datetime_utils import format_datetime
from submitr.rclone.amazon_credentials import AmazonCredentials
from submitr.rclone.rclone_utils import cloud_path
from submitr.utils import DEBUG


# Module with class/functions to aid in integration testing of smaht-submitr rclone support.

class AwsS3:

    # Added 2024-06-01 to accomodate S3-to-S3 copy via rclone when using temporary/session credentials, which
    # require s3:ListBucket on the destination, for some reason. To make this work in real life this requires
    # a change in encoded_core.types.file.external_creds. Note that we will thus allow s3:ListBucket on the
    # destination bucket but for security we will also restrict it to a prefix condition which is exact name
    # of the destination key; note that also with this S3-to-S3 rclone copy situation, for some reason,
    # we cannot use --s3-no-head-object, but rather just --s3-no-head.
    ALLOW_EXTRA_POLICY_FOR_RCLONE_S3_TO_S3 = True

    # Audience for the OIDC token we request when generating scoped temporary credentials via
    # web identity federation; this is what aws-actions/configure-aws-credentials uses by default,
    # and the role's trust policy is expected to condition on it.
    WEB_IDENTITY_AUDIENCE = "sts.amazonaws.com"

    @staticmethod
    def create(*args, **kwargs) -> AwsS3:
        return AwsS3(*args, **kwargs)

    def __init__(self, credentials: AmazonCredentials) -> None:
        self._credentials = credentials
        self._client = None

    @property
    def credentials(self) -> AmazonCredentials:
        return self._credentials

    @property
    def client(self) -> BotoClient:
        if not self._client:
            self._client = self._create_boto_client("s3", self.credentials)
        return self._client

    def upload_file(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file, str) or not file:
                return False
            bucket, key = cloud_path.bucket_and_key(bucket, key, preserve_suffix=True)
            if not bucket:
                return False
            if not key:
                key = os.path.basename(file)
            elif key.endswith(cloud_path.separator):
                key = cloud_path.join(key, os.path.basename(file))
            if kms_key_id := self.credentials.kms_key_id:
                # Note that it is not necessary to use the KMS Key ID when downloading
                # a file uploaded with a KMS Key ID, since this info is stored together
                # with the uploaded file and is used if applicable.
                extra_args = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": kms_key_id}
            else:
                extra_args = None
            self.client.upload_file(file, bucket, key, ExtraArgs=extra_args)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def download_file(self, file: str, bucket: str, key: str, raise_exception: bool = True) -> bool:
        try:
            if not isinstance(file := normalize_path(file), str) or not file:
                return False
            bucket, key = cloud_path.bucket_and_key(bucket, key)
            if not (bucket and key):
                return False
            if os.path.isdir(file):
                if cloud_path.separator in key:
                    key_basename = cloud_path.basename(key)
                    file = os.path.join(file, key_basename)
                else:
                    file = os.path.join(file, key)
            self.client.download_file(bucket, key, file)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def create_folder(self, bucket: str, folder: Optional[str] = None, raise_exception: bool = True) -> bool:
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if folder := cloud_path.normalize(folder):
                bucket = cloud_path.join(bucket, folder)
            bucket, folder = cloud_path.bucket_and_key(bucket)
            if not folder:
                return False
            if not folder.endswith(cloud_path.separator):
                folder += cloud_path.separator
            self.client.put_object(Bucket=bucket, Key=folder)
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def delete_file(self, bucket: str, key: Optional[str] = None,
                    check: bool = False, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return False
        try:
            if not (check is True) or self.file_exists(bucket, key):
                self.client.delete_object(Bucket=bucket, Key=key)
                return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def delete_folders(self, bucket: str, folder: Optional[str] = None, raise_exception: bool = True) -> bool:
        """
        This delete ONLY folders, within the given folder (within the given bucket) not actual keys
        and this is used ONLY for (integration) testing (see test_rclone_support.py), as is this entire
        module, and is only used to CLEANUP after ourselves after each test. We delete ONLY folders for
        safety, as we don't want this to be accidently (due to some errant testing bug) deleting real data.
        Deleting a folder which contains a key does NOT cause the key to be deleted. And so it is up to
        the caller (the integration tests) to explicitly delete any actual files/keys in the folder
        first, and then call this to cleanup the folder and any sub-folders.
        """
        try:
            if not (bucket := cloud_path.normalize(bucket)):
                return False
            if folder := cloud_path.normalize(folder):
                bucket = cloud_path.join(bucket, folder)
            bucket, folder = cloud_path.bucket_and_key(bucket)
            if not folder:
                return False
            if not folder.endswith(cloud_path.separator):
                folder += cloud_path.separator
            client = self.client
            args = {"Prefix": folder}
            while True:
                response = self.client.list_objects_v2(Bucket=bucket, **args)
                if contents := response.get("Contents"):
                    for item in contents:
                        key = item["Key"]
                        client.delete_object(Bucket=bucket, Key=key)
                if not (continuation_token := response.get("NextContinuationToken")):
                    break
                args["ContinuationToken"] = continuation_token
            return True
        except Exception as e:
            if raise_exception is True:
                raise e
        return False

    def bucket_exists(self, bucket: str, raise_exception: bool = True) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def file_exists(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return False
        if self._file_head(bucket, key, raise_exception=raise_exception):
            return True
        return False

    def file_equals(self, file: str, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        try:
            with temporary_file() as temporary_downloaded_file_name:
                if self.download_file(temporary_downloaded_file_name, bucket, key):
                    return are_files_equal(file, temporary_downloaded_file_name)
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return False
            if raise_exception is True:
                raise e
        return False

    def file_size(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[int]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            return file_head.get("ContentLength", None)
        return None

    def file_checksum(self, bucket: str, key: Optional[str] = None,
                      etag: bool = False, raise_exception: bool = True) -> Optional[str]:
        # N.B. When using rclone to copy a file to AWS S3, it writes checksum (md5) for the file
        # to the metadata associated with the target key; it seems to put it in two places, in
        # x-amz-meta-md5chksum in the HTTPHeaders and also in md5chksum in the Metadata; see below.
        # But this is (possibly/plausibly) only for smaller sized files; see rclone.py for more
        # comments on checksums; in any case this code here is only for testing and is fine for
        # our purposes of testing the basic functioning of the rclone copy/copyto commands.
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if etag is not True:
                # TODO: Document exactly where these md5 related metadata might come from.
                if isinstance(md5 := file_head.get("Metadata", {}).get("md5chksum"), str) and md5:
                    return base64_decode(md5).hex()
                elif isinstance(md5 := file_head.get("Metadata", {}).get("md5"), str) and md5:
                    return md5
                md5 = file_head.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-meta-md5chksum")
                if isinstance(md5, str):
                    return base64_decode(md5).hex()
            return file_head.get("ETag").strip("\"")
        return None

    def file_metadata(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[dict]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if isinstance(metadata := file_head.get("Metadata"), dict):
                return metadata
        return None

    def file_kms_encrypted(self, bucket: str, key: Optional[str] = None,
                           kms_key_id: Optional[str] = None, raise_exception: bool = True) -> bool:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if file_kms_key_id := file_head.get("SSEKMSKeyId"):
                if isinstance(kms_key_id, str) and (kms_key_id := kms_key_id.strip()):
                    return True if (kms_key_id in file_kms_key_id) else False
                return True
        return False

    def file_kms_key(self, bucket: str, key: Optional[str] = None, raise_exception: bool = True) -> Optional[str]:
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if not bucket or not key:
            return None
        if file_head := self._file_head(bucket, key, raise_exception=raise_exception):
            if file_kms_key := file_head.get("SSEKMSKeyId"):
                return file_kms_key
        return None

    def list_files(self, bucket: str,
                   prefix: Optional[str] = None,
                   sort: Optional[str] = None,
                   count: Optional[int] = None, offset: Optional[int] = None,
                   raise_exception: bool = True) -> List[str]:
        keys = []
        try:
            args = {"Prefix": prefix} if isinstance(prefix, str) and prefix else {}
            while True:
                response = self.client.list_objects_v2(Bucket=bucket, **args)
                if contents := response.get("Contents"):
                    for item in contents:
                        keys.append({"key": item["Key"],
                                     "modified": format_datetime(item["LastModified"]),
                                     "size": item["Size"]})
                if not (continuation_token := response.get("NextContinuationToken")):
                    break
                args["ContinuationToken"] = continuation_token
            if isinstance(sort, str) and (sort := sort.strip().lower()):
                sort_reverse = sort.startswith("-")
                sort_key = "modified" if "modified" in sort else "name"
                keys = sorted(keys, key=lambda item: item[sort_key], reverse=sort_reverse)
        except Exception as e:
            if raise_exception is True:
                raise e
        if isinstance(offset, int) and (offset >= 0):
            if isinstance(count, int) and (count >= 0):
                keys = keys[offset:offset + count]
            else:
                keys = keys[offset:]
        elif isinstance(count, int) and (count >= 0):
            keys = keys[:count]
        return keys

    def generate_temporary_credentials(self,
                                       bucket: Optional[str] = None, key: Optional[str] = None,
                                       kms_key_id: Optional[str] = None,
                                       duration: Optional[Union[int, timedelta]] = None,
                                       untargeted: bool = False,
                                       readonly: bool = False) -> Optional[AmazonCredentials]:
        """
        Generates and returns temporary AWS credentials. The default duration of validity for
        the generated credential is one hour; this can be overridden by specifying the duration
        argument (which is in seconds). By default the generated credentials will have full S3
        access (AmazonS3FullAccess); but if the readonly argument is True then this will be
        limited to readonly S3 access (AmazonS3ReadOnlyAccess). Passing bucket or bucket/key
        key argument/s will further limit access to just the specified bucket or bucket/key.
        If the given policy argument is {} then it will be populated with the contents of the
        AWS policy used to create the temporary credentials; this is for troubleshooting.

        N.B. For the real use-case WRT Portal see: encoded-core/../types/file.py/external_creds
        """
        statements = []
        bucket, key = cloud_path.bucket_and_key(bucket, key)
        if bucket and untargeted is not True:
            if key:
                resources = [f"arn:aws:s3:::{bucket}/{key}"]
            else:
                raise Exception("Must use both bucket and key for temporary credentials or no bucket at all.")
        else:
            # N.B. Not a real use-case WRT Portal (encoded-core/../types/file.py/external_creds).
            resources = ["*"]
        # For how this policy stuff is defined in smaht-portal for file upload
        # session token creation process see: encoded_core.types.file.external_creds
        actions = ["s3:GetObject"]
        if kms_key_id := normalize_string(kms_key_id):
            actions_kms = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
            if not (account_number := self.credentials.account_number):
                # Fail clearly here; otherwise the account number lands in the resource ARN as
                # "None" and AWS rejects the whole request with a confusing MalformedPolicyDocument.
                raise Exception("Cannot determine the AWS account number needed for the KMS"
                                " resource ARN of the temporary credentials policy.")
            resource_kms = f"arn:aws:kms:{self.credentials.region}:{account_number}:key/{kms_key_id}"
            statements.append({"Effect": "Allow", "Action": actions_kms, "Resource": resource_kms})
        if not (readonly is True):
            # Note the s3:CreateBucket is specifically required (for some reason) by rclone (but not for plain
            # aws), unless these temporary (session) credentials are targetted specifically for the bucket/key.
            # actions = actions + ["s3:PutObject", "s3:DeleteObject", "s3:CreateBucket"]
            actions = actions + ["s3:PutObject"]
        statements.append({"Effect": "Allow", "Action": actions, "Resource": resources})
        if AwsS3.ALLOW_EXTRA_POLICY_FOR_RCLONE_S3_TO_S3:
            if isinstance(bucket, str) and (bucket := bucket.strip()) and isinstance(key, str) and (key := key.strip()):
                if untargeted is not True:
                    statements.append({"Effect": "Allow",
                                       "Action": "s3:ListBucket",
                                       "Resource": f"arn:aws:s3:::{bucket}",
                                       "Condition": {"StringLike": {"s3:prefix": [f"{key}"]}}})  # NEW
                else:
                    # N.B. Not a real use-case WRT Portal (encoded-core/../types/file.py/external_creds).
                    statements.append({"Effect": "Allow",
                                       "Action": "s3:ListBucket",
                                       "Resource": f"arn:aws:s3:::{bucket}"})
        policy = {"Version": "2012-10-17", "Statement": statements}
        DEBUG(f"TEMPORARY-CREDENTIALS-POLICY: {policy}")
        temporary_credentials = AwsS3._generate_temporary_credentials(generating_credentials=self.credentials,
                                                                      policy=policy,
                                                                      kms_key_id=kms_key_id,
                                                                      duration=duration)
        # For troubleshooting squirrel away the policy in the credentials; harmless in general.
        setattr(temporary_credentials, "_policy", policy)
        return temporary_credentials

    @staticmethod
    def _generate_temporary_credentials(generating_credentials: AmazonCredentials,
                                        policy: Optional[dict] = None,
                                        kms_key_id: Optional[str] = None,
                                        duration: Optional[Union[int, timedelta]] = None,
                                        raise_exception: bool = True) -> Optional[AmazonCredentials]:
        """
        Generates and returns temporary AWS credentials. The default duration of validity
        for the generated credential is one hour; this can be overridden by specifying
        the duration argument (which is in seconds). By default the generated credentials
        will have the same permissions as the given generating_credentials; this can be
        changed by passing in an AWS policy object (dictionary).
        """
        DURATION_DEFAULT = 60 * 60  # One hour
        DURATION_MIN = 60 * 15  # Fifteen minutes
        DURATION_MAX = 60 * 60 * 12  # Twelve hours

        if isinstance(duration, timedelta):
            duration = duration.total_seconds()
        if (not isinstance(duration, int)) or (duration <= 0):
            duration = DURATION_DEFAULT
        elif duration < DURATION_MIN:
            duration = DURATION_MIN
        elif duration > DURATION_MAX:
            duration = DURATION_MAX

        policy = dump_json(policy) if isinstance(policy, dict) else None

        name = f"test.smaht.submitr.{create_short_uuid(length=12)}"
        try:
            sts = AwsS3._create_boto_client("sts", generating_credentials)
            if web_identity := AwsS3._obtain_web_identity(generating_credentials):
                # We are authenticated via web identity federation (e.g. GitHub OIDC), so the
                # generating credentials are a role session, and a role session cannot call
                # sts:GetFederationToken -- AWS only permits an IAM user or the account root user
                # to call it. AssumeRoleWithWebIdentity takes the same kind of inline session
                # policy and gives the same result (permissions are the intersection of the role's
                # own policy and the session policy), and requires no caller credentials at all.
                role_arn, web_identity_token = web_identity
                arguments = {"RoleArn": role_arn,
                             "RoleSessionName": name,
                             "WebIdentityToken": web_identity_token,
                             # A role session cannot outlive the role's maximum session duration,
                             # which defaults to one hour; asking for more fails outright.
                             "DurationSeconds": min(duration, DURATION_DEFAULT)}
                if policy:
                    arguments["Policy"] = policy
                response = sts.assume_role_with_web_identity(**arguments)
            else:
                response = sts.get_federation_token(Name=name, Policy=policy, DurationSeconds=duration)
            if isinstance(credentials := response.get("Credentials"), dict):
                return AmazonCredentials(access_key_id=credentials.get("AccessKeyId"),
                                         secret_access_key=credentials.get("SecretAccessKey"),
                                         session_token=credentials.get("SessionToken"),
                                         kms_key_id=kms_key_id)
        except Exception as e:
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def is_web_identity_configured() -> bool:
        """
        Returns True iff this environment is setup to authenticate to AWS via web identity
        federation, i.e. iff an OIDC token can be obtained for us. Deliberately cheap (environment
        variables only, no I/O) as this is also used to decide what shape the ambient credentials
        are expected to have.
        """
        return bool((os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL") and
                     os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")) or
                    os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE"))

    @staticmethod
    def _obtain_web_identity(generating_credentials: AmazonCredentials) -> Optional[Tuple[str, str]]:
        """
        Returns a (role_arn, web_identity_token) tuple for generating temporary credentials via
        sts:AssumeRoleWithWebIdentity, or None if web identity federation is not usable here (e.g.
        for a normal command-line user authenticated with an IAM user's long-term access keys, in
        which case the sts:GetFederationToken path is used instead).
        """
        if not AwsS3.is_web_identity_configured():
            return None
        if not (role_arn := AwsS3._obtain_web_identity_role_arn(generating_credentials)):
            DEBUG("WEB-IDENTITY: no role ARN can be determined; not using web identity federation.")
            return None
        if not (web_identity_token := AwsS3._obtain_web_identity_token()):
            DEBUG("WEB-IDENTITY: no token can be obtained; not using web identity federation.")
            return None
        return role_arn, web_identity_token

    @staticmethod
    def _obtain_web_identity_role_arn(generating_credentials: AmazonCredentials) -> Optional[str]:
        # Prefer being told explicitly; see .github/workflows/main-integration-tests.yml
        if role_arn := normalize_string(os.environ.get("AWS_OIDC_ROLE_ARN")):
            return role_arn
        # Otherwise derive it from whoever we currently are, turning e.g.
        # arn:aws:sts::1234:assumed-role/some-role/some-session into
        # arn:aws:iam::1234:role/some-role. N.B. this does not round-trip for a role which was
        # created with a path, as the assumed-role ARN does not include it.
        try:
            sts = AwsS3._create_boto_client("sts", generating_credentials)
            arn = sts.get_caller_identity().get("Arn") or ""
            if len(parts := arn.split(":")) == 6 and parts[2] == "sts":
                if (resource := parts[5]).startswith("assumed-role/"):
                    if role_name := resource.split("/")[1:2]:
                        return f"arn:aws:iam::{parts[4]}:role/{role_name[0]}"
        except Exception as e:
            DEBUG(f"WEB-IDENTITY: cannot derive role ARN: {e!r}")
        return None

    @staticmethod
    def _obtain_web_identity_token() -> Optional[str]:
        # N.B. A fresh token is fetched for each call rather than cached; these are short-lived
        # and STS rejects an expired one (ExpiredToken/InvalidIdentityToken).
        request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
        request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
        if request_url and request_token:
            # Running within GitHub Actions, with the id-token: write permission granted.
            try:
                response = requests.get(f"{request_url}&audience={AwsS3.WEB_IDENTITY_AUDIENCE}",
                                        headers={"Authorization": f"Bearer {request_token}"},
                                        timeout=30)
                response.raise_for_status()
                if token := normalize_string(response.json().get("value")):
                    return token
            except Exception as e:
                DEBUG(f"WEB-IDENTITY: cannot fetch OIDC token from GitHub: {e!r}")
        if token_file := normalize_path(os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE"), expand_home=True):
            # Conventional location for a projected OIDC token; e.g. on EKS.
            try:
                with open(token_file) as f:
                    if token := normalize_string(f.read()):
                        return token
            except Exception as e:
                DEBUG(f"WEB-IDENTITY: cannot read token file {token_file}: {e!r}")
        return None

    def _file_head(self, bucket: str, key: str, raise_exception: bool = True) -> Optional[dict]:
        try:
            return self.client.head_object(Bucket=bucket, Key=key)
        except Exception as e:
            if hasattr(e, "response") and e.response.get("Error", {}).get("Code") == "404":
                return None
            if raise_exception is True:
                raise e
        return None

    @staticmethod
    def _create_boto_client(boto_service: str, credentials: AmazonCredentials) -> BotoClient:
        return BotoClient(
            boto_service,
            region_name=credentials.region,
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token)
