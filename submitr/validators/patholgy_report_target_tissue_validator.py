from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports if a PathologyReport item has a target_tissues.present = No
# the target_tissues.percentages field must be [0] 
_PATHREPORT_SCHEMA_NAME = "PathologyReport"
_T_TISSUE_PROPERTY_NAME = "target_tissues"  # this is a sub-object
_PRESENT_PROPERTY_NAME = "target_tissue_present"
_PERCENTAGE_PROPERTY_NAME = "target_tissue_percentage"
_PRESENT_PROPERTY_VALUE_NO = "No"
_PERC_PROP_NAME_VALUE_IF_ABSENT = [0]


@structured_data_validator_finish_hook
def _pathology_report_target_tissue_not_present_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_PATHREPORT_SCHEMA_NAME), list):
        return
    for item in data:
        submitted_id = item.get("submitted_id")
        if target_tissues := item.get(_T_TISSUE_PROPERTY_NAME):
            for tt in target_tissues:
                if (tt.get(_PRESENT_PROPERTY_NAME) == _PRESENT_PROPERTY_VALUE_NO):
                    if tt.get(_PERCENTAGE_PROPERTY_NAME) != _PERC_PROP_NAME_VALUE_IF_ABSENT:
                        structured_data.note_validation_error(
                            f"{_PATHREPORT_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" property {_PERCENTAGE_PROPERTY_NAME} must be"
                            f" {_PERC_PROP_NAME_VALUE_IF_ABSENT} when"
                            f" {_PRESENT_PROPERTY_NAME} is"
                            f" {_PRESENT_PROPERTY_VALUE_NO}."
                        )
