import json
import os
from requests import get as requests_get
from typing import Any, List, Optional
from dcicutils.data_readers import Excel, ExcelSheetReader

# This module implements a custom Excel spreadsheet class which support "custom column mappings",
# meaning that, and a very low/early level in processing, the columns/values in the spreadsheet
# can be redefined/remapped to different columns/values. The mapping is defined by a JSON config
# file (by default in ../config/custom_column_mappings.json). It can be thought of as a virtual
# preprocessing step on the spreadsheet. This was first implemented to support the simplified QC
# columns/values. For EXAMPLE, so the spreadsheet author can specify a single column like this:
#
#     external_quality_metric: 11870183
#     total_raw_bases_sequenced: 44928835584
#
# But this will be mapped, i.e the system will act AS-iF we instead had these columns/values:
#
#     qc_values#0.derived_from: total_raw_reads_sequenced
#     qc_values#0.value:        11870183
#     qc_values#0.key:          Total Raw Reads Sequenced
#     qc_values#0.tooltip:      # of reads (150bp)
#     qc_values#1.derived_from: total_raw_bases_sequenced
#     qc_values#1.value:        44928835584
#     qc_values#1.key:          Total Raw Bases Sequenced
#     qc_values#1.tooltip:      None
#
# The hook for this is to pass the CustomExcel type to StructuredDataSet in submission.py.
# Note that the config file is fetched from GitHub, with a fallback to ../config/custom_column_mappings.json.

CUSTOM_COLUMN_MAPPINGS_BASE_URL = "https://raw.githubusercontent.com/smaht-dac/submitr/refs/heads"
CUSTOM_COLUMN_MAPPINGS_BRANCH = "dmichaels-custom-column-mappings-20250115"
CUSTOM_COLUMN_MAPPINGS_PATH = "submitr/config/custom_column_mappings.json"
CUSTOM_COLUMN_MAPPINGS_URL = f"{CUSTOM_COLUMN_MAPPINGS_BASE_URL}/{CUSTOM_COLUMN_MAPPINGS_BRANCH}/{CUSTOM_COLUMN_MAPPINGS_PATH}"  # noqa


class CustomExcel(Excel):

    def sheet_reader(self, sheet_name: str) -> ExcelSheetReader:
        return CustomExcelSheetReader(self, sheet_name=sheet_name, workbook=self._workbook,
                                      custom_column_mappings=CustomExcel._get_custom_column_mappings())

    @staticmethod
    def _get_custom_column_mappings() -> dict:
        try:
            custom_column_mappings = requests_get(CUSTOM_COLUMN_MAPPINGS_URL).json()
        except Exception:
            try:
                with open(os.path.join(os.path.dirname(__file__), "config", "custom_column_mappings.json"), "r") as f:
                    custom_column_mappings = json.load(f)
            except Exception:
                custom_column_mappings = None
        if not isinstance(custom_column_mappings, dict):
            custom_column_mappings = {}
        if isinstance(column_mappings := custom_column_mappings.get("column_mappings"), dict):
            if isinstance(sheet_mappings := custom_column_mappings.get("sheet_mappings"), dict):
                for sheet_name in list(sheet_mappings.keys()):
                    if isinstance(sheet_mappings[sheet_name], str):
                        if isinstance(column_mappings.get(sheet_mappings[sheet_name]), dict):
                            sheet_mappings[sheet_name] = column_mappings.get(sheet_mappings[sheet_name])
                        else:
                            del sheet_mappings[sheet_name]
                    elif not isinstance(sheet_mappings[sheet_name], dict):
                        del sheet_mappings[sheet_name]
        return sheet_mappings


class CustomExcelSheetReader(ExcelSheetReader):

    def __init__(self, *args, **kwargs) -> None:
        ARGUMENT_NAME_SHEET_NAME = "sheet_name"
        ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS = "custom_column_mappings"
        self._custom_column_mappings = None
        if ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS in kwargs:
            custom_column_mappings = kwargs[ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS]
            del kwargs[ARGUMENT_NAME_CUSTOM_COLUMN_MAPPINGS]
            if not (isinstance(custom_column_mappings, dict) and
                    isinstance(sheet_name := kwargs.get(ARGUMENT_NAME_SHEET_NAME, None), str) and
                    isinstance(custom_column_mappings := custom_column_mappings.get(sheet_name), dict)):
                custom_column_mappings = None
            self._custom_column_mappings = custom_column_mappings
        super().__init__(*args, **kwargs)

    def _define_header(self, header: List[Optional[Any]]) -> None:
        super()._define_header(header)
        if self._custom_column_mappings:
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
                        elif synthetic_column_value == "{value}":
                            synthetic_columns[synthetic_column_name] = row[column_name]
                        else:
                            synthetic_columns[synthetic_column_name] = synthetic_column_value
                    columns_to_delete.append(column_name)
            if columns_to_delete:
                for column_to_delete in columns_to_delete:
                    del row[column_to_delete]
            if synthetic_columns:
                row.update(synthetic_columns)
        return row
