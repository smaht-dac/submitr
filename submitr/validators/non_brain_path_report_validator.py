from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# Constants
_SCHEMA_NAME = "NonBrainPathologyReport"
_TARGET_TISSUES_PROPERTY = "target_tissues"
_NON_TARGET_TISSUES_PROPERTY = "non_target_tissues"
_PATHOLOGIC_FINDINGS_PROPERTY = "pathologic_findings"


# Validator 1: Target Tissues
@structured_data_validator_finish_hook
def _non_brain_pathology_target_tissues_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates target_tissues conditional logic:
    - If target_tissue_present = "No": target_tissue_percentage must be "0" and target_tissue_autolysis_score must be empty
    - If target_tissue_present = "Yes": target_tissue_percentage must be non-zero enum value and target_tissue_autolysis_score must be present
    """
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        if not isinstance(target_tissues := item.get(_TARGET_TISSUES_PROPERTY), list):
            continue

        for index, target_tissue in enumerate(target_tissues):
            subtype = target_tissue.get("target_tissue_subtype", "unknown")
            present = target_tissue.get("target_tissue_present")
            percentage = target_tissue.get("target_tissue_percentage")
            autolysis_score = target_tissue.get("target_tissue_autolysis_score")

            if present == "No":
                # When not present, percentage must be "0"
                if percentage != "0":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(target_tissue_subtype: {subtype}): "
                        f"when target_tissue_present is 'No', "
                        f"target_tissue_percentage must be '0'"
                    )

                # When not present, autolysis_score must be empty/absent
                if autolysis_score is not None:
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(target_tissue_subtype: {subtype}): "
                        f"when target_tissue_present is 'No', "
                        f"target_tissue_autolysis_score must be empty"
                    )

            elif present == "Yes":
                # When present, percentage must exist
                if percentage is None:
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(target_tissue_subtype: {subtype}): "
                        f"when target_tissue_present is 'Yes', "
                        f"target_tissue_percentage must be provided"
                    )
                # When present, percentage cannot be "0"
                elif percentage == "0":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(target_tissue_subtype: {subtype}): "
                        f"when target_tissue_present is 'Yes', "
                        f"target_tissue_percentage cannot be '0'"
                    )

                # When present, autolysis_score must exist
                if autolysis_score is None:
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(target_tissue_subtype: {subtype}): "
                        f"when target_tissue_present is 'Yes', "
                        f"target_tissue_autolysis_score must be provided"
                    )


# Validator 2: Non-Target Tissues
@structured_data_validator_finish_hook
def _non_brain_pathology_non_target_tissues_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates non_target_tissues conditional logic:
    - If non_target_tissue_present = "Yes": non_target_tissue_percentage must be provided
    - If non_target_tissue_present = "No": non_target_tissue_percentage must be empty
    """
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        if not isinstance(
            non_target_tissues := item.get(_NON_TARGET_TISSUES_PROPERTY), list
        ):
            continue

        for index, non_target_tissue in enumerate(non_target_tissues):
            subtype = non_target_tissue.get("non_target_tissue_subtype", "unknown")
            present = non_target_tissue.get("non_target_tissue_present")
            percentage = non_target_tissue.get("non_target_tissue_percentage")

            if present == "Yes":
                # When present, percentage must exist and have a value
                if percentage is None or percentage == "":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_NON_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(non_target_tissue_subtype: {subtype}): "
                        f"when non_target_tissue_present is 'Yes', "
                        f"non_target_tissue_percentage must be provided"
                    )

            elif present == "No":
                # When not present, percentage must be absent
                if percentage is not None and percentage != "":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_NON_TARGET_TISSUES_PROPERTY}[{index}] "
                        f"(non_target_tissue_subtype: {subtype}): "
                        f"when non_target_tissue_present is 'No', "
                        f"non_target_tissue_percentage must be empty"
                    )


# Validator 3: Pathologic Findings
@structured_data_validator_finish_hook
def _non_brain_pathology_findings_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validates pathologic_findings conditional logic:
    - If finding_present = "Yes": finding_description and finding_percentage must be provided
    """
    if not isinstance(data := structured_data.data.get(_SCHEMA_NAME), list):
        return

    for item in data:
        submitted_id = item.get("submitted_id", "unknown")

        if not isinstance(
            pathologic_findings := item.get(_PATHOLOGIC_FINDINGS_PROPERTY), list
        ):
            continue

        for index, finding in enumerate(pathologic_findings):
            finding_type = finding.get("finding_type", "unknown")
            present = finding.get("finding_present")
            description = finding.get("finding_description")
            percentage = finding.get("finding_percentage")

            if present == "Yes":
                # When present, description must exist and have a non-empty value
                if description is None or (
                    isinstance(description, str) and description.strip() == ""
                ):
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_PATHOLOGIC_FINDINGS_PROPERTY}[{index}] "
                        f"(finding_type: {finding_type}): "
                        f"when finding_present is 'Yes', "
                        f"finding_description must be provided"
                    )

                # When present, percentage must exist
                if percentage is None or percentage == "":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_PATHOLOGIC_FINDINGS_PROPERTY}[{index}] "
                        f"(finding_type: {finding_type}): "
                        f"when finding_present is 'Yes', "
                        f"finding_percentage must be provided"
                    )
            elif present == "No":
                # When not present, percentage must be absent or empty
                if percentage is not None and percentage != "":
                    structured_data.note_validation_error(
                        f"{_SCHEMA_NAME}: item {submitted_id} "
                        f"{_PATHOLOGIC_FINDINGS_PROPERTY}[{index}] "
                        f"(finding_type: {finding_type}): "
                        f"when finding_present is 'No', "
                        f"finding_percentage must be empty"
                    )
