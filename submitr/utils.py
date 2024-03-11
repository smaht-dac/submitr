import datetime
import io
import time
from typing import Any, Callable, Tuple, Union
from dcicutils.misc_utils import ignored, PRINT
from json import dumps as json_dumps, loads as json_loads


ERASE_LINE = "\033[K"
TIMESTAMP_PATTERN = "%H:%M:%S"
TIMESTAMP_REGEXP = "[0-2][0-9]:[0-5][0-9]:[0-5][0-9]"


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time: bool = False, same_line: bool = False):
    """
    Prints its args space-separated, as 'print' would, possibly with an hh:mm:ss timestamp prepended.

    :param args: an object to be printed
    :param with_time: a boolean specifying whether to prepend a timestamp
    :param same_line: a boolean saying whether to do this output in a way that erases the current line
        and returns to the start of the line without advancing vertically so that subsequent same_line=True
        requests will erase (and so replace) the current line.
    """
    output = io.StringIO()
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime(TIMESTAMP_PATTERN))
        print(hh_mm_ss, *args, end="", file=output)
    else:
        print(*args, end="", file=output)
    output = output.getvalue()
    if same_line:
        PRINT(f"{ERASE_LINE}{output}\r", end="", flush=True)
    else:
        PRINT(output)


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


# TODO: If deemed generally useful then move to dcicutils.
def check_repeatedly(check_function: Callable,
                     wait_seconds: int = 10,
                     repeat_count: int = -1,
                     check_message: str = None,
                     wait_message: str = None,
                     done_message: str = None,
                     stop_message: str = None,
                     action: str = "processing",
                     response_message: bool = True,
                     messages: bool = True,
                     verbose: bool = True) -> Union[Tuple[bool, str, Any], Any]:
    """
    Calls the given function (check_function) repeatedly, until it returns either a tuple whose first element is
    truthy, or just a non-tuple truthy value, waiting between calls for the given number (wait_seconds) of seconds,
    and trying for a maximum of the given number (repeat_count) of times; if repeat_count is non-positive (default),
    then never stop calling the function. If the function returns either a tuple whose first element is truthy,
    or just a non-tuple truthy value, then returns that value. If the function never returns a truthy value,
    and repeat_count is postiive, then after that maxmimum number of tries (repeat_count), return False.

    If the messages argument is True (default) then a message to the stdout will be printed indicating each time
    the function is called, how long (in seconds) till the next call, and how many times in total it has been called.
    Additionally, if the response_message argument is True (default) then if the function finally returns a truthy
    value, then that value will be printed to the stdout.
    """
    ignored(response_message)  # TODO: Why is this not used? -kmp 2-Aug-2023

    def output(message):
        show(message, with_time=False, same_line=True)
    if not check_message:
        check_message = f"Checkin for {action} completion"
    if not wait_message:
        wait_message = f"Waiting for {action} completion"
    if not done_message:
        done_message = f"{action.title()} complete"
    if not stop_message:
        stop_message = f"Giving up waiting for {action} completion"
    ntimes = 0
    check_function_returning_tuple = True
    check_status = "Not Done Yet"
    start_time = time.time()
    def duration():  # noqa
        duration = time.time() - start_time
        return f"{'%.1f' % duration}s"
    while True:
        if messages:
            output(f"{check_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                   f" ‖ Checked: {ntimes}x"
                   f" | Next: {wait_seconds - 0}s"
                   f" ‖ {duration()}")
        check_function_response = check_function()
        ntimes += 1
        if isinstance(check_function_response, Tuple) and len(check_function_response) >= 2:
            check_done = check_function_response[0]
            check_status = check_function_response[1]
        else:
            check_function_returning_tuple = False
            check_done = check_function_response
            check_status = None
        if check_done:
            if messages:
                output(f"{done_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                       f" ‖ {duration()}\n")
            return check_function_response
        if ntimes >= repeat_count > 0:
            if messages:
                output(f"{stop_message} {f' Status: {check_status.title()}' if check_status else ''}"
                       f" ‖ Checked: {ntimes}x"
                       f" | Next: {wait_seconds - 0}s"
                       f" ‖ {duration()}\n")
            return check_function_response if check_function_returning_tuple else False
        for i in range(wait_seconds):
            time.sleep(0.2)
            if messages:
                output(f"{wait_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                       f" ‖ Checked: {ntimes}x"
                       f" | Next: {wait_seconds - i}s"
                       f" ‖ {duration()}")
