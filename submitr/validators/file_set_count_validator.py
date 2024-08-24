from typing import List
from dcicutils.structured_data import StructuredDataSet
from dcicutils.misc_utils import to_integer
from submitr.validators.decorators import structured_data_validator_sheet_hook

_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME = "expected_file_count"
_FILE_SCHEMA_NAMES = ["AlignedReads", "UnalignedReads", "VariantCalls"]


# TODO: The FileSet sheet needs to come after and file sheets for this to work.
@structured_data_validator_sheet_hook("FileSet")
def _file_set_count_validator(structured_data: StructuredDataSet, schema: str, data: List[dict]) -> None:
    for item in data:
        if _FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME in item:
            if ((submitted_id := item.get("submitted_id")) and
                ((expected_file_count :=
                  to_integer(item[_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME], fallback=-1)) >= 0)):  # noqa
                actual_file_count = 0
                for file_schema_name in _FILE_SCHEMA_NAMES:
                    if isinstance(files := structured_data.data.get(file_schema_name), list):
                        for file in files:
                            if file.get("submitted_id") == submitted_id:
                                actual_file_count += 1
                if actual_file_count != expected_file_count:
                    structured_data.note_validation_error("TODO")
                    pass
            del item[_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME]
