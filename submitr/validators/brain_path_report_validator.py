from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

print(f"DEBUG: Loading brain_path_report_validator module")
print(f"DEBUG: Decorator type: {type(structured_data_validator_finish_hook)}")

# Constants
_SCHEMA_NAME = "BrainPathologyReport"
_BRAIN_SUBREGIONS_PROPERTY = "brain_subregions"

_PRESENT_SUFFIX = "_present"
_DESCRIPTION_SUFFIX = "_description"

# Age-related staining result
_AGE_RELATED_STAINING_FIELDS = [
    "abc_score_A",
    "abc_score_B",
    "abc_score_C",
    "cerad_score",
    "ad_neuropathologic_change_level",
    "braak_pd",
    "small_vessel_disease",
    "braak_and_braak_ad",
    "thal",
    "caa_vonsattel",
    "mckeith",
    "vonsattel_hd",
]


# Neuropathology Present/Description Pairs
@structured_data_validator_finish_hook
def _brain_pathology_neuropathology_present_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates all _present/_description field pairs at the top level:
    - If <field>_present = "Yes": the corresponding <field>_description must
    be provided and non-empty.
    """
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        for field, value in item.items():
            if not field.endswith(_PRESENT_SUFFIX) or value != "Yes":
                continue

            stem = field[: -len(_PRESENT_SUFFIX)]
            description_field = f"{stem}{_DESCRIPTION_SUFFIX}"
            description = item.get(description_field)

            if description is None or (
                isinstance(description, str) and description.strip() == ""
            ):
                structured_data.note_validation_error(
                    f"{_SCHEMA_NAME}: item {submitted_id}: "
                    f"when {field} is 'Yes', "
                    f"{description_field} must be provided"
                )


# Brain Subregions present
@structured_data_validator_finish_hook
def _brain_pathology_subregions_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates brain_subregions conditional logic:
    - If is_present = "Yes": tissue_autolysis_score must be provided
    - If is_present = "No": tissue_autolysis_score must be absent
    """
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        if not isinstance(
            brain_subregions := item.get(_BRAIN_SUBREGIONS_PROPERTY), list
        ):
            continue

        for index, subregion in enumerate(brain_subregions):
            subregion_name = subregion.get("subregion", "unknown")
            is_present = subregion.get("is_present")
            autolysis_score = subregion.get("tissue_autolysis_score")

            if is_present == "Yes":
                if autolysis_score is None:
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_BRAIN_SUBREGIONS_PROPERTY}[{index}] "
                        f"(subregion: {subregion_name}): "
                        f"when is_present is 'Yes', "
                        f"tissue_autolysis_score must be provided"
                    )

            elif is_present == "No":
                if autolysis_score is not None:
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_BRAIN_SUBREGIONS_PROPERTY}[{index}] "
                        f"(subregion: {subregion_name}): "
                        f"when is_present is 'No', "
                        f"tissue_autolysis_score must be absent"
                    )


# Additional Age-Related Staining
@structured_data_validator_finish_hook
def _brain_pathology_age_related_staining_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates additional_age-related_staining_performed conditional logic:
    - If additional_age-related_staining_performed = "Yes": at least one of the age-related
      staining result fields must have a value
"""
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        staining_performed = item.get("additional_age-related_staining_performed")

        if staining_performed == "Yes":
            has_any_value = any(
                item.get(field) is not None and item.get(field) != ""
                for field in _AGE_RELATED_STAINING_FIELDS
            )

            if not has_any_value:
                structured_data.note_validation_error(
                    f"{_SCHEMA_NAME}: item {submitted_id}: "
                    f"when additional_age-related_staining_performed is 'Yes', "
                    f"at least one of the following fields must be provided: "
                    f"{', '.join(_AGE_RELATED_STAINING_FIELDS)}"
                )
