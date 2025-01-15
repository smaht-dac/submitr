from requests import get as requests_get
from typing import Any, Iterator, List, Optional
from dcicutils.data_readers import Excel, ExcelSheetReader
from submitr.config.custom_column_mappings import CUSTOM_COLUMN_MAPPINGS as CUSTOM_COLUMN_MAPPINGS_FALLBACK

CUSTOM_COLUMN_MAPPINGS_BASE_URL = "https://raw.githubusercontent.com/smaht-dac/submitr/refs/heads"
CUSTOM_COLUMN_MAPPINGS_BRANCH = "c4-1187-fix-missing-consortia-on-submitted-items"
CUSTOM_COLUMN_MAPPINGS_PATH = "submitr/config/custom_column_mappings.json"
CUSTOM_COLUMN_MAPPINGS_URL = f"{CUSTOM_COLUMN_MAPPINGS_BASE_URL}/{CUSTOM_COLUMN_MAPPINGS_BRANCH}/{CUSTOM_COLUMN_MAPPINGS_PATH}"  # noqa


class CustomExcel(Excel):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def sheet_reader(self, sheet_name: str) -> ExcelSheetReader:
        return CustomExcelSheetReader(self, sheet_name=sheet_name, workbook=self._workbook)

    @staticmethod
    def _get_custom_column_mappings() -> dict:
        try:
            return requests_get(CUSTOM_COLUMN_MAPPINGS_URL).json()
        except Exception:
            return CUSTOM_COLUMN_MAPPINGS_FALLBACK


class CustomExcelSheetReader(ExcelSheetReader):

    def __init__(self, *args, **kwargs) -> None:
        self._custom_column_mappings = CustomExcel._get_custom_column_mappings()
        super().__init__(*args, **kwargs)

    def _define_header(self, header: List[Optional[Any]]) -> None:
        if not self._custom_column_mappings:
            super()._define_header(header)
            return
        self.header = []
        for column_name in header:
            if column_name in self._custom_column_mappings:
                synthetic_column_names = list(self._custom_column_mappings[column_name].keys())
                self.header += synthetic_column_names
            else:
                self.header.append(column_name)

    def __iter__(self) -> Iterator:
        for row in super().__iter__():
            yield self._map(row)

    def _map(self, row: dict) -> dict:
        if not self._custom_column_mappings:
            return row
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
