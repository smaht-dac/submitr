import contextlib
import pytest
import re

from dcicutils.misc_utils import ignored, override_environ, environ_bool
from unittest import mock

from .. import utils as utils_module
from ..utils import (
    show, keyword_as_title, FakeResponse, script_catch_errors, ERROR_HERALD, ERASE_LINE, TIMESTAMP_REGEXP,
)


@contextlib.contextmanager
def shown_output():

    class ShownOutput:

        def __init__(self):
            self.lines = []

        def mock_print_handler(self, *args, **kwargs):
            assert kwargs.keys() <= {"end", "flush"}
            text = " ".join(map(str, args))
            print("Mocked print:", text)
            self.lines.append(text)

    shown = ShownOutput()

    with mock.patch.object(utils_module, "PRINT") as mock_print:
        mock_print.side_effect = shown.mock_print_handler
        yield shown


ERASE_LINE_REGEXP = re.escape(ERASE_LINE)

SHOW_RAW_STRING_PATTERN = re.compile("^(.*)$")
SHOW_TIMESTAMP_PATTERN = re.compile(f"^{TIMESTAMP_REGEXP} (.*)$")

SHOW_ERASE_LINE_PATTERN = re.compile(f"^{ERASE_LINE_REGEXP}(.*)\r$")
SHOW_ERASE_LINE_TIMESTAMP_PATTERN = re.compile(f"^{ERASE_LINE_REGEXP}{TIMESTAMP_REGEXP} (.*)\r$")


def test_show():

    print()  # start on a fresh line

    # Test uses WITHOUT timestamps
    with shown_output() as shown:
        show("This", "is", "a", "test.")
        show("This, too.")

        assert shown.lines == ["This is a test.", "This, too."]

    # Test uses WITH timestamps
    with shown_output() as shown:
        show("This", "is", "a", "test.", with_time=True)
        show("This, too.", with_time=True)

        trimmed = []
        for line in shown.lines:
            matched = SHOW_TIMESTAMP_PATTERN.match(line)
            assert matched, f"pattern={SHOW_TIMESTAMP_PATTERN!r}\n{line!r}\nTimestamp missing or in bad form."
            trimmed.append(matched.group(1))

        assert trimmed == ["This is a test.", "This, too."]

    #  Tester for full range of arg patterns.
    def check_output(pattern, with_time=False, same_line=False):

        with shown_output() as shown:

            fragment_lists = [["This", "is", "a", "test."],
                              ["This, too."],
                              ["This is also", "part of", "the test."]]

            expected_lines = []

            for fragment_list in fragment_lists:
                show(*fragment_list, with_time=with_time, same_line=same_line)
                expected_line = " ".join(fragment_list)
                expected_lines.append(expected_line)

            for i, line in enumerate(shown.lines):
                m = pattern.match(line)
                assert m
                assert m.group(1) == expected_lines[i]

    # Check all four argument patterns...
    check_output(SHOW_RAW_STRING_PATTERN)
    check_output(SHOW_TIMESTAMP_PATTERN, with_time=True)
    check_output(SHOW_ERASE_LINE_PATTERN, same_line=True)
    check_output(SHOW_ERASE_LINE_TIMESTAMP_PATTERN, with_time=True, same_line=True)


def test_keyword_as_title():

    assert keyword_as_title('foo') == 'Foo'
    assert keyword_as_title('some_text') == 'Some Text'


def test_fake_response():

    # Cannot specify both json and content
    with pytest.raises(Exception):
        FakeResponse(200, content="foo", json={"foo": "bar"})

    ok_empty_response = FakeResponse(status_code=200)

    assert ok_empty_response.content == ""

    with pytest.raises(Exception):
        ok_empty_response.json()

    assert str(ok_empty_response) == '<FakeResponse 200>'

    ok_empty_response.raise_for_status()  # This should raise no error

    ok_response = FakeResponse(status_code=200, json={'foo': 'bar'})

    assert ok_response.status_code == 200
    assert ok_response.json() == {'foo': 'bar'}

    assert str(ok_response) == '<FakeResponse 200 {"foo": "bar"}>'

    ok_response.raise_for_status()  # This should raise no error

    ok_non_json_response = FakeResponse(status_code=200, content="foo")

    assert ok_non_json_response.status_code == 200
    assert ok_non_json_response.content == "foo"
    with pytest.raises(Exception):
        ok_non_json_response.json()

    error_response = FakeResponse(status_code=400, json={'message': 'bad stuff'})

    assert error_response.status_code == 400
    assert error_response.json() == {'message': "bad stuff"}

    assert str(error_response) == '<FakeResponse 400 {"message": "bad stuff"}>'

    with pytest.raises(Exception):
        error_response.raise_for_status()


def test_script_catch_errors():

    with shown_output() as shown:
        with pytest.raises(SystemExit) as caught:
            with script_catch_errors():
                print("foo")
        # foo = sys.exc_info()
        assert caught.value.code == 0
        assert shown.lines == []

    with shown_output() as shown:
        with pytest.raises(SystemExit) as caught:
            with script_catch_errors():
                raise Exception("Foo")
        assert caught.value.code == 1
        assert shown.lines == [ERROR_HERALD, "Exception: Foo"]

    # Not enough to override env var DEBUG_CGAP, since the module is already loaded and the env var's value
    # is already seen and parsed. We must change module value at this point if we want to exercise the relevant
    # code path.
    with mock.patch.object(utils_module, "DEBUG_CGAP", True):
        with shown_output() as shown:
            with pytest.raises(Exception) as caught:
                ignored(caught)
                with script_catch_errors():
                    raise Exception("Foo")
            assert shown.lines == []  # The value was not trapped, so not shown

    # Since we couldn't override the setting of the variable in the preceding code, we at least verify that setting
    # the value would have produced the right effect.
    with override_environ(DEBUG_CGAP=None):
        assert not environ_bool("DEBUG_CGAP")  # Unset, the value is False
    with override_environ(DEBUG_CGAP=""):
        assert not environ_bool("DEBUG_CGAP")  # Set to empty string, the value is False
    with override_environ(DEBUG_CGAP="FALSE"):
        assert not environ_bool("DEBUG_CGAP")  # Set to "FALSE", the value is False
    with override_environ(DEBUG_CGAP="TRUE"):
        assert environ_bool("DEBUG_CGAP")      # Set to "TRUE", the value is True
    # As it happens, random other values are false, but we just don't care about that.
