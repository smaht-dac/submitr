import contextlib


@contextlib.contextmanager
def system_exit_expected(*, exit_code):
    try:
        yield
    except SystemExit as e:
        if e.code != exit_code:
            raise AssertionError(f"SystemExit got code={e.code} where code={exit_code} was expected.")
    except Exception as e:
        raise AssertionError(f"Expected SystemExit({exit_code}) but got unexpected error: {e}")
    else:
        raise AssertionError(f"Expected SystemExit({exit_code}) but got non-error exit.")
