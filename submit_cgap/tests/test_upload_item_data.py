import pytest

from dcicutils.misc_utils import ignored
from dcicutils.qa_utils import override_environ
from unittest import mock
from ..base import KeyManager
from ..scripts.upload_item_data import main as upload_item_data_main
from ..scripts import upload_item_data as upload_item_data_module


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_upload_item_data_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):

        with override_environ(CGAP_KEYS_FILE=keyfile):
            with mock.patch.object(upload_item_data_module,
                                   "upload_item_data") as mock_upload_item_data:
                try:
                    # Outside of the call, we will always see the default filename for cgap keys
                    # but inside the call, because of a decorator, the default might be different.
                    # See additional test below.
                    assert KeyManager.keydicts_filename() == KeyManager.DEFAULT_KEYDICTS_FILENAME

                    def mocked_upload_item_data(*args, **kwargs):
                        ignored(args, kwargs)
                        # We don't need to test this function's actions because we test its call args below.
                        # However, we do need to run this one test from the same dynamic context,
                        # so this is close enough.
                        assert KeyManager.keydicts_filename() == (keyfile or KeyManager.DEFAULT_KEYDICTS_FILENAME)

                    mock_upload_item_data.side_effect = mocked_upload_item_data
                    upload_item_data_main(args_in)
                    mock_upload_item_data.assert_called_with(**expect_call_args)
                except SystemExit as e:
                    assert e.code == expect_exit_code
                assert mock_upload_item_data.call_count == (1 if expect_called else 0)

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some.file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'item_filename': 'some.file',
        'env': None,
        'server': None,
        'uuid': None,
    })
    expect_call_args = {
        'item_filename': 'some.file',
        'env': None,
        'server': None,
        'uuid': 'some-guid'
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
        'uuid': 'some-guid'
    }
    test_it(args_in=['some.file', '-e', 'some-env', '--server', 'some-server', '-u', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-e', 'some-env', '--server', 'some-server', '-u', 'some-guid', 'some.file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
