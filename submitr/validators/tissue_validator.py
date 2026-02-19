from typing import Dict
from dcicutils import ff_utils
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook
from utils.dcicutils import structured_data


# Validator that reports if any Tissue items are linked to Donor items
# with an external_id that does not contain the external_id of the Donor
# if at least one of the two items is TPC-submitted

_TISSUE_SCHEMA_NAME = "Tissue"
_DONOR_PROPERTY_NAME = "donor"
_EXTERNAL_ID_PROPERTY_NAME = "external_id"
_DONOR_SCHEMA_NAME = "Donor"
_NDRI_SUBMISSION_CENTER = "NDRI"
_TISSUE_TERM_PROPERTY_NAME = "uberon_id"
_OT_TYPE = "OntologyTerm"


@structured_data_validator_finish_hook
def _tissue_external_id_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_TISSUE_SCHEMA_NAME), list):
        return
    for item in data:
        if _DONOR_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            tissue_sc = submitted_id.split('_')[0]
            if (donor_item := [
                    donor
                    for donor in structured_data.data.get(_DONOR_SCHEMA_NAME, [])
                    if donor.get("submitted_id") == item.get(_DONOR_PROPERTY_NAME)
            ]):
                donor_sc = donor_item[0].get("submitted_id", "").split('_')[0]
                if tissue_sc == _NDRI_SUBMISSION_CENTER or donor_sc == _NDRI_SUBMISSION_CENTER:
                    donor_external_id = donor_item[0].get(_EXTERNAL_ID_PROPERTY_NAME)
                    tissue_external_id = item.get(_EXTERNAL_ID_PROPERTY_NAME)
                    if tissue_external_id.split('-')[0] != donor_external_id:
                        structured_data.note_validation_error(
                            f"{_TISSUE_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" external_id {tissue_external_id} does not"
                            f" match Donor external_id {donor_external_id}."
                        )


def _get_term_info(term_id: str, key: Dict) -> str:
    term_info = {}
    #import pdb; pdb.set_trace()
    query = f"/search/?type={_OT_TYPE}&identifier={term_id}"
    result = ff_utils.search_metadata(query, key)
    if result and len(result) == 1:
        term = result[0]
        if term and (pids := term.get('valid_protocol_ids')):
            for pid in pids:
                code, ptype = (pid.split('_', 1) + [''])[:2]
                term_info[code] = ptype
    return term_info


@structured_data_validator_finish_hook
def _tissue_preservation_type_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_TISSUE_SCHEMA_NAME), list):
        return
    seen = {}
    for item in data:
        if _TISSUE_TERM_PROPERTY_NAME not in item or not (
            term_id := item.get(_TISSUE_TERM_PROPERTY_NAME)
        ):
            continue  # Skip items without uberon_id
        if not (term_info := seen.get(term_id)):
            term_info = _get_term_info(term_id, structured_data.portal.key)
            seen[term_id] = term_info

        if ptype := item.get("preservation_type"):
            for code, expected_ptype in term_info.items():
                if expected_ptype and code in item.get(_EXTERNAL_ID_PROPERTY_NAME, ""):
                    if expected_ptype not in ptype:
                        structured_data.note_validation_error(
                            f"{_TISSUE_SCHEMA_NAME}:"
                            f" item {item.get('submitted_id')}"
                            f" preservation_type {ptype} does not match"
                            f" expected preservation type {expected_ptype}"
                            f" for code {code} in Uberon term {term_id}."
                        )
