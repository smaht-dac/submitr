from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# This "validator" does not use any of the decorator hooks defined in this directory;
# it is a simple function (require_strand) called from submission.py.
# It reports if and LibraryPrepration items defined in the spreadsheet (StructuredDataSet) are missing the strand property if they are linked to an RNA library
_LIBRARY_SCHEMA_NAME = "Library"
_ANALYTE_PROPERTY_NAME = 'analytes'
_LIBRARY_PREPARATION_PROPERTY_NAME = 'library_preparation'
_ANALTYE_SCHEMA_NAME = "Analyte"
_MOLECULE_PROPERTY_NAME = "molecule"
_RNA_VALUE_NAME = "RNA"
_LIBRARY_PREP_SCHEMA_NAME = "LibraryPreparation"
_STRAND_PROPERTY_NAME = "strand"


@structured_data_validator_finish_hook
def _strand_required(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_LIBRARY_SCHEMA_NAME), list):
        return
    for item in data:
        if _ANALYTE_PROPERTY_NAME in item and (submitted_id := item.get("submitted_id")):
            if isinstance(analytes := structured_data.data.get(_ANALTYE_SCHEMA_NAME), list):
                for analyte in analytes:
                    if _RNA_VALUE_NAME in analyte.get(_MOLECULE_PROPERTY_NAME):
                        if _LIBRARY_PREPARATION_PROPERTY_NAME in item:
                            if isinstance(library_prep := structured_data.data.get(_LIBRARY_PREP_SCHEMA_NAME), dict):
                                if _STRAND_PROPERTY_NAME not in library_prep:
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}."
                                        f" ({_LIBRARY_PREP_SCHEMA_NAME} Property {_STRAND_PROPERTY_NAME} is required for RNA libraries: {submitted_id}"
                                    )
                        else:
                            structured_data.note_validation_error(
                                f"{_LIBRARY_SCHEMA_NAME}."
                                f" ({_LIBRARY_PREP_SCHEMA_NAME} Property {_STRAND_PROPERTY_NAME} is required for RNA libraries: {submitted_id}"
                            )
