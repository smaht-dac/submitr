# This file contains centralized functions for all Portal interactions used by SubmitCGAP.

import io
import json
import requests
from typing import Callable, Optional, Tuple, Union
from dcicutils import ff_utils
from dcicutils.misc_utils import environ_bool, PRINT


DEBUG_PROTOCOL = environ_bool("DEBUG_PROTOCOL", default=False)


def portal_metadata_post(schema: str, data: dict, auth: Tuple) -> dict:
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.post_metadata(post_item=data, schema_name=schema, key=auth)
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: METADATA POST {'/' if not schema.startswith('/') else ''}{schema} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_metadata_patch(uuid: str, data: dict, auth: Tuple) -> dict:
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: METADATA PATCH {'/' if not uuid.startswith('/') else ''}{uuid}"
              f" | DATA: {json.dumps(data)}")
    response = ff_utils.patch_metadata(patch_item=data, obj_id=uuid, key=auth)
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: METADATA PATCH {'/' if not uuid.startswith('/') else ''}{uuid} -> {response.get('status')}"
              f" | RESPONSE: {json.dumps(response, default=str)}")
    return response


def portal_request_get(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return _portal_request(requests.get, url=url, auth=auth, **kwargs)


def portal_request_post(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return _portal_request(requests.post, url=url, auth=auth, **kwargs)


def _portal_request(request: Callable, url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url}", end="")
        if kwargs.get("headers"):
            PRINT(f" | HEADERS: {json.dumps(kwargs['headers'], default=str)}", end="")
        if kwargs.get("data"):
            PRINT(f" | DATA: {json.dumps(kwargs['data'], default=str)}", end="")
        if kwargs.get("json"):
            PRINT(f" | JSON: {json.dumps(kwargs['json'], default=str)}", end="")
        if kwargs.get("files"):
            PRINT(f" | FILES: {json.dumps(kwargs['files'], default=str)}", end="")
        if auth:
            PRINT(f" | AUTH: <REDACTED>", end="")
    response = request(url, auth=auth, allow_redirects=True, **kwargs)
    if DEBUG_PROTOCOL:  # pragma: no cover
        PRINT(f"DEBUG: HTTP {request.__name__.upper()} {url} -> {response.status_code}"
              f" | RESPONSE: {json.dumps(response.json(), default=str)}")
    return response
