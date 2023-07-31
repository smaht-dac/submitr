from unittest import mock

from dcicutils.misc_utils import ignored
from ..scripts.make_sample_fastq_file import main as make_sample_fastq_file_main
from ..scripts import make_sample_fastq_file as make_sample_fastq_file_module
from .testing_helpers import system_exit_expected


def test_make_sample_fastq_file_script():

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        ignored(expect_call_args)
        with mock.patch.object(make_sample_fastq_file_module,
                               "generate_sample_fastq_file") as mock_generate_sample_fastq_file:
            with system_exit_expected(exit_code=expect_exit_code):
                make_sample_fastq_file_main(args_in)
                raise AssertionError("make_sample_fastq_file_main should not exit normally.")  # pragma: no cover
            assert mock_generate_sample_fastq_file.call_count == (1 if expect_called else 0)

    test_it(args_in=[], expect_exit_code=2, expect_called=False)  # Missing args
    test_it(args_in=['some.file'], expect_exit_code=0, expect_called=True, expect_call_args={
        'filename': 'some.file',
        'num': 10,
        'length': 10,
    })
    expect_call_args = {
        'filename': 'some.file',
        'num': 4,
        'length': 9,
    }
    test_it(args_in=['-n', '4', '-l', '9', 'some.file'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
    test_it(args_in=['some.file', '-n', '4', '-l', '9'],
            expect_exit_code=0,
            expect_called=True,
            expect_call_args=expect_call_args)
