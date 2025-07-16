from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# Validator that reports if any TissueSample items are linked to Tissue items
# with an external_id that does not contain the external_id of the Tissue
# if at least one of the two items is TPC-submitted

_TISSUE_SAMPLE_SCHEMA_NAME = "TissueSample"
_SAMPLE_SOURCE_PROPERTY_NAME = "sample_sources"
_EXTERNAL_ID_PROPERTY_NAME = "external_id"
_TISSUE_SCHEMA_NAME = "Tissue"
_NDRI_SUBMISSION_CENTER = "NDRI"


@structured_data_validator_finish_hook
def _tissue_sample_external_id_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list):
        return
    for item in data:
        if _SAMPLE_SOURCE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            tissue_sample_sc = submitted_id.split('_')[0]
            if (tissue_items := [
                tissue
                for tissue in structured_data.data.get(_TISSUE_SCHEMA_NAME, [])
                if tissue.get("submitted_id") in item.get(_SAMPLE_SOURCE_PROPERTY_NAME)
            ]):
                tissue_sc = tissue_items[0].get("submitted_id", "").split('_')[0]
                if tissue_sample_sc == _NDRI_SUBMISSION_CENTER or tissue_sc == _NDRI_SUBMISSION_CENTER:
                    tissue_external_id = tissue_items[0].get(_EXTERNAL_ID_PROPERTY_NAME)
                    tissue_sample_external_id = item.get(_EXTERNAL_ID_PROPERTY_NAME)
                    if "-".join(tissue_sample_external_id.split("-")[0:2]) != tissue_external_id:
                        structured_data.note_validation_error(
                            f"{_TISSUE_SAMPLE_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" external_id {tissue_sample_external_id} does not"
                            f" match {_TISSUE_SCHEMA_NAME} external_id"
                            f" {tissue_external_id}."
                        )
