import contextlib
import re

from unittest import mock
from .. import utils as utils_module
from ..utils import show, FakeResponse


def test_show():

    @contextlib.contextmanager
    def shown_output():

        class ShownOutput:

            def __init__(self):
                self.lines = []

            def mock_print_handler(self, *args):
                text = " ".join(args)
                print("Mocked print:", text)
                self.lines.append(text)

        shown = ShownOutput()

        with mock.patch.object(utils_module, "PRINT") as mock_print:
            mock_print.side_effect = shown.mock_print_handler
            yield shown

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


def test_fake_response():
    pass
