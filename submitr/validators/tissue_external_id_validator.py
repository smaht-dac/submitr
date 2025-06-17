from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# Validator that reports if any Tissue items are linked to Donor items
# with an external_id that does not contain the external_id of the Donor

_TISSUE_SCHEMA_NAME = "Tissue"
_DONOR_PROPERTY_NAME = "donor"
_EXTERNAL_ID_PROPERTY_NAME = "external_id"
_DONOR_SCHEMA_NAME = "Donor"


@structured_data_validator_finish_hook
def _tissue_external_id_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_TISSUE_SCHEMA_NAME), list):
        return
    for item in data:
        if _DONOR_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if (donor_item := [
                    donor
                    for donor in structured_data.data.get(_DONOR_SCHEMA_NAME)
                    if donor.get("submitted_id") == item.get(_DONOR_PROPERTY_NAME)
            ]):
                donor_external_id = donor_item[0].get(_EXTERNAL_ID_PROPERTY_NAME)
                tissue_external_id = item.get(_EXTERNAL_ID_PROPERTY_NAME)
                if tissue_external_id.split('-')[0] != donor_external_id:
                    structured_data.note_validation_error(
                        f"{_TISSUE_SCHEMA_NAME}:"
                        f" item {submitted_id}"
                        f" external_id {tissue_external_id} does not"
                        f" match Donor external_id {donor_external_id}."
                    )
