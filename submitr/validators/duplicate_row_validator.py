import json
from typing import List
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.utils.structured_data_validator_hook import structured_data_validator_sheet_hook

# Sheet for which we will check for duplicate rows, per:
# https://docs.google.com/document/d/1zj-edWR1ugqhd6ZxC07Rkq6M7I_jqiR-pO598gFg0p8
_DUPLICATE_ROW_DETECTIONS_SHEETS = [
    "AnalytePreparation",
    "Basecalling",
    "LibraryPreparation",
    "PreparationKit",
    "Sequencing",
    "Software",
    "Treatment"
]


@structured_data_validator_sheet_hook(_DUPLICATE_ROW_DETECTIONS_SHEETS)
def duplicate_row_validator(structured_data: StructuredDataSet, sheet_name: str, data: dict) -> None:
    if _has_duplicate_elements(data):
        structured_data.note_validation_error(f"Duplicate rows in sheet: {sheet_name}", sheet_name, 0)
        print(f"\nTODO: DUPLICATE ROW VALIDATOR: [{sheet_name}] -> DUPLICATES!")
    else:
        print(f"\nTODO: DUPLICATE ROW VALIDATOR: [{sheet_name}] -> OK")


def _has_duplicate_elements(array: List[dict]) -> bool:
    seen = set()
    for element in array:
        serialized_element = json.dumps(element, sort_keys=True)
        if serialized_element in seen:
            return True
        seen.add(serialized_element)
    return False
