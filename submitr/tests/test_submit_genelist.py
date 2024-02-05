import pytest

from unittest import mock
from .. import submission as submission_module
from ..scripts import submit_genelist as submit_genelist_module
from ..scripts.submit_genelist import main as submit_genelist_main
from .testing_helpers import system_exit_expected, argparse_errors_muffled


INGESTION_TYPE = "genelist"


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_submit_genelist_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        output = []
        with argparse_errors_muffled():
            with mock.patch.object(submit_genelist_module, "submit_any_ingestion") as mock_submit_any_ingestion:
                with mock.patch.object(submission_module, "print") as mock_print:
                    mock_print.side_effect = lambda *args: output.append(" ".join(args))
                    with mock.patch.object(submission_module, "yes_or_no") as mock_yes_or_no:
                        mock_yes_or_no.return_value = True
                        with system_exit_expected(exit_code=expect_exit_code):
                            submit_genelist_main(args_in)
                            raise AssertionError(  # pragma: no cover
                                "submit_genelist_main should not exit normally.")
                        assert mock_submit_any_ingestion.call_count == (1 if expect_called else 0)
                        if expect_called:
                            assert mock_submit_any_ingestion.called_with(**expect_call_args)
                        assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'ingestion_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': None,
        'server': None,
        'institution': None,
        'project': None,
        'validate_only': False,
    })
    expect_call_args = {
        'ingestion_filename': 'some-file',
        'ingestion_type': INGESTION_TYPE,
        'env': "some-env",
        'server': "some-server",
        'institution': "some-institution",
        'project': "some-project",
        'validate_only': True,
    }
    test_it(args_in=["--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "-v", "-p", "some-project",
                     "some-file"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=["some-file", "--env", "some-env", "--institution", "some-institution",
                     "-s", "some-server", "--validate-only", "-p", "some-project"],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
