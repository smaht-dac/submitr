import json
from dcicutils.portal_utils import Portal

env = "smaht-local"
data_type = "SubmissionCenter"
user_uuid = "74fef71a-dfc1-4aa4-acc0-cedcb7ac1d68"  # David Michaels (smaht-local)
# From staging (2024-03-29)
data = {
    "code": "cwru",
    "title": "CWRU TTD",
#   "leader": "9f8f6144-9977-4ba6-8245-78f200c28a03",
    "leader": "74fef71a-dfc1-4aa4-acc0-cedcb7ac1d68",
    "status": "public",
    "identifier": "cwru_ttd",
    "description": "Case Western Reserve University Jin TTD",
    "date_created": "2024-01-26T16:25:09.345928+00:00",
    "submitted_by": "986b362f-4eb6-4a9c-8173-3ab267226992",
#   "schema_version": "1",
    "uuid": "47a1e892-5542-416c-b9cc-c93f4afd643d"
}

portal = Portal(env)
response = portal.post_metadata(data_type, data)
print("POST RESPONSE:")
print(json.dumps(response, indent=4))

print("GET RESPONSE:")
response = portal.get_metadata(f"/{data_type}/{data['uuid']}")
print(json.dumps(response, indent=4))
