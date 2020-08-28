from unittest import mock
from ..scripts.make_sample_fastq_file import main as make_sample_fastq_file_main
from ..scripts import make_sample_fastq_file as make_sample_fastq_file_module


def test_make_sample_fastq_file_script():

    def test_it(args_in, expect_exit_code, expect_called, expect_call_args=None):
        with mock.patch.object(make_sample_fastq_file_module,
                               "generate_sample_fastq_file") as mock_generate_sample_fastq_file:
            try:
                make_sample_fastq_file_main(args_in)
                mock_generate_sample_fastq_file.assert_called_with(**expect_call_args)
            except SystemExit as e:
                assert e.code == expect_exit_code
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
