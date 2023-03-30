# This file contains centralized functions for all Portal interactions used by SubmitCGAP.

import io
import json
import requests
from typing import Callable, Optional, Tuple, Union
from dcicutils import ff_utils
from dcicutils.misc_utils import environ_bool, PRINT


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def portal_metadata_post(schema: str, data: dict, auth: Tuple) -> dict:
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.post_metadata(post_item=data, schema_name=schema, key=auth)
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_metadata_patch(uuid: str, data: dict, auth: Tuple) -> dict:
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: METADATA PATCH {'/' if not uuid.startswith('/') else ''}{uuid}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.patch_metadata(patch_item=data, obj_id=uuid, key=auth)
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: METADATA PATCH {'/' if not uuid.startswith('/') else ''}{uuid} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_request_get(url: str, auth: Tuple = None) -> dict:
    return _portal_request(requests.get, url=url, auth=auth)


def portal_request_post(url: str,
                        data: Optional[Union[str, dict]] = None,
                        file: Optional[str] = None,
                        files: Optional[dict] = None,
                        auth: Tuple = None) -> dict:
    return _portal_request(requests.post, url=url, auth=auth, data=data, file=file, files=files)


def _portal_request(request: Callable,
                    url: str,
                    auth: Tuple = None,
                    headers: Optional[dict] = None,
                    data: Optional[Union[dict, list]] = None,
                    file: Optional[str] = None,
                    files: Optional[dict] = None) -> dict:
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
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url}", end="")
        if data:
            PRINT(f" | DATA: {json.dumps(data, default=str)}", end="")
        if files:
            PRINT(f" | FILES: {json.dumps(files, default=str)}", end="")
        if headers:
            PRINT(f" | HEADERS: {json.dumps(headers, default=str)}", end="")
        if auth:
            PRINT(f" | AUTH: <REDACTED>", end="")
        PRINT()
    response = request(url, **kwargs)
    if DEBUG_PROTOCOL:
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url} -> {response.status_code}"
              f" | RESPONSE: {json.dumps(response.json(), default=str)}")
    return response
