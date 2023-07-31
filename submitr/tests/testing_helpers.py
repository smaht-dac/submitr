import argparse
import contextlib
import json
import os
import tempfile
from typing import Any, Generator
from unittest import mock


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


@contextlib.contextmanager
def argparse_errors_muffled():
    with mock.patch.object(argparse.ArgumentParser, "_print_message"):
        yield


@contextlib.contextmanager
def temporary_json_file(data: dict) -> Generator[Any, None, None]:
    filename = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            filename = f.name  # obtain file's absolute path for later use
            json.dump(data, f)
            f.close()  # The deleted=False above keeps file from being deleted upon this close
        yield filename
    finally:
        if filename:
            try:
                os.remove(filename)
            except Exception:  # perhaps someone else already removed it
                pass
