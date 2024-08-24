# import argparse
import pytest
import tempfile
from unittest import mock
from .. import submission as submission_module
from ..submission import DEFAULT_INGESTION_TYPE
from ..scripts.submit_metadata_bundle import (
    main as submit_metadata_bundle_main
)
from ..scripts import submit_metadata_bundle as submit_metadata_bundle_module
from .testing_helpers import system_exit_expected, argparse_errors_muffled


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_submit_metadata_bundle_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):

        output = []
        with argparse_errors_muffled():
            with mock.patch.object(submit_metadata_bundle_module,
                                   "submit_any_ingestion") as mock_submit_any_ingestion:
                with mock.patch.object(submission_module, "print") as mock_print:
                    mock_print.side_effect = lambda *args: output.append(" ".join(args))
                    with system_exit_expected(exit_code=expect_exit_code):
                        submit_metadata_bundle_main(args_in)
                        raise AssertionError(  # pragma: no cover
                            "submit_metadata_bundle_main should not exit normally.")
                    assert mock_submit_any_ingestion.call_count == (1 if expect_called else 0)
                    if expect_called:
                        # New in Python 3.12: Default arguments expected to be here too for assert_called_with.
                        expect_call_args = {
                            "ingestion_filename": expect_call_args["ingestion_filename"],
                            "ingestion_type": expect_call_args.get("ingestion_type"),
                            "env": expect_call_args.get("env", None),
                            "env_from_env": False,
                            "keys_file": None,
                            "server": expect_call_args.get("server"),
                            "consortium": None,
                            "submission_center": None,
                            "add_submission_center": None,
                            "no_query": expect_call_args.get("no_query"),
                            "subfolders": True if "--directory" in args_in else False,
                            "app": None,
                            "submission_protocol": "upload",
                            "upload_folder": expect_call_args.get("upload_folder", None),
                            "show_details": False,
                            "post_only": False,
                            "patch_only": False,
                            "submit": False,
                            "submit_update": False,
                            "rclone_google": None,
                            "validate_local_only": False,
                            "validate_remote_only": False,
                            "validate_local_skip": False,
                            "validate_remote_skip": False,
                            "noanalyze": False,
                            "nouploads": False,
                            "json_only": False,
                            "ref_nocache": False,
                            "verbose_json": False,
                            "merge": False,
                            "verbose": False,
                            "noversion": False,
                            "noprogress": False,
                            "output_file": False,
                            "timeout": None,
                            "debug": False,
                            "debug_sleep": False
                        }
                        mock_submit_any_ingestion.assert_called_with(**expect_call_args)
                    assert output == []

    some_file = _create_some_temporary_file()
    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=[some_file], expect_exit_code=0, expect_called=True, expect_call_args={
        'ingestion_filename': some_file,
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': None,
        'server': None,
        # 'institution': None,
        # 'project': None,
        'validate_remote_only': False,
        'upload_folder': None,
        'no_query': False,
        'subfolders': False,
    })
    expect_call_args = {
        'ingestion_filename': some_file,
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        # 'institution': "some-institution",
        # 'project': "some-project",
        'validate_remote_only': True,
        'upload_folder': None,
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env",  # "--institution", "some-institution",
                     "--server", "some-server", "--validate",  # "-p", "some-project",
                     some_file],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=[some_file, "--env", "some-env",  # "--institution", "some-institution",
                     "--server", "some-server"],  # , "--project", "some-project"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': some_file,
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        # 'institution': "some-institution",
        # 'project': "some-project",
        'validate_remote_only': False,
        'upload_folder': 'a-folder',
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env",
                     # "--institution", "some-institution",
                     "--server", "some-server",
                     # "-p", "some-project",
                     '--directory', 'a-folder',
                     some_file],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=[some_file,
                     "--env", "some-env",
                     # "--institution", "some-institution",
                     "--server", "some-server",
                     # "--project", "some-project",
                     '--directory', 'a-folder'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': some_file,
        'ingestion_type': 'simulated_bundle',
        'env': "some-env",
        'server': "some-server",
        # 'institution': "some-institution",
        # 'project': "some-project",
        'validate_remote_only': True,
        'upload_folder': 'a-folder',
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env",
                     # "--institution", "some-institution",
                     "--server", "some-server",
                     "--validate",
                     # "-p", "some-project",
                     '--directory', 'a-folder',
                     '--ingestion_type', 'simulated_bundle',
                     some_file],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=[some_file,
                     "--env", "some-env",
                     # "--institution", "some-institution",
                     "--server", "some-server",
                     # "--project", "some-project",
                     '--directory', 'a-folder',
                     '--ingestion_type', 'simulated_bundle'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': some_file,
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        # 'institution': "some-institution",
        # 'project': "some-project",
        'validate_remote_only': True,
        'upload_folder': None,
        'no_query': True,
        'subfolders': True,
    }
    test_it(args_in=["--env", "some-env",  # "--institution", "some-institution",
                     "--server", "some-server", "--validate",  # "-p", "some-project",
                     some_file, '--yes'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["--env", "some-env",  # "--institution", "some-institution",
                     "--server", "some-server", "--validate",  # "-p", "some-project",
                     some_file, '--yes'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)


def _create_some_temporary_file() -> str:
    some_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        some_file.write(b"")
    finally:
        some_file.close()
    return some_file.name
