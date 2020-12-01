import pytest

from dcicutils.misc_utils import ignored
from dcicutils.qa_utils import override_environ
from unittest import mock
from ..base import KeyManager
from ..scripts.show_upload_info import main as show_upload_info_main
from ..scripts import show_upload_info as show_upload_info_module


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_show_upload_info_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        output = []
        with override_environ(CGAP_KEYS_FILE=keyfile):
            with mock.patch.object(show_upload_info_module, "print") as mock_print:
                mock_print.side_effect = lambda *args: output.append(" ".join(args))
                with mock.patch.object(show_upload_info_module, "show_upload_info") as mock_show_upload_info:
                    try:
                        # Outside of the call, we will always see the default filename for cgap keys
                        # but inside the call, because of a decorator, the default might be different.
                        # See additional test below.
                        assert KeyManager.keydicts_filename() == KeyManager.DEFAULT_KEYDICTS_FILENAME

                        def mocked_show_upload_info(*args, **kwargs):
                            ignored(args, kwargs)
                            # We don't need to test this function's actions because we test its call args below.
                            # However, we do need to run this one test from the same dynamic context,
                            # so this is close enough.
                            assert KeyManager.keydicts_filename() == (keyfile or KeyManager.DEFAULT_KEYDICTS_FILENAME)

                        mock_show_upload_info.side_effect = mocked_show_upload_info
                        show_upload_info_main(args_in)
                        mock_show_upload_info.assert_called_with(**expect_call_args)
                    except SystemExit as e:
                        assert e.code == expect_exit_code
                    assert mock_show_upload_info.call_count == (1 if expect_called else 0)
                    assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-guid'], expect_exit_code=0, expect_called=True, expect_call_args={
        'env': None,
        'server': None,
        'uuid': 'some-guid'
    })
    expect_call_args = {
        'env': 'some-env',
        'server': None,
        'uuid': 'some-guid'
    }
    test_it(args_in=['some-guid', '-e', 'some-env'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-e', 'some-env', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'env': 'some-env',
        'server': 'http://some.server',
        'uuid': 'some-guid'
    }
    test_it(args_in=['some-guid', '-e', 'some-env', '-s', 'http://some.server'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-e', 'some-env', '-s', 'http://some.server', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
