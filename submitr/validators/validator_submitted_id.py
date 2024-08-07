from typing import Any, Optional, Tuple
from dcicutils.misc_utils import run_concurrently  # noqa
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorator import validator

# Validator for the submitted_id column which is checked for EVERY schema (aka type or sheet)
# within the submission etadata. We use the smaht-portal /validators/submitted_id/{submitted_id}
# endpoint/API to do the actual validation. But for better performance we do this in parallel
# as much as possible. And to do this we need to save up the list of all submitted_id values,
# within the main _validator_submitted_id function. Then when the _validator_finish_submitted_id
# function is called at this end of the submission metadata processing, we make the smaht-portal
# API calls concurrently; this function also checks for duplicates.

_STRUCTURED_DATA_HOOK_PROPERTY = "__validator_submitted_id__"


@validator("submitted_id")
def _validator_submitted_id(structured_data: StructuredDataSet,
                            schema_name: str, column_name: str, row_number: int,
                            value: Any, **kwargs) -> Tuple[Any, Optional[str]]:

    if not hasattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY):
        setattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY, {})
    validator_submitted_ids = getattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY)
    if schema_name not in validator_submitted_ids:
        validator_submitted_ids[schema_name] = []
    validator_submitted_ids[schema_name].append({"value": value, "row": row_number})
    return value, None


@validator("submitted_id", finish=True)
def _validator_finish_submitted_id(structured_data: StructuredDataSet, **kwargs) -> None:

    if not hasattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY):
        return

    validator_submitted_ids = getattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY)
    valid_submission_centers = kwargs.get("valid_submission_centers")

    def validate_submitted_id(submitted_id: str, schema_name: str, row_number: int) -> None:
        nonlocal structured_data, valid_submission_centers
        path = f"/validators/submitted_id/{submitted_id}"
        if valid_submission_centers:
            path += f"?submission_centers={valid_submission_centers}"
        if result := structured_data.portal.get_metadata(path):
            if (result := result.get("status")) != "OK":
                structured_data.note_validation_error(result, schema_name, row_number + 1)

    submitted_ids = []
    for schema_name in validator_submitted_ids:
        uniques = {}
        duplicates = []
        for item in validator_submitted_ids[schema_name]:
            submitted_id = item.get("value")
            row_number = item.get("row")
            submitted_ids.append(lambda submitted_id=submitted_id, schema_name=schema_name, row_number=row_number:
                                 validate_submitted_id(submitted_id, schema_name, row_number))
            if submitted_id in uniques:
                duplicates.append(item)
            else:
                uniques[submitted_id] = row_number
        if duplicates:
            for duplicate in duplicates:
                duplicate_submitted_id = duplicate["value"]
                validation_error = (f"Duplicate submission_id: {duplicate_submitted_id}"
                                    f" (first seen on item: {uniques[duplicate_submitted_id] + 1})")
                structured_data.note_validation_error(validation_error, schema_name, row_number + 1)
    if submitted_ids:
        run_concurrently(submitted_ids, nthreads=5)
