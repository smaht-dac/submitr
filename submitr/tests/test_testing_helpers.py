import pytest
import re

from .testing_helpers import system_exit_expected, argparse_errors_muffled


def test_system_exit_expected():

    with system_exit_expected(exit_code=0):
        exit(0)

    with system_exit_expected(exit_code=1):
        exit(1)

    with pytest.raises(AssertionError, match=re.escape("SystemExit got code=1 where code=0 was expected.")):
        with system_exit_expected(exit_code=0):
            exit(1)

    with pytest.raises(AssertionError, match=re.escape("SystemExit got code=0 where code=1 was expected.")):
        with system_exit_expected(exit_code=1):
            exit(0)

    with pytest.raises(AssertionError, match=re.escape("Expected SystemExit(0) but got unexpected error: foo")):
        with system_exit_expected(exit_code=0):
            raise RuntimeError("foo")

    with pytest.raises(AssertionError, match=re.escape("Expected SystemExit(0) but got non-error exit.")):
        with system_exit_expected(exit_code=0):
            print("foo")  # no error


def test_argparse_errors_muffled():

    with argparse_errors_muffled():
        # For now, we just test that we can call this at all. capturing the error output is a pain.
        # The real test of this is that the test output doesn't have argparse error messages all over it.
        pass
