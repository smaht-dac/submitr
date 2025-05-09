from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports if any UnalignedRead items that are paired fastqs defined in the spreadsheet (StructuredDataSet)
# are paired appropriately to the same FileSet with the R2 file paired to the R1 file
_UNALIGNED_READS_SCHEMA_NAME = "UnalignedReads"
_FILE_SETS_PROPERTY_NAME = "file_sets"
_READ_PAIR_NUMBER_PROPERTY_NAME = "read_pair_number"
_PAIRED_WITH_PROPERTY_NAME = "paired_with"


@structured_data_validator_finish_hook
def _paired_read_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_UNALIGNED_READS_SCHEMA_NAME), list):
        return
    for item in data:
        if _FILE_SETS_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if _PAIRED_WITH_PROPERTY_NAME in item:
                # paired_with is present
                if item.get(_READ_PAIR_NUMBER_PROPERTY_NAME) != "R2":
                    #read_pair_number is not R2
                    structured_data.note_validation_error(
                        f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                        f" item {submitted_id}"
                        f" property paired_with is only for R2 files."
                        f" File read_pair_number is"
                        f" {item.get(_READ_PAIR_NUMBER_PROPERTY_NAME)}."
                    )
                if (paired_file := [
                    paired_file_item
                    for paired_file_item in structured_data.data.get(_UNALIGNED_READS_SCHEMA_NAME)
                    if paired_file_item.get("submitted_id") == item.get(_PAIRED_WITH_PROPERTY_NAME)
                ]):
                    paired_file_set = paired_file[0].get(_FILE_SETS_PROPERTY_NAME)
                    read_pair_number = paired_file[0].get(_READ_PAIR_NUMBER_PROPERTY_NAME)
                    if item.get(_FILE_SETS_PROPERTY_NAME) != paired_file_set:
                        # paired files have different file sets
                        structured_data.note_validation_error(
                            f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" paired_with file must be linked to the same FileSet."
                            f" R2 file linked to file set {item.get(_FILE_SETS_PROPERTY_NAME)}"
                            f" and R1 file linked to file set {paired_file_set}."
                        )
                    if read_pair_number != "R1":
                        # paired file is not R1
                        structured_data.note_validation_error(
                            f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" paired_with file must have read_pair_number of R1."
                            f" Linked file read_pair_number is"
                            f" {read_pair_number}."
                        )
            else:
                # paired_with is not present
                if item.get(_READ_PAIR_NUMBER_PROPERTY_NAME) == "R2":
                    #read_pair_number is R2
                    structured_data.note_validation_error(
                        f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                        f" item {submitted_id}"
                        f" property paired_with is required for R2 files"
                        f" to link the associated R1 file."
                    )
