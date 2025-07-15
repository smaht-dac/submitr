from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports if any Library items defined in the spreadsheet (StructuredDataSet)
# are missing the strand property in LibraryPreparation if they are linked to RNA Analyte items
# or if they are missing the rna_seq_protocol property if that are linked to an RNA-Seq Assay item.
# Also reports if non-RNA Library items are linked to LibraryPreparation items with either of these
# properties.

# NOTE: Currently only works for new POSTs where none of the items checked are already present on the
# portal and not present in the spreadsheet as their own item rows (e.g. a Library references a LibraryPreparation
# item that is already present on the portal but is not in the LibraryPreparation sheet will not be checked).
_LIBRARY_SCHEMA_NAME = "Library"
_ANALYTE_PROPERTY_NAME = "analytes"
_ASSAY_PROPERTY_NAME = "assay"
_RNA_SEQ = "bulk_rna_seq"
_LIBRARY_PREP_PROPERTY_NAME = "library_preparation"
_RNA_SEQ_PROTOCOL = "rna_seq_protocol"
_ANALTYE_SCHEMA_NAME = "Analyte"
_MOLECULE_PROPERTY_NAME = "molecule"
_RNA_VALUE_NAME = "RNA"
_LIBRARY_PREP_SCHEMA_NAME = "LibraryPreparation"
_STRAND_PROPERTY_NAME = "strand"


@structured_data_validator_finish_hook
def _library_prep_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_LIBRARY_SCHEMA_NAME), list):
        return
    for item in data:
        if _ANALYTE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if isinstance(
                analytes := [
                    analyte_item
                    for analyte_item in structured_data.data.get(_ANALTYE_SCHEMA_NAME)
                    if analyte_item.get("submitted_id")
                    in item.get(_ANALYTE_PROPERTY_NAME)
                ],
                list,
            ):
                for analyte in analytes:
                    if _RNA_VALUE_NAME in analyte.get(_MOLECULE_PROPERTY_NAME):
                        # RNA analyte
                        if _LIBRARY_PREP_PROPERTY_NAME in item:
                            # library prep item present
                            if library_prep := [
                                lp_item
                                for lp_item in structured_data.data.get(
                                    _LIBRARY_PREP_SCHEMA_NAME, []
                                )
                                if lp_item.get("submitted_id")
                                == item.get(_LIBRARY_PREP_PROPERTY_NAME)
                            ]:
                                assay = item.get(_ASSAY_PROPERTY_NAME)
                                if _STRAND_PROPERTY_NAME not in library_prep[0]:
                                    # missing strand property
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}: {submitted_id}"
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep[0].get('submitted_id')}"
                                        f" property {_STRAND_PROPERTY_NAME} is required for RNA"
                                        f" libraries"
                                    )
                                if assay == _RNA_SEQ and _RNA_SEQ_PROTOCOL not in library_prep[0]:
                                    # missing rna_seq_protocol for RNA-Seq
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}: {submitted_id}"
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep[0].get('submitted_id')}"
                                        f" property {_RNA_SEQ_PROTOCOL} is required for RNA-Seq"
                                        f" libraries"
                                    )
                        else:
                            # library prep item not present
                            structured_data.note_validation_error(
                                f"{_LIBRARY_SCHEMA_NAME}: {submitted_id}"
                                f" {_LIBRARY_PREP_SCHEMA_NAME} property {_STRAND_PROPERTY_NAME}"
                                f" is required for RNA libraries"
                            )
                    else:
                        if _LIBRARY_PREP_PROPERTY_NAME in item:
                            if library_prep := [
                                lp_item
                                for lp_item in structured_data.data.get(
                                    _LIBRARY_PREP_SCHEMA_NAME
                                )
                                if lp_item.get("submitted_id")
                                == item.get(_LIBRARY_PREP_PROPERTY_NAME)
                            ]:
                                if _STRAND_PROPERTY_NAME in library_prep[0]:
                                    # DNA analyte with strand property
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}: {submitted_id}"
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep[0].get('submitted_id')}:"
                                        f" property {_STRAND_PROPERTY_NAME} is only for RNA libraries"
                                    )
                                if _RNA_SEQ_PROTOCOL in library_prep[0]:
                                    # DNA analyte with rna_seq_protocol property
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}: {submitted_id}"
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep[0].get('submitted_id')}:"
                                        f" property {_RNA_SEQ_PROTOCOL} is only for RNA libraries"
                                    )
