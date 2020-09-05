import datetime

from dcicutils.misc_utils import PRINT
from json import dumps as json_dumps, loads as json_loads


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time=False):
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime("%H:%M:%S"))
        PRINT(hh_mm_ss, *args)
    else:
        PRINT(*args)


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
            raise Exception("%s raised for status." % self)
