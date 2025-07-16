from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports if any Analyte items that have molecule RNA
# do not have the `rna_integrity_number` property filled out
# and if non-RNA Analyte items have the `rna_integrity_number` filled out
_ANALYTE_SCHEMA_NAME = "Analyte"
_RIN_PROPERTY_NAME = "rna_integrity_number"
_MOLECULE_PROPERTY_NAME = "molecule"
_RNA_VALUE = "RNA"


@structured_data_validator_finish_hook
def _analyte_rin_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_ANALYTE_SCHEMA_NAME), list):
        return
    for item in data:
        if _MOLECULE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if _RNA_VALUE in item.get(_MOLECULE_PROPERTY_NAME) and _RIN_PROPERTY_NAME not in item:
                # rna and rna_integrity_number not present
                structured_data.note_validation_error(
                    f"{_ANALYTE_SCHEMA_NAME}:"
                    f" item {submitted_id}"
                    f" property {_RIN_PROPERTY_NAME} is required"
                    f" for {_RNA_VALUE} analytes."
                )
            elif _RNA_VALUE not in item.get(_MOLECULE_PROPERTY_NAME) and _RIN_PROPERTY_NAME in item:
                # not rna and rna_integrity_number present
                structured_data.note_validation_error(
                    f"{_ANALYTE_SCHEMA_NAME}:"
                    f" item {submitted_id}"
                    f" property {_RIN_PROPERTY_NAME} only allowed"
                    f" for {_RNA_VALUE} analytes."
                )
