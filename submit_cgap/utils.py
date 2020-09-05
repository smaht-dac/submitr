import datetime

from dcicutils.misc_utils import PRINT


# Programmatic output will use 'show' so that debugging statements using regular 'print' are more easily found.
def show(*args, with_time=False):
    if with_time:
        hh_mm_ss = str(datetime.datetime.now().strftime("%H:%M:%S"))
        PRINT(hh_mm_ss, *args)
    else:
        PRINT(*args)


class FakeResponse:

    def __init__(self, status_code, json=None):
        self.status_code = status_code
        self._json = json

    def __str__(self):
        return "<FakeResponse %s %s>" % (self.status_code, json.dumps(self.json))

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 300:
            raise Exception("%s raised for status." % self)
