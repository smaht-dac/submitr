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
        with mock.patch.object(resume_uploads_module, "print") as mock_print:
            mock_print.side_effect = lambda *args: output.append(" ".join(args))
            with mock.patch.object(resume_uploads_module, "resume_uploads") as mock_resume_uploads:
                try:
                    assert KeyManager.keydicts_filename() == keyfile or KeyManager.DEFAULT_KEYDICTS_FILENAME
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
