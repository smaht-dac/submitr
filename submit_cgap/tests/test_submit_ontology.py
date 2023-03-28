import pytest

from dcicutils.creds_utils import CGAPKeyManager
from unittest import mock
from .. import submission as submission_module
from ..scripts import submit_ontology as submit_ontology_module
from ..scripts.submit_ontology import main as submit_ontology_main
from .testing_helpers import system_exit_expected, argparse_errors_muffled


INGESTION_TYPE = "ontology"


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_submit_ontology_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        output = []
        with argparse_errors_muffled():
            with CGAPKeyManager.default_keys_file_for_testing(keyfile):
                with mock.patch.object(submit_ontology_module, "submit_any_ingestion") as mock_submit_any_ingestion:
                    with mock.patch.object(submission_module, "print") as mock_print:
                        mock_print.side_effect = lambda *args: output.append(" ".join(args))
                        with mock.patch.object(submission_module, "yes_or_no") as mock_yes_or_no:
                            mock_yes_or_no.return_value = True
                            with system_exit_expected(exit_code=expect_exit_code):
                                key_manager = CGAPKeyManager()
                                if keyfile:
                                    assert key_manager.keys_file == keyfile
                                assert key_manager.keys_file == (keyfile or key_manager.KEYS_FILE)
                                submit_ontology_main(args_in)
                                raise AssertionError(  # pragma: no cover
                                    "submit_ontology_main should not exit normally.")
                            assert mock_submit_any_ingestion.call_count == (1 if expect_called else 0)
                            if expect_called:
                                assert mock_submit_any_ingestion.called_with(**expect_call_args)
                            assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'ontology_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': None,
        'server': None,
        'lab': None,
        'award': None,
        'validate_only': False,
    })
    expect_call_args = {
        'ontology_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'lab': "some-lab",
        'award': "some-award",
        'validate_only': True,
    }
    test_it(args_in=["--env", "some-env", "--lab", "some-lab",
                     "-s", "some-server", "-v", "-a", "some-award",
                     "some-file"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file", "--env", "some-env", "--lab", "some-lab",
                     "-s", "some-server", "--validate-only", "-a", "some-award"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
