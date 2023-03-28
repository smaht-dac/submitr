import contextlib
import datetime
import io
import json
import requests
import time
from typing import Callable, Optional, Tuple, Union
from dcicutils import ff_utils
from dcicutils.misc_utils import PRINT, environ_bool
from json import dumps as json_dumps, loads as json_loads


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time: bool = False, same_line: bool = False):
    """
    Prints its args space-separated, as 'print' would, possibly with an hh:mm:ss timestamp prepended.

    :param args: an object to be printed
    :param with_time: a boolean specifying whether to prepend a timestamp
    """
    output = io.StringIO()
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime("%H:%M:%S"))
        print(hh_mm_ss, *args, end="", file=output)
    else:
        print(*args, end="", file=output)
    output = output.getvalue()
    if same_line:
        PRINT(f"\033[K{output}\r", end="", flush=True)
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


def check_repeatedly(check_function: Callable,
                     wait_seconds: int = 10,
                     repeat_count: int = -1,
                     check_message: str = None,
                     wait_message: str = None,
                     done_message: str = None,
                     stop_message: str = None,
                     response_message: bool = True,
                     messages: bool = True,
                     verbose: bool = False) -> bool:
    """
    Calls the given function (check_function) repeatedly, until it returns either a tuple whose first element is
    truthy, or just a non-tuple truthy value, waiting between calls for the given number (wait_seconds) of seconds,
    and trying for a maximum of the given number (repeat_count) of times; if repeat_count is non-positive (default),
    then never stop calling the function. If the function returns either a tuple whose first element is truthy,
    or just a non-tuple truthy value, then returns that value. If the function never returns a truthy value,
    and repeat_count is postiive, then after that maxmimum number of tries (repeat_count), return False.

    If the messages argument is True (default) then a message to the stdout will be printed indicating each time
    the function is called, how long (in seconds) till the next call, and how many times in total it has been called.
    Additionally if the response_message argument is True (default) then if the function finally returns a truthy
    value, then that value will be printed to the stdout.
    """
    def output(message):
        show(message, with_time=verbose, same_line=True)
    if not check_message:
        check_message = "Checking processing"
    if not wait_message:
        wait_message = "Waiting for processing completion"
    if not done_message:
        done_message = "Processing complete"
    if not stop_message:
        stop_message = "Giving up waiting for processing completion"
    ntimes = 0
    check_function_returning_tuple = True
    check_status = "Not Done Yet"
    start_time = time.time()
    start_time = 0
    while True:
        if messages:
            output(f"{check_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                   f" | Checked: {ntimes} time{'s' if ntimes != 1 else ''} ...")
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
                       f" | Checked: {ntimes} time{'s' if ntimes != 1 else ''}\n")
            return check_function_response
        if repeat_count > 0 and ntimes >= repeat_count:
            if messages:
                output(f"{stop_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                       f" | Checked: {ntimes} time{'s' if ntimes != 1 else ''}\n")
            return check_function_response if check_function_returning_tuple else False
        for i in range(wait_seconds):
            time.sleep(1)
            if messages:
                output(f"{wait_message} {f'| Status: {check_status.title()}' if check_status else ''}"
                       f" | Checked: {ntimes} time{'s' if ntimes != 1 else ''}"
                       f" | Next check: {wait_seconds - i} second{'s' if wait_seconds - i != 1 else ''} ...")


def portal_metadata_post(schema: str, data: dict, auth: Tuple, debug: bool = False) -> dict:
    if debug:
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.post_metadata(post_item=data, schema_name=schema, key=auth)
    if debug:
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_metadata_patch(uuid: str, data: dict, auth: Tuple, debug: bool = False) -> dict:
    if debug:
        PRINT(f"DEBUG: METADATA PATCH {'/' if not schema.startswith('/') else ''}{uuid}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.patch_metadata(patch_item=data, obj_id=uuid, key=auth)
    if debug:
        PRINT(f"DEBUG: METADATA PATCH {'/' if not schema.startswith('/') else ''}{uuid} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_request_get(url: str,
                       auth: Tuple = None,
                       debug: bool = False) -> dict:
    return _portal_request(requests.get, url=url, auth=auth, debug=debug)


def portal_request_post(url: str,
                        data: Optional[Union[str, dict]] = None,
                        file: Optional[str] = None,
                        files: Optional[dict] = None,
                        auth: Tuple = None,
                        debug: bool = False) -> dict:
    return _portal_request(requests.post, url=url, auth=auth, data=data, file=file, files=files, debug=debug)


def _portal_request(request: Callable,
                    url: str,
                    auth: Tuple = None,
                    headers: Optional[dict] = None,
                    data: Optional[Union[dict, list]] = None,
                    file: Optional[str] = None,
                    files: Optional[dict] = None,
                    debug: bool = False) -> dict:
    kwargs = {
        "auth": auth,
        "allow_redirects": True
    }
    if not files:
        if file:
            files = {"datafile": io.open(file, "rb") if file != "/dev/null" else None}
    if not headers:
        if not files:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        kwargs["headers"] = headers
    else:
        kwargs["headers"] = None
    if data:
        if not files:
            kwargs["json"] = data
        else:
            kwargs["data"] = data
    if files:
        kwargs["files"] = files
    if debug:
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url}", end="")
        if data:
            PRINT(f" | DATA: {json.dumps(data, default=str)}", end="")
        if files:
            PRINT(f" | FILES: {json.dumps(files, default=str)}", end="")
        if headers:
            PRINT(f" | HEADERS: {json.dumps(headers, default=str)}", end="")
        if auth:
            PRINT(f" | AUTH: (\"{auth[0]}\", <REDACTED>)", end="")
        PRINT()
    response = request(url, **kwargs)
    if debug:
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url} -> {response.status_code} | RESPONSE: {json.dumps(response.json(), default=str)}")
    return response
