from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports if any Library items defined in the spreadsheet (StructuredDataSet)
# are missing the strand property in LibraryPreparation if they are linked to RNA Analyte items
_LIBRARY_SCHEMA_NAME = "Library"
_ANALYTE_PROPERTY_NAME = "analytes"
_LIBRARY_PREP_PROPERTY_NAME = "library_preparation"
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
                        if _LIBRARY_PREP_PROPERTY_NAME in item:
                            if library_prep := [
                                lp_item
                                for lp_item in structured_data.data.get(
                                    _LIBRARY_PREP_SCHEMA_NAME
                                )
                                if lp_item.get("submitted_id")
                                == item.get(_LIBRARY_PREP_PROPERTY_NAME)
                            ][0]:
                                if _STRAND_PROPERTY_NAME not in library_prep:
                                    structured_data.note_validation_error(
                                        f"{_LIBRARY_SCHEMA_NAME}:"
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep.get('submitted_id')}"
                                        f" requires property {_STRAND_PROPERTY_NAME} for RNA libraries: {submitted_id}"
                                    )
                        else:
                            structured_data.note_validation_error(
                                f"{_LIBRARY_SCHEMA_NAME}:"
                                f" {_LIBRARY_PREP_SCHEMA_NAME} property {_STRAND_PROPERTY_NAME}"
                                f" is required for RNA libraries: {submitted_id}"
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
                            ][0]:
                                if _STRAND_PROPERTY_NAME in library_prep:
                                    structured_data.note_validation_error(
                                        f" {_LIBRARY_PREP_SCHEMA_NAME} item {library_prep.get('submitted_id')}:"
                                        f" property {_STRAND_PROPERTY_NAME} is only for RNA libraries"
                                    )