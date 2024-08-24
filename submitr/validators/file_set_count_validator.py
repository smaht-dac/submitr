from typing import List
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_sheet_hook


@structured_data_validator_sheet_hook("FileSet")
def _file_set_count_validator(structured_data: StructuredDataSet, schema: str, data: List[dict]) -> None:
    structured_data.data[schema] = data
    return data
