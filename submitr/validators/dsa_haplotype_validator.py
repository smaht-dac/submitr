from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports any SupplementaryFile items that are DSA fasta files are missing the haplotype property

_SUPP_FILE_SCHEMA_NAME = "SupplementaryFile"
_FILE_FORMAT_PROPERTY_NAME = "file_format"
_HAPLOTYPE_PROPERTY_NAME = "haplotype"
_DATA_TYPE_PROPERTY_NAME = "data_type"
_DSA_PROPERTY_NAME = "donor_specific_assembly"

_FASTA_FILE_FORMAT = "fa"
_DSA_DATA_TYPE = "DSA"

@structured_data_validator_finish_hook
def _dsa_haplotype_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_SUPP_FILE_SCHEMA_NAME), list):
        return
    for item in data:
        if _DATA_TYPE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if item.get(_FILE_FORMAT_PROPERTY_NAME) == _FASTA_FILE_FORMAT:
                if _DSA_DATA_TYPE in item.get(_DATA_TYPE_PROPERTY_NAME):
                    if _HAPLOTYPE_PROPERTY_NAME not in item:
                        structured_data.note_validation_error(
                            f"{_SUPP_FILE_SCHEMA_NAME}: {submitted_id}"
                            f" property {_HAPLOTYPE_PROPERTY_NAME}"
                            f" is required for DSA fasta files"
                        )
                    if _DSA_PROPERTY_NAME not in item:
                        structured_data.note_validation_error(
                            f"{_SUPP_FILE_SCHEMA_NAME}: {submitted_id}"
                            f" property {_DSA_PROPERTY_NAME}"
                            f" is required for DSA fasta files"
                        )