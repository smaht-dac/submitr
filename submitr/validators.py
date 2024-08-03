from typing import Any, Callable, List, Optional, Tuple
from dcicutils.structured_data import Portal


def _validators_submited_id(portal: Portal, value: Any,
                            known_submission_center_names: str) -> Tuple[Any, Optional[str]]:
    url = f"/validators/submitted_id?value={value}&submission_centers={known_submission_center_names}"
    if result := portal.get_metadata(url):
        if (result := result.get("status")) != "OK":
            return value, result
    return value, None


# Keys for this may be either a column name (exact name) to validate across ALL types,
# e.g. submitted_id, in which case the value is just the function (callable) to be use
# to validate the column value; or the key may be a type name (lower cased name) whose
# value is a dictionary which contains keys representing column names within that type
# which should be validated by the corresponding function (callable) key value.
_VALIDATORS = {
    "submitted_id": _validators_submited_id
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
               known_submission_center_names: List[Any] = []) -> Tuple[Any, Optional[str]]:
    if validator := _find_validator(sheet_name, column_name):
        return validator(portal, value, known_submission_center_names=known_submission_center_names)
    return value, None
