from typing import List
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_sheet_hook

_FILE_SET_EXPECTED_FILE_COUNT_COLUMN_NAME = "expected_file_count"
_FILE_SCHEMA_NAMES = ["AlignedReads", "UnalignedReads", "VariantCalls"]


@structured_data_validator_sheet_hook("FileSet")
def _file_set_count_validator(structured_data: StructuredDataSet, schema: str, data: List[dict]) -> None:
    for item in data:
        if _FILE_SET_EXPECTED_FILE_COUNT_COLUMN_NAME in item:
            if ((submitted_id := item.get("submitted_id")) and
                isinstance(expected_file_count := item[_FILE_SET_EXPECTED_FILE_COUNT_COLUMN_NAME], int)):  # noqa
                actual_file_count = 0
                for file_schema_name in _FILE_SCHEMA_NAMES:
                    if isinstance(files := structured_data.data.get(file_schema_name), list):
                        for file in files:
                            if file.get("submitted_id") == submitted_id:
                                actual_file_count += 1
                if actual_file_count != expected_file_count:
                    # TODO: Error
                    import pdb ; pdb.set_trace()  # noqa
                    pass  # TODO
            del item[_FILE_SET_EXPECTED_FILE_COUNT_COLUMN_NAME]
