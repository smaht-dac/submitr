# This file contains centralized functions for all Portal interactions used by submitr.

import requests
from typing import Tuple
from dcicutils.trace_utils import Trace
from dcicutils.portal_utils import Portal


# TODO: Eventually replace these with simple direct calls via dcicutils.portal_utils.Portal.


@Trace()
def portal_metadata_post(schema: str, data: dict, auth: Tuple) -> dict:
    return Portal(auth).post_metadata(object_type=schema, data=data)
#   return ff_utils.post_metadata(post_item=data, schema_name=schema, key=auth)


@Trace()
def portal_metadata_patch(uuid: str, data: dict, auth: Tuple) -> dict:
    return Portal(auth).patch_metadata(object_id=uuid, data=data)
#   return ff_utils.patch_metadata(patch_item=data, obj_id=uuid, key=auth)


@Trace()
def portal_request_get(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return Portal(auth).get(url, **kwargs)
#   return requests.get(url, auth=auth, **kwargs)


@Trace()
def portal_request_post(url: str, auth: Tuple, **kwargs) -> requests.models.Response:
    return Portal(auth).post(url, **kwargs)
#   return requests.post(url, auth=auth, **kwargs)
