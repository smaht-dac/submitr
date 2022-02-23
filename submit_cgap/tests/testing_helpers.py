import contextlib


@contextlib.contextmanager
def system_exit_expected(*, exit_code):
    try:
        yield
    except SystemExit as e:
        assert e.code == exit_code
    except Exception as e:
        raise AssertionError(f"Expected SystemExit({exit_code}) but got unexpected error: {e}")
    else:
        raise AssertionError(f"Expected SystemExit({exit_code}) but got non-error exit.")
