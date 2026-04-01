from copy import deepcopy
import io
import json
import os
from typing import Any, List, Optional
from dcicutils.data_readers import Excel, ExcelSheetReader
from dcicutils.misc_utils import to_boolean, to_float, to_integer

# This module implements a custom Excel spreadsheet class which supports "custom column mappings",
# meaning that, at a very low/early level in processing, the columns/values in the spreadsheet
# can be redefined/remapped to different columns/values.
#
# Previously the mapping config was defined by a static JSON file (config/custom_column_mappings.json)
# and fetched from GitHub on startup. It is now fetched live from the portal via:
#
#   GET /search/?type=GenericQcConfig&tags=external_quality_metrics
#
# Each GenericQcConfig item returned is expected to have the structure:
#
#   {
#     "sheet_name": "DuplexSeq_ExternalQualityMetric",   # Excel sheet name(s) this config applies to
#     "mapping_name": "duplexseq_external_quality_metric",  # internal key
#     "fields": [
#       {
#         "column": "total_raw_reads_sequenced",
#         "key": "Total Raw Reads Sequenced",
#         "tooltip": "# of reads (150bp)",
#         "value_type": "integer"     # one of: integer, float, boolean, string
#       },
#       ...
#     ]
#   }
#
# From these items the code reconstructs the same internal config dict structure that was
# previously loaded from JSON (see comments below for format details).  If the portal query
# fails or returns nothing, the local JSON file (config/custom_column_mappings.json) is used
# as a fallback so that existing behaviour is preserved.
#
# The mapping config can be thought of as a virtual preprocessing step on the spreadsheet.
# For EXAMPLE, so the spreadsheet author can specify single columns like this:
#
#   total_raw_reads_sequenced: 11870183
#   total_raw_bases_sequenced: 44928835584
#
# But this will be mapped, i.e the system will act AS-IF we instead had these columns/values:
#
#   qc_values#0.derived_from: total_raw_reads_sequenced
#   qc_values#0.value:        11870183
#   qc_values#0.key:          Total Raw Reads Sequenced
#   qc_values#0.tooltip:      # of reads (150bp)
#   qc_values#1.derived_from: total_raw_bases_sequenced
#   qc_values#1.value:        44928835584
#   qc_values#1.key:          Total Raw Bases Sequenced
#   qc_values#1.tooltip:      None
#
# The internal config dict (whether built from the portal or loaded from JSON) looks like:
#
#   {
#     "sheet_mappings": {
#       "DuplexSeq_ExternalQualityMetric": "duplexseq_external_quality_metric"
#     },
#     "column_mappings": {
#       "duplexseq_external_quality_metric": {
#         "total_raw_reads_sequenced": {
#           "qc_values#.derived_from": "{name}",
#           "qc_values#.value": "{value:integer}",
#           "qc_values#.key": "Total Raw Reads Sequenced",
#           "qc_values#.tooltip": "# of reads (150bp)"
#         },
#         ...
#       }
#     }
#   }
#
# The hook for this is to pass the CustomExcel type to StructuredDataSet in submission.py.
#
# ALSO ...
# This CustomExcel class also handles multiple sheets within a spreadsheet representing
# the same (portal) type; see comments below near the ExcelSheetName class definition.

CUSTOM_COLUMN_MAPPINGS_LOCAL_CONFIG = os.path.join(
    os.path.dirname(__file__), "config", "custom_column_mappings.json"
)

COLUMN_NAME_ARRAY_SUFFIX_CHAR = "#"
COLUMN_NAME_SEPARATOR = "."

# The portal search used to retrieve EQM column-mapping configs.
GENERIC_QC_CONFIG_SEARCH = "search/?type=GenericQcConfig&tags=external_quality_metrics"

# Mapping from GenericQcConfig field value_type strings to the {value:TYPE} macro suffix
# used in the column-mapping config.
_VALUE_TYPE_MACRO = {
    "integer": "{value:integer}",
    "int":     "{value:integer}",
    "float":   "{value:float}",
    "number":  "{value:float}",
    "boolean": "{value:boolean}",
    "bool":    "{value:boolean}",
    "string":  "{value}",
    "str":     "{value}",
}


class CustomExcel(Excel):

    def __init__(self, *args, portal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._custom_column_mappings = CustomExcel._get_custom_column_mappings(portal=portal)

    def sheet_reader(self, sheet_name: str) -> ExcelSheetReader:
        return CustomExcelSheetReader(self, sheet_name=sheet_name, workbook=self._workbook,
                                      custom_column_mappings=self._custom_column_mappings)

    @staticmethod
    def effective_sheet_name(sheet_name: str) -> str:
        if (underscore := sheet_name.find("_")) > 1:
            return sheet_name[underscore + 1:]
        return sheet_name

    @staticmethod
    def _get_custom_column_mappings(portal=None) -> Optional[dict]:

        def fetch_from_portal(portal) -> Optional[dict]:
            """Query the portal for GenericQcConfig items and convert them into
            the same config-dict structure previously loaded from JSON."""
            if portal is None:
                return None
            try:
                results = portal.get_metadata(GENERIC_QC_CONFIG_SEARCH)
                if not isinstance(results, dict):
                    return None
                items = results.get("@graph", [])
                if not items:
                    return None
                return _build_config_from_portal_results(items)
            except Exception:
                return None

        def fetch_from_local_json() -> Optional[dict]:
            """Fall back to the bundled static JSON config."""
            try:
                with io.open(CUSTOM_COLUMN_MAPPINGS_LOCAL_CONFIG, "r") as f:
                    return json.load(f)
            except Exception:
                return None

        def post_process(raw_config: dict) -> Optional[dict]:
            """Resolve sheet_mappings string references into the actual column-mapping dicts."""
            if not isinstance(raw_config, dict):
                return None
            column_mappings = raw_config.get("column_mappings")
            sheet_mappings = raw_config.get("sheet_mappings")
            if not isinstance(column_mappings, dict) or not isinstance(sheet_mappings, dict):
                return None
            for sheet_name in list(sheet_mappings.keys()):
                mapping_key = sheet_mappings[sheet_name]
                if isinstance(mapping_key, str):
                    resolved = column_mappings.get(mapping_key)
                    if isinstance(resolved, dict):
                        sheet_mappings[sheet_name] = resolved
                    else:
                        del sheet_mappings[sheet_name]
                elif not isinstance(mapping_key, dict):
                    del sheet_mappings[sheet_name]
            return sheet_mappings if sheet_mappings else None

        raw_config = fetch_from_portal(portal) or fetch_from_local_json()
        if not raw_config:
            return None
        return post_process(raw_config)


def _build_config_from_portal_results(items: list) -> Optional[dict]:
    """Convert a list of GenericQcConfig portal objects into the internal config dict.

    Each item is expected to have at minimum:
      - "sheet_name"   : str  (the Excel sheet name this config applies to)
      - "mapping_name" : str  (internal key linking sheet_mappings → column_mappings)
      - "fields"       : list of dicts with keys: column, key, tooltip, value_type

    Returns a dict with "sheet_mappings" and "column_mappings" keys, or None if
    nothing useful could be built.
    """
    sheet_mappings: dict = {}
    column_mappings: dict = {}

    for item in items:
        sheet_name = item.get("sheet_name")
        mapping_name = item.get("mapping_name")
        fields = item.get("fields")

        if not (isinstance(sheet_name, str) and sheet_name
                and isinstance(mapping_name, str) and mapping_name
                and isinstance(fields, list) and fields):
            continue

        # Build the per-column mapping dict for this config item.
        per_column: dict = {}
        for field in fields:
            column = field.get("column")
            if not isinstance(column, str) or not column:
                continue
            key = field.get("key", column)
            tooltip = field.get("tooltip")  # may be None / null
            value_type = str(field.get("value_type", "string")).lower().strip()
            value_macro = _VALUE_TYPE_MACRO.get(value_type, "{value}")

            per_column[column] = {
                "qc_values#.derived_from": "{name}",
                "qc_values#.value": value_macro,
                "qc_values#.key": key,
                "qc_values#.tooltip": tooltip,
            }

        if not per_column:
            continue

        sheet_mappings[sheet_name] = mapping_name
        column_mappings[mapping_name] = per_column

    if not sheet_mappings:
        return None

    return {"sheet_mappings": sheet_mappings, "column_mappings": column_mappings}


class CustomExcelSheetReader(ExcelSheetReader):

    def __init__(self, *args, **kwargs) -> None:
        ARGUMENT_NAME_SHEET_NAME = "sheet_name"
        ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS = "custom_column_mappings"
        self._custom_column_mappings = None
        if ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS in kwargs:
            def lookup_custom_column_mappings(custom_column_mappings: dict, sheet_name: str) -> Optional[dict]:
                if isinstance(custom_column_mappings, dict) and isinstance(sheet_name, str):
                    if isinstance(found := custom_column_mappings.get(sheet_name), dict):
                        return found
                    if (effective := CustomExcel.effective_sheet_name(sheet_name)) != sheet_name:
                        if isinstance(found := custom_column_mappings.get(effective), dict):
                            return found
                return None
            custom_column_mappings = kwargs[ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS]
            del kwargs[ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS]
            if not (isinstance(custom_column_mappings, dict) and
                    isinstance(sheet_name := kwargs.get(ARGUMENT_NAME_SHEET_NAME, None), str) and
                    isinstance(custom_column_mappings :=
                               lookup_custom_column_mappings(custom_column_mappings, sheet_name), dict)):
                custom_column_mappings = None
            self._custom_column_mappings = custom_column_mappings
        super().__init__(*args, **kwargs)

    def _define_header(self, header: List[Optional[Any]]) -> None:

        def fixup_custom_column_mappings(custom_column_mappings: dict, actual_column_names: List[str]) -> dict:

            def fixup_custom_array_column_mappings(custom_column_mappings: dict) -> None:

                def get_simple_array_column_name_component(column_name: str) -> Optional[str]:
                    if isinstance(column_name, str):
                        if column_name_components := column_name.split(COLUMN_NAME_SEPARATOR):
                            if (suffix := column_name_components[0].find(COLUMN_NAME_ARRAY_SUFFIX_CHAR)) > 0:
                                if (suffix + 1) == len(column_name_components[0]):
                                    return column_name_components[0][:suffix]
                    return None

                synthetic_array_column_names = {}
                for column_name in custom_column_mappings:
                    for synthetic_column_name in list(custom_column_mappings[column_name].keys()):
                        synthetic_array_column_name = get_simple_array_column_name_component(synthetic_column_name)
                        if synthetic_array_column_name:
                            if synthetic_array_column_name not in synthetic_array_column_names:
                                synthetic_array_column_names[synthetic_array_column_name] = \
                                    {"index": 0, "columns": [column_name]}
                            elif (column_name not in
                                  synthetic_array_column_names[synthetic_array_column_name]["columns"]):
                                synthetic_array_column_names[synthetic_array_column_name]["index"] += 1
                                synthetic_array_column_names[synthetic_array_column_name]["columns"].append(column_name)
                            synthetic_array_column_index = \
                                synthetic_array_column_names[synthetic_array_column_name]["index"]
                            synthetic_array_column_name = synthetic_column_name.replace(
                                f"{synthetic_array_column_name}#",
                                f"{synthetic_array_column_name}#{synthetic_array_column_index}")
                            custom_column_mappings[column_name][synthetic_array_column_name] = \
                                custom_column_mappings[column_name][synthetic_column_name]
                            del custom_column_mappings[column_name][synthetic_column_name]

            custom_column_mappings = deepcopy(custom_column_mappings)
            for custom_column_name in list(custom_column_mappings.keys()):
                if custom_column_name not in actual_column_names:
                    del custom_column_mappings[custom_column_name]
            fixup_custom_array_column_mappings(custom_column_mappings)
            return custom_column_mappings

        super()._define_header(header)
        if self._custom_column_mappings:
            self._custom_column_mappings = fixup_custom_column_mappings(self._custom_column_mappings, self.header)
            self._original_header = self.header
            self.header = []
            for column_name in header:
                if column_name in self._custom_column_mappings:
                    synthetic_column_names = list(self._custom_column_mappings[column_name].keys())
                    self.header += synthetic_column_names
                else:
                    self.header.append(column_name)

    def _iter_header(self) -> List[str]:
        if self._custom_column_mappings:
            return self._original_header
        return super()._iter_header()

    def _iter_mapper(self, row: dict) -> List[str]:
        if self._custom_column_mappings:
            synthetic_columns = {}
            columns_to_delete = []
            for column_name in row:
                if column_name in self._custom_column_mappings:
                    column_mapping = self._custom_column_mappings[column_name]
                    for synthetic_column_name in column_mapping:
                        synthetic_column_value = column_mapping[synthetic_column_name]
                        if synthetic_column_value == "{name}":
                            synthetic_columns[synthetic_column_name] = column_name
                        elif (column_value := self._parse_value_specifier(synthetic_column_value,
                                                                          row[column_name])) is not None:
                            synthetic_columns[synthetic_column_name] = column_value
                        else:
                            synthetic_columns[synthetic_column_name] = synthetic_column_value
                    columns_to_delete.append(column_name)
            if columns_to_delete:
                for column_to_delete in columns_to_delete:
                    del row[column_to_delete]
            if synthetic_columns:
                row.update(synthetic_columns)
        return row

    @staticmethod
    def _parse_value_specifier(value_specifier: Optional[Any], value: Optional[Any]) -> Optional[Any]:
        if value is not None:
            if isinstance(value_specifier, str) and (value_specifier := value_specifier.replace(" ", "")):
                if value_specifier.startswith("{value"):
                    if (value_specifier[len(value_specifier) - 1] == "}"):
                        if len(value_specifier) == 7:
                            return str(value)
                        if value_specifier[6] == ":":
                            if (value_specifier := value_specifier[7:-1]) in ["int", "integer"]:
                                return to_integer(value, fallback=value,
                                                  allow_commas=True, allow_multiplier_suffix=True)
                            elif value_specifier in ["float", "number"]:
                                return to_float(value, fallback=value,
                                                allow_commas=True, allow_multiplier_suffix=True)
                            elif value_specifier in ["bool", "boolean"]:
                                return to_boolean(value, fallback=value)
                        return str(value)
        return None


# This ExcelSheetName class is used to represent an Excel sheet name; it is simply a str type with an
# additional "original" property. The value of this will be given string with any prefix preceding an
# underscore removed; and the "original" property will evaluate to the original/given string. This is
# used to support the use of sheet names of the form "XYZ_TypeName", where "XYZ" is an arbitrary string
# and "TypeName" is the virtual name of the sheet, which will be used by StructuredDataSet/etc, and which
# represents the (portal) type of (the items/rows within the) sheet. The purpose of all this is to allow
# multiple sheets within a spreadsheet of the same (portal object) type; since sheet names must be unique,
# this would otherwise not be possible; this provides a way for a spreadsheet to partition items/rows of
# a particular fixed type across multiple sheets.
#
class ExcelSheetName(str):
    def __new__(cls, value: str):
        value = value if isinstance(value, str) else str(value)
        original_value = value
        if ((delimiter := value.find("_")) > 0) and (delimiter < len(value) - 1):
            value = value[delimiter + 1:]
        instance = super().__new__(cls, value)
        setattr(instance, "original", original_value)
        return instance