import pytest

from dcicutils.s3_utils import HealthPageKey
from unittest import mock
from .. import submission as submission_module
from ..scripts.upload_item_data import main as upload_item_data_main
from ..scripts import upload_item_data as upload_item_data_module
from .testing_helpers import system_exit_expected, argparse_errors_muffled


TEST_ENCRYPT_KEY = 'encrypt-key-for-testing'


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
@pytest.mark.parametrize("mocked_s3_encrypt_key_id", [None, TEST_ENCRYPT_KEY])
def test_upload_item_data_script(keyfile, mocked_s3_encrypt_key_id):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):

        output = []
        with argparse_errors_muffled():
            with mock.patch.object(upload_item_data_module,
                                   "_upload_item_data") as mock_upload_item_data:
                with mock.patch.object(submission_module, "_get_health_page") as mock_get_health_page:
                    mock_get_health_page.return_value = {HealthPageKey.S3_ENCRYPT_KEY_ID: mocked_s3_encrypt_key_id}
                    with mock.patch.object(submission_module, "print") as mock_print:
                        mock_print.side_effect = lambda *args: output.append(" ".join(args))
                        with system_exit_expected(exit_code=expect_exit_code):
                            upload_item_data_main(args_in)
                            raise AssertionError(  # pragma: no cover
                                "upload_item_data_main should not exit normally.")
                        assert mock_upload_item_data.call_count == (1 if expect_called else 0)
                        if expect_called:
                            assert mock_upload_item_data.called_with(**expect_call_args)
                        assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some.file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'item_filename': 'some.file',
        'env': None,
        'server': None,
        'uuid': None,
        'no_query': False,
    })
    expect_call_args = {
        'item_filename': 'some.file',
        'env': None,
        'server': None,
        'uuid': 'some-guid',
        'no_query': False,
    }
    test_it(args_in=['-u', 'some-guid', 'some.file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['some.file', '-u', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'item_filename': 'some.file',
        'env': 'some-env',
        'server': 'some-server',
        'uuid': 'some-guid',
        'no_query': False,
    }
    test_it(args_in=['some.file', '-e', 'some-env', '--server', 'some-server', '-u', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-e', 'some-env', '--server', 'some-server', '-u', 'some-guid', 'some.file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'item_filename': 'some.file',
        'env': 'some-env',
        'server': 'some-server',
        'uuid': 'some-guid',
        'no_query': True,
    }
    test_it(args_in=['some.file', '-e', 'some-env', '--server', 'some-server', '-u', 'some-guid', '-nq'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
