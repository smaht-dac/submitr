import pytest

from dcicutils.creds_utils import CGAPKeyManager
from unittest import mock
from .. import submission as submission_module
from ..submission import DEFAULT_INGESTION_TYPE
from ..scripts.submit_metadata_bundle import main as submit_metadata_bundle_main
from ..scripts import submit_metadata_bundle as submit_metadata_bundle_module
from .testing_helpers import system_exit_expected, argparse_errors_muffled


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_submit_metadata_bundle_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):

        output = []
        with argparse_errors_muffled():
            with CGAPKeyManager.default_keys_file_for_testing(keyfile):
                with mock.patch.object(submit_metadata_bundle_module,
                                       "submit_any_ingestion") as mock_submit_any_ingestion:
                    with mock.patch.object(submission_module, "print") as mock_print:
                        mock_print.side_effect = lambda *args: output.append(" ".join(args))
                        with system_exit_expected(exit_code=expect_exit_code):
                            key_manager = CGAPKeyManager()
                            if keyfile:
                                assert key_manager.keys_file == keyfile
                            assert key_manager.keys_file == (keyfile or key_manager.KEYS_FILE)
                            submit_metadata_bundle_main(args_in)
                            raise AssertionError(  # pragma: no cover
                                "submit_metadata_bundle_main should not exit normally.")
                        assert mock_submit_any_ingestion.call_count == (1 if expect_called else 0)
                        if expect_called:
                            assert mock_submit_any_ingestion.called_with(**expect_call_args)
                        assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'ingestion_filename': 'some-file',
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': None,
        'server': None,
        'institution': None,
        'project': None,
        'validate_only': False,
        'upload_folder': None,
        'no_query': False,
        'subfolders': False,
    })
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': True,
        'upload_folder': None,
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "-v", "-p", "some-project",
                     'some-file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file", "--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "--validate-only", "--project", "some-project"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': False,
        'upload_folder': 'a-folder',
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env",
                     "--institution", "some-institution",
                     "-s", "some-server",
                     "-p", "some-project",
                     '-u', 'a-folder',
                     'some-file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file",
                     "--env", "some-env",
                     "--institution", "some-institution",
                     "-s", "some-server",
                     "--project", "some-project",
                     '--upload_folder', 'a-folder'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': 'simulated_bundle',
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': True,
        'upload_folder': 'a-folder',
        'no_query': False,
        'subfolders': False,
    }
    test_it(args_in=["--env", "some-env",
                     "--institution", "some-institution",
                     "-s", "some-server",
                     "-v",
                     "-p", "some-project",
                     '-u', 'a-folder',
                     '-t', 'simulated_bundle',
                     'some-file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file",
                     "--env", "some-env",
                     "--institution", "some-institution",
                     "-s", "some-server",
                     "--validate-only",
                     "--project", "some-project",
                     '--upload_folder', 'a-folder',
                     '--ingestion_type', 'simulated_bundle'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': DEFAULT_INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': True,
        'upload_folder': None,
        'no_query': True,
        'subfolders': True,
    }
    test_it(args_in=["--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "-v", "-p", "some-project",
                     'some-file', '-nq', '-sf'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "-v", "-p", "some-project",
                     'some-file', '--no_query', '--subfolders'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
