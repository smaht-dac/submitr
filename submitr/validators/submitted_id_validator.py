from typing import Any
from dcicutils.misc_utils import run_concurrently  # noqa
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_hook, structured_data_validator_finish_hook

# Validator for the submitted_id column which is checked for EVERY schema (aka type or sheet)
# within the submission metadata. We use the smaht-portal /validators/submitted_id/{submitted_id}
# endpoint/API to do the actual validation. But for better performance we do this in parallel
# as much as possible. And to do this we need to save up the list of all submitted_id values,
# within the main _submitted_id_validator function. Then when the _submitted_id_validator_finish
# function is called at the end of the submission metadata processing, we make the smaht-portal
# API calls concurrently (via run_concurrently); this function also checks-for/reports duplicates.

_STRUCTURED_DATA_HOOK_PROPERTY = "__submitted_id_validator__"
_NTHREADS_FOR_SMAHT_PORTAL_API_CALLS = 6


@structured_data_validator_hook("submitted_id")
def _submitted_id_validator(structured_data: StructuredDataSet, schema: str,
                            column: str, row: int, value: Any, **kwargs) -> Any:

    # Squirrel away the list of all seen submitted_id values within a hidden property
    # in the StructuredDataSet object. We save these up and process/validate them all
    # at once in _submitted_id_validator_finish so that we can do themt in parallel.
    if not hasattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY):
        setattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY, {})
    submitted_ids = getattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY)
    if schema not in submitted_ids:
        submitted_ids[schema] = []
    # If we decide at some point that we don't want to store the entire
    # submitted_id list in memory, we could kick off the calls here in
    # parallel _NTHREADS_FOR_SMAHT_PORTAL_API_CALLS at a time.
    submitted_ids[schema].append({"value": value, "row": row})
    return value


@structured_data_validator_finish_hook
def _submitted_id_validator_finish(structured_data: StructuredDataSet, **kwargs) -> None:

    if not hasattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY):
        return
    if not (submitted_ids := getattr(structured_data, _STRUCTURED_DATA_HOOK_PROPERTY)):
        return
    valid_submission_centers = kwargs.get("valid_submission_centers")

    def validate_submitted_id(submitted_id: str, schema: str, row: int) -> None:
        nonlocal structured_data, valid_submission_centers
        path = f"/validators/submitted_id/{submitted_id}"
        if valid_submission_centers:
            path += f"?submission_centers={valid_submission_centers}"
        # Here is the actual call to the /validators/submitted_id/{submitted_id} endpoint/API.
        if result := structured_data.portal.get_metadata(path):
            if (result := result.get("status")) != "OK":
                structured_data.note_validation_error(result, schema, row + 1)

    # The submitted_id_validators array here will be the list of functions/lambdas to be called
    # in parallel (see run_concurrently call below) for better performance. This same
    # loop also checks for duplicate submitted_id values within each schema/type/sheet.
    submitted_id_validators = []
    for schema in submitted_ids:
        uniques = {}
        duplicates = []
        for item in submitted_ids[schema]:
            submitted_id = item.get("value")
            row = item.get("row")
            # This adds the actual validation function/lambda to the submitted_id_validators list.
            submitted_id_validators.append(
                lambda submitted_id=submitted_id, schema=schema, row=row:
                    validate_submitted_id(submitted_id, schema, row))
            if submitted_id not in uniques:
                uniques[submitted_id] = row
            else:
                duplicates.append(item)
        for duplicate in duplicates:
            duplicate_submitted_id = duplicate["value"]
            validation_error = (f"Duplicate submission_id: {duplicate_submitted_id}"
                                f" (first seen on item: {uniques[duplicate_submitted_id] + 1})")
            structured_data.note_validation_error(validation_error, schema, row + 1)
    # This call kicks off calls to the validation functions/lambdas (in submitted_id_validators)
    # in parallel, up to _NTHREADS_FOR_SMAHT_PORTAL_API_CALLS threads at a time.
    run_concurrently(submitted_id_validators, nthreads=_NTHREADS_FOR_SMAHT_PORTAL_API_CALLS)
