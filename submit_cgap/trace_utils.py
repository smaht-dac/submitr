from dcicutils.misc_utils import environ_bool, full_object_name, PRINT
from dcicutils.obfuscation_utils import obfuscate_dict
import functools
import json


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def Trace(enabled=None):
    if enabled is None:
        enabled = DEBUG_PROTOCOL
    def _maybe_attach_trace(fn):
        if not enabled:
            return fn
        trace_name = full_object_name(fn)
        @functools.wraps(fn)
        def _traced(*args, **kwargs):
            PRINT(f"TRACE {trace_name} | ARGS: {args!r} KWARGS: {_show_dict(kwargs)}")
            try:
                res = fn(*args, **kwargs)
                PRINT(f"TRACE {trace_name} RETURN: {res!r}")
                return res
            except BaseException as exc:
                PRINT(f"TRACE {trace_name} EXCEPTION: {get_error_message(exc)}")
                raise
        return _traced
    return _maybe_attach_trace


def _show_dict(d, indent=0):
    d = obfuscate_dict(d)
    if not isinstance(d, dict):
        return ""
    elif not d:
        return "{}"
    else:
        return json.dumps(d)
