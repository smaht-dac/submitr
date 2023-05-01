# This file contains centralized functions for all Portal interactions used by SubmitCGAP.

import requests
from typing import Tuple
from dcicutils import ff_utils
from dcicutils.trace_utils import Trace


@Trace()
def portal_metadata_post(schema: str, data: dict, auth: Tuple) -> dict:
    return ff_utils.post_metadata(post_item=data, schema_name=schema, key=auth)


@Trace()
def portal_metadata_patch(uuid: str, data: dict, auth: Tuple) -> dict:
    return ff_utils.patch_metadata(patch_item=data, obj_id=uuid, key=auth)


@Trace()
def portal_request_get(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return requests.get(url, auth=auth, **kwargs)


@Trace()
def portal_request_post(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return requests.post(url, auth=auth, **kwargs)
