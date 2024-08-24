from submitr.validators.utils.structured_data_validator_hook import structured_data_validator_sheet_hook
from dcicutils.structured_data import StructuredDataSet


@structured_data_validator_sheet_hook(["CellLine", "Analyte", "FileSet"])
def duplicate_row_validator(structured_data: StructuredDataSet, sheet_name: str, data: dict) -> None:
    print(f'\nxxxxx/validate[{sheet_name}')
