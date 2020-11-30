import pytest

from dcicutils.qa_utils import override_environ
from unittest import mock
from ..base import KeyManager
from ..scripts.resume_uploads import main as resume_uploads_main
from ..scripts import resume_uploads as resume_uploads_module


@pytest.mark.parametrize("keyfile", [None, "foo.bar"])
def test_resume_uploads_script(keyfile):

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        output = []
        with override_environ(CGAP_KEYS_FILE=keyfile):
            with mock.patch.object(resume_uploads_module, "print") as mock_print:
                mock_print.side_effect = lambda *args: output.append(" ".join(args))
                with mock.patch.object(resume_uploads_module, "resume_uploads") as mock_resume_uploads:
                    try:
                        # Outside of the call, we will always see the default filename for cgap keys
                        # but inside the call, because of a decorator, the default might be different.
                        # See additional test below.
                        assert KeyManager.keydicts_filename() == KeyManager.DEFAULT_KEYDICTS_FILENAME
                        def mocked_resume_uploads(*args, **kwargs):
                            # We don't need to test this function's actions because we test its call args below.
                            # However, we do need to run this one test from the same dynamic context,
                            # so this is close enough.
                            assert KeyManager.keydicts_filename() == (keyfile or KeyManager.DEFAULT_KEYDICTS_FILENAME)
                        mock_resume_uploads.side_effect = mocked_resume_uploads
                        resume_uploads_main(args_in)
                        mock_resume_uploads.assert_called_with(**expect_call_args)
                    except SystemExit as e:
                        assert e.code == expect_exit_code
                    assert mock_resume_uploads.call_count == (1 if expect_called else 0)
                    assert output == []

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some-guid'], expect_exit_code=0, expect_called=True, expect_call_args={
        'bundle_filename': None,
        'env': None,
        'server': None,
        'uuid': 'some-guid'
    })
    expect_call_args = {
        'bundle_filename': 'some.file',
        'env': None,
        'server': None,
        'uuid': 'some-guid'
    }
    test_it(args_in=['-b', 'some.file', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['some-guid', '-b', 'some.file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'bundle_filename': 'some.file',
        'env': 'some-env',
        'server': None,
        'uuid': 'some-guid'
    }
    test_it(args_in=['some-guid', '-b', 'some.file', '-e', 'some-env'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-b', 'some.file', '-e', 'some-env', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    expect_call_args = {
        'bundle_filename': 'some.file',
        'env': 'some-env',
        'server': 'http://some.server',
        'uuid': 'some-guid'
    }
    test_it(args_in=['some-guid', '-b', 'some.file', '-e', 'some-env', '-s', 'http://some.server'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['-b', 'some.file', '-e', 'some-env', '-s', 'http://some.server', 'some-guid'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
