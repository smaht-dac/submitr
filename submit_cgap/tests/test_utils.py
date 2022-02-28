import contextlib
import pytest
import re

from dcicutils.misc_utils import override_environ, environ_bool
from unittest import mock
from .. import utils as utils_module
from ..utils import show, keyword_as_title, FakeResponse, script_catch_errors, ERROR_HERALD


@contextlib.contextmanager
def shown_output():

    class ShownOutput:

        def __init__(self):
            self.lines = []

        def mock_print_handler(self, *args):
            text = " ".join(map(str, args))
            print("Mocked print:", text)
            self.lines.append(text)

    shown = ShownOutput()

    with mock.patch.object(utils_module, "PRINT") as mock_print:
        mock_print.side_effect = shown.mock_print_handler
        yield shown


def test_show():

    # Test uses WITHOUT timestamps
    with shown_output() as shown:
        show("This", "is", "a", "test.")
        show("This, too.")

        assert shown.lines == ["This is a test.", "This, too."]

    timestamp_pattern = re.compile(r'^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] (.*)$')

    # Test uses WITH timestamps
    with shown_output() as shown:
        show("This", "is", "a", "test.", with_time=True)
        show("This, too.", with_time=True)

        trimmed = []
        for line in shown.lines:
            matched = timestamp_pattern.match(line)
            assert matched, "Timestamp missing or in bad form: %s" % line
            trimmed.append(matched.group(1))

        assert trimmed == ["This is a test.", "This, too."]

    with shown_output() as shown:
        show("This", "is", "a", "test.", with_time=True)
        show("This, too.")

        assert timestamp_pattern.match(shown.lines[0])
        assert not timestamp_pattern.match(shown.lines[1])


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
