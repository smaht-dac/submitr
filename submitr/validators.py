from typing import Any, Callable, Optional, Tuple
from dcicutils.structured_data import Portal


def _validator_submited_id(portal: Portal, value: Any,
                           valid_submission_centers: Optional[str] = None) -> Tuple[Any, Optional[str]]:
    path = f"/validators/submitted_id/{value}"
    if valid_submission_centers:
        path += f"?submission_centers={valid_submission_centers}"
    if result := portal.get_metadata(path):
        if (result := result.get("status")) != "OK":
            return value, result
    return value, None


# Keys for this may be either a column name (exact name) to validate across ALL types,
# e.g. submitted_id, in which case the value is just the function (callable) to be use
# to validate the column value; or the key may be a type name (lower cased name) whose
# value is a dictionary which contains keys representing column names within that type
# which should be validated by the corresponding function (callable) key value.
_VALIDATORS = {
    "submitted_id": _validator_submited_id
}


def _find_validator(sheet_name: str, column_name: str) -> Optional[Callable]:
    if column_validator := _VALIDATORS.get(column_name):
        return column_validator
    elif ((type_validators := _VALIDATORS.get(sheet_name.lower())) and
          (type_column_validator := type_validators.get(column_name))):
        return type_column_validator
    return None


def validators(portal: Portal,
               sheet_name: str, column_name: str,
               value: Any,
               valid_submission_centers: Optional[str] = None) -> Tuple[Any, Optional[str]]:
    if validator := _find_validator(sheet_name, column_name):
        return validator(portal, value, valid_submission_centers=valid_submission_centers)
    return value, None
