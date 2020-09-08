import contextlib
import pytest
import re

from unittest import mock
from .. import utils as utils_module
from ..utils import show, keyword_as_title, FakeResponse


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
