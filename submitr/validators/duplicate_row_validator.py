from submitr.validators.utils.structured_data_validator_hook import structured_data_validator_sheet_hook
from dcicutils.structured_data import StructuredDataSet

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
    print(f"\nTODO: DUPLICATE ROW VALIDATOR: [{sheet_name}]")
