from typing import Callable, List, Optional
from dcicutils.structured_data import StructuredDataSet

# This "validator" does not use any of the decorator hooks defined in this directory;
# it is a simple function (report_unreferenced_references) called from submission.py.
# It reports any items defined in the spreadsheet (StructuredDataSet) which are not referenced
# by any other item within the spreadsheet, except we ignore items of those types specifically listed below.

_TYPES_WHICH_ARE_ALLOWED_TO_BE_UNREFERENCED = [
    "AlignedReads",
    "HistologyImage",
    "SupplementaryFile",
    "TissueSample",
    "UnalignedReads",
    "VariantCalls",
    "Demographic",
    "Diagnosis",
    "Exposure",
    "FamilyHistory",
    "MedicalTreatment",
    "DeathCircumstances",
    "TissueCollection"
]


def report_unreferenced_references(structured_data: StructuredDataSet, printf: Optional[Callable] = None) -> int:
    global _TYPES_WHICH_ARE_ALLOWED_TO_BE_UNREFERENCED
    unreferenced_items = _get_unreferenced_references(structured_data,
                                                      ignore_types=_TYPES_WHICH_ARE_ALLOWED_TO_BE_UNREFERENCED)
    if unreferenced_items:
        if not callable(printf):
            printf = print
        printf("\n- Unreferenced items:")
        for unreferenced_item in unreferenced_items:
            printf(f"  - {unreferenced_item}")
        return len(unreferenced_items)
    return 0


def _get_unreferenced_references(structured_data: StructuredDataSet,
                                 ignore_types: Optional[List[str]] = None,
                                 identifying_property_name: Optional[str] = None) -> List[str]:

    def get_item_identifying_paths(item: dict, item_type: str) -> List[str]:
        nonlocal structured_data, identifying_property_name
        if isinstance(item, dict) and isinstance(item_type, str):
            if item_identifying_value := item.get(identifying_property_name):
                identifying_paths = set()
                if item_super_type_names := structured_data.portal.get_schema_super_type_names(item_type):
                    for item_super_type_name in item_super_type_names:
                        identifying_paths.add(f"/{item_super_type_name}/{item_identifying_value}")
                identifying_paths = list(identifying_paths)
                identifying_paths.insert(0, f"/{item_type}/{item_identifying_value}")
                return identifying_paths
        return []

    if not isinstance(structured_data, StructuredDataSet):
        return []

    if not isinstance(ignore_types, list):
        ignore_types = None

    if not (isinstance(identifying_property_name, str) and identifying_property_name):
        identifying_property_name = "submitted_id"

    # Note that structured_data.resolved_refs is an array of all of the references
    # within the spreadsheet, identified by path (e.g. /Sequencer/pacbio_revio_hifi),
    # and is set up by the StructuredDataSet spreadsheet parsing process.
    resolved_refs = set(structured_data.resolved_refs)
    unreferenced_items = []

    for item_type in structured_data.data:
        if ignore_types and (item_type in ignore_types):
            continue
        for item in structured_data.data[item_type]:
            if item_identifying_paths := get_item_identifying_paths(item, item_type):
                if bool(set(item_identifying_paths) & resolved_refs) is False:
                    unreferenced_items.append(item_identifying_paths[0])

    return unreferenced_items
