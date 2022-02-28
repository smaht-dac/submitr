import contextlib
import datetime

from dcicutils.misc_utils import PRINT, environ_bool
from json import dumps as json_dumps, loads as json_loads


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time=False):
    """
    Prints its args space-separated, as 'print' would, possibly with an hh:mm:ss timestamp prepended.

    :param args: an object to be printed
    :param with_time: a boolean specifying whether to prepend a timestamp
    """
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime("%H:%M:%S"))
        PRINT(hh_mm_ss, *args)
    else:
        PRINT(*args)


def keyword_as_title(keyword):
    """
    Given a dictionary key or other token-like keyword, return a prettier form of it use as a display title.

    Example:
        keyword_as_title('foo') => 'Foo'
        keyword_as_title('some_text') => 'Some Text'

    :param keyword:
    :return: a string which is the keyword in title case with underscores replaced by spaces.
    """

    return keyword.replace("_", " ").title()


class FakeResponse:

    def __init__(self, status_code, json=None, content=None):
        self.status_code = status_code
        if json is not None and content is not None:
            raise Exception("FakeResponse cannot have both content and json.")
        elif content is not None:
            self.content = content
        elif json is None:
            self.content = ""
        else:
            self.content = json_dumps(json)

    def __str__(self):
        if self.content:
            return "<FakeResponse %s %s>" % (self.status_code, self.content)
        else:
            return "<FakeResponse %s>" % (self.status_code,)

    def json(self):
        return json_loads(self.content)

    def raise_for_status(self):
        if self.status_code >= 300:
            raise Exception(f"{self} raised for status.")


DEBUG_CGAP = environ_bool("DEBUG_CGAP")

ERROR_HERALD = "Command exited in an unusual way. Please feel free to report this, citing the following message."


@contextlib.contextmanager
def script_catch_errors():
    try:
        yield
        exit(0)
    except Exception as e:
        if DEBUG_CGAP:
            # If debugging, let the error propagate, do not trap it.
            raise
        else:
            show(ERROR_HERALD)
            show(f"{e.__class__.__name__}: {e}")
            exit(1)
