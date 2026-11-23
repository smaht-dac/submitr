from types import SimpleNamespace
from unittest import mock

import pytest
from dcicutils.structured_data import Portal

from submitr.file_for_upload import FileForUpload
from submitr.filename_preflight import (
    FilenameCollisionError,
    check_portal_filename_collision,
    duplicate_upload_filename_errors,
    portal_filename_collision_errors,
)
from submitr import submission, submission_uploads


class FakePortal:
    def __init__(self, records=None, file_schemas=None):
        self.records = records or []
        self.file_schemas = file_schemas or {"File", "OtherFile"}

    def is_schema_file_type(self, schema):
        return schema in self.file_schemas

    def get(self, url):
        return SimpleNamespace(status_code=200, json=lambda: {"@graph": self.records})

    def get_metadata(self, uuid, raise_exception=False):
        return next((record for record in self.records if record.get("uuid") == uuid), None)


def test_duplicate_upload_filenames_within_and_across_sheets():
    data = {
        "File": [{"filename": "first/reads.fastq"}, {"filename": "reads.fastq"}],
        "OtherFile": [{"filename": "third/reads.fastq"}],
    }

    errors = duplicate_upload_filename_errors(data, FakePortal())

    assert len(errors) == 1
    assert "File row 2" in errors[0]
    assert "File row 3" in errors[0]
    assert "OtherFile row 2" in errors[0]


def test_duplicate_upload_filename_for_same_item_is_allowed():
    data = {
        "File": [
            {"uuid": "file-1", "filename": "first/reads.fastq"},
            {"uuid": "file-1", "filename": "reads.fastq"},
        ]
    }

    assert duplicate_upload_filename_errors(data, FakePortal()) == []


def test_existing_same_center_filename_conflict():
    portal = FakePortal([{
        "uuid": "other-file",
        "filename": "reads.fastq",
        "submission_centers": [{"identifier": "center-a"}],
    }])
    file = FileForUpload({"filename": "reads.fastq", "uuid": "new-file"})

    with pytest.raises(FilenameCollisionError, match="reads.fastq"):
        check_portal_filename_collision(file, portal, ["center-a"])


def test_different_center_and_same_item_updates_are_allowed():
    different_center = FakePortal([{
        "uuid": "other-file",
        "filename": "reads.fastq",
        "submission_centers": [{"identifier": "center-b"}],
    }])
    current_item = FakePortal([{
        "uuid": "current-file",
        "filename": "reads.fastq",
        "submission_centers": [{"identifier": "center-a"}],
    }])

    check_portal_filename_collision(
        FileForUpload({"filename": "reads.fastq", "uuid": "new-file"}),
        different_center,
        ["center-a"],
    )
    check_portal_filename_collision(
        FileForUpload({"filename": "reads.fastq", "uuid": "current-file"}),
        current_item,
        ["center-a"],
    )


def test_filename_collision_check_precedes_patch_and_upload():
    portal = Portal({"key": "key", "secret": "secret", "server": "http://localhost"})
    file = FileForUpload("reads.fastq")
    file._uuid = None
    events = []

    def collision(*args, **kwargs):
        events.append("collision")

    def credentials(*args, **kwargs):
        events.append("credentials")
        return "s3://bucket/key", {}, None

    def upload(*args, **kwargs):
        events.append("bytes")

    with mock.patch.object(submission_uploads, "check_portal_filename_collision", side_effect=collision), \
         mock.patch.object(submission_uploads, "generate_credentials_for_upload", side_effect=credentials), \
         mock.patch.object(submission_uploads, "upload_file_to_aws_s3", side_effect=upload):
        submission_uploads.upload_file(file, portal, submission_centers=["center-a"])

    assert events == ["collision", "credentials", "bytes"]


def test_portal_filename_collision_errors_scope_and_same_item():
    portal = FakePortal([{
        "uuid": "existing-file",
        "submitted_id": "TEST_FILE_EXISTING",
        "filename": "reads.fastq",
        "submission_centers": [{"@id": "/submission-centers/center-a/"}],
    }])
    data = {"File": [
        {"submitted_id": "TEST_FILE_NEW", "filename": "dir/reads.fastq"},
        {"submitted_id": "TEST_FILE_EXISTING", "filename": "reads.fastq"},
    ]}

    errors = portal_filename_collision_errors(data, portal, ["/submission-centers/center-a/"])

    assert len(errors) == 1
    assert errors[0].startswith("File row 2: ")
    assert "existing-file" in errors[0]
    assert portal_filename_collision_errors(data, portal, ["/submission-centers/center-b/"]) == []


def test_portal_filename_collision_aborts_before_metadata_submission():
    portal = FakePortal([{
        "uuid": "existing-file",
        "filename": "reads.fastq",
        "submission_centers": [{"@id": "/submission-centers/center-a/"}],
    }])
    portal.ping = lambda: True
    portal.key = {}
    portal.key_pair = ("key", "secret")
    portal.server = "http://localhost"
    portal.app = "smaht"
    structured_data = SimpleNamespace(
        data={"File": [{"submitted_id": "TEST_FILE_NEW", "filename": "reads.fastq"}]}
    )
    app_args = {"consortia": ["/consortia/smaht/"],
                "submission_centers": ["/submission-centers/center-a/"]}

    with mock.patch.object(submission, "_define_portal", return_value=portal), \
         mock.patch.object(submission, "_resolve_app_args", return_value=app_args), \
         mock.patch.object(submission, "_get_user_record", return_value={}), \
         mock.patch.object(submission, "get_metadata_bundles_bucket_from_health_path", return_value="bucket"), \
         mock.patch.object(submission, "_do_app_arg_defaulting", return_value=True), \
         mock.patch.object(submission, "_get_submission_centers", return_value=[]), \
         mock.patch.object(submission, "_validate_locally", return_value=structured_data), \
         mock.patch.object(submission, "yes_or_no", return_value=True), \
         mock.patch.object(submission, "_initiate_server_ingestion_process") as initiate:
        with pytest.raises(SystemExit) as exc:
            submission.submit_any_ingestion(
                "workbook.json", ingestion_type="metadata_bundle", server="http://localhost",
                env=None, submit=True, validate_remote_skip=True, noversion=True,
            )

    assert exc.value.code == 1
    initiate.assert_not_called()
