from dcicutils.structured_data import StructuredDataSet
from dcicutils.misc_utils import to_integer
from submitr.validators.decorators import structured_data_validator_finish_hook

# Sanity check the pseudo-column FileSet.expected_file_count which should be equal,
# for each FileSet row, to all of the actual file type (e.g. AlignedReads) rows
# which refer to it (via its submitted_id) by is file_set property. See:
# https://docs.google.com/document/d/1zj-edWR1ugqhd6ZxC07Rkq6M7I_jqiR-pO598gFg0p8

_FILE_SET_SCHEMA_NAME = "FileSet"
_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME = "expected_file_count"
_FILE_SCHEMA_NAMES = ["AlignedReads", "UnalignedReads", "VariantCalls"]


@structured_data_validator_finish_hook
def _file_set_count_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_FILE_SET_SCHEMA_NAME), list):
        return
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
                    structured_data.note_validation_error(
                        f"{_FILE_SET_SCHEMA_NAME}.{_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME}"
                        f" ({expected_file_count}) does not match the actual number of ({actual_file_count})"
                        f" files defined for this set: {submitted_id}")
                    pass
            del item[_FILE_SET_EXPECTED_FILE_COUNT_PSEUDO_COLUMN_NAME]
