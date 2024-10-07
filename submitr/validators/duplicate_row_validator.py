import json
from typing import List, Optional, Tuple
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_sheet_hook

# Sheets for which we will check for duplicate rows, per:
# https://docs.google.com/document/d/1zj-edWR1ugqhd6ZxC07Rkq6M7I_jqiR-pO598gFg0p8
_DUPLICATE_ROW_DETECTION_SHEETS = [
    "AnalytePreparation",
    "Basecalling",
    "LibraryPreparation",
    "PreparationKit",
    "Sequencing",
    "Software",
    "Treatment"
]


@structured_data_validator_sheet_hook(_DUPLICATE_ROW_DETECTION_SHEETS)
def _duplicate_row_validator(structured_data: StructuredDataSet, schema: str, data: List[dict]) -> Optional[List[dict]]:
    index, duplicate_index = _find_duplicate_elements(data)
    if duplicate_index is not None:
        # When reporting the indices we add two; one because it was
        # zero-indexed (by _find_duplicate_elements), and another one for the header column.
        structured_data.note_validation_error(
            f"Duplicate rows in sheet: {schema} (items: {index + 2} and {duplicate_index + 2})", schema)


def _find_duplicate_elements(array: List[dict]) -> Tuple[Optional[int], Optional[int]]:
    if isinstance(array, list):
        seen = {}
        for index, element in enumerate(array):
            serialized_element = json.dumps(element, sort_keys=True)
            if serialized_element in seen:
                return seen[serialized_element], index
            seen[serialized_element] = index
    return None, None
