from typing import Any, Callable
from dcicutils.structured_data import StructuredDataSet

# Decorator for per-column per-schema/type/sheet validators.
# Called by StructuredDat for each column/value within each sheet for post-processing.
# Usage like this:
#
#   @structured_data_validator_hook("submitted_id")
#   def validator_some_name(structured_data: StructuredDataSet,
#                           schema: str, column: str, row: int,
#                           value: Any, **kwargs) -> None
#
#   @structured_data_validator_hook("submitted_id", finish=True)
#   def validator_finish_some_name(structured_data: StructuredDataSet, *kwargs) -> None:
#
# The @structured_data_validator_hook argument may be either a column name, e.g. submitted_id, in
# which case the validator will be called for each value of the named column for all schemas; or a
# schema name (aka type or sheet name) followed by dot and a column name, e.g. Analyte.submitted_id,
# in which case the validator will be called for each value of the named column within the named
# schema. The return value is the desired column value. If the finish decorator argument is True,
# then the validator function will be called only at the end of submission metadata processing.
#
# To get the main validator hook to pass as the validator_hook argument to the StructuredDataSet object,
# used to parse the submission metadata, constructor, call the define_structured_data_validator_hook
# function (any kwargs passed to it will also be passed along to the validator functions).
# To ensure that the "finish" validators are called call the finish_validators_hook function
# after the StructureDataSet load function (load_file) is complete.
#
# Currently (2024-08-06) only used for submitted_id across all schemas/types/sheets; see submitted_id_validator.py.

_VALIDATORS = {}
_FINISH_VALIDATORS = {}


def structured_data_validator_hook(*decorator_args, **decorator_kwargs) -> Callable:
    if (len(decorator_args) > 0) and callable(decorator_args[0]):
        print(f"CODE ERROR: Missing schema name for @structured_data_validator_hook: {decorator_args[0].__name__}")
        exit(1)
    def decorator(wrapped_function: Callable) -> Callable:  # noqa
        nonlocal decorator_args, decorator_kwargs
        if not (len(decorator_args) == 1) and isinstance(sheets := decorator_args[0], str) and sheets:
            print(f"CODE ERROR: Missing column or schema.column argument"
                  f" for @structured_data_validator_hook: {wrapped_function.__name__}")
            exit(1)
        if decorator_kwargs.get("finish") is True:
            _FINISH_VALIDATORS[decorator_args[0]] = wrapped_function
        else:
            _VALIDATORS[decorator_args[0]] = wrapped_function
    return decorator


def define_structured_data_validator_hook(**kwargs) -> Callable:
    def hook(structured_data: StructuredDataSet, schema: str,
             column: str, row: int, value: Any) -> Any:
        if ((validator := _VALIDATORS.get(column)) or
            (validator := _VALIDATORS.get(f"{schema}.{column}"))):  # noqa
            return validator(structured_data, schema, column, row, value=value, **kwargs)
        return value
    def finish_validators(structured_data: StructuredDataSet) -> None:  # noqa
        nonlocal kwargs
        for validator in _FINISH_VALIDATORS:
            _FINISH_VALIDATORS[validator](structured_data, **kwargs)
    setattr(hook, "finish", finish_validators)
    return hook


# Decorator for per-schema/type/sheeet validators.
# Called from StructuredDataSet at end of processing for each sheet for post-processing.
# Usage like this: TODO
#
#   @structured_data_validator_sheet_hook(["Analyte", "CellLine"])
#   def some_validator(structured_data: StructuredDataSet, schema: str, data: dict) -> None:
#       pass

_SHEET_VALIDATORS = {}


def structured_data_validator_sheet_hook(*decorator_args, **decorator_kwargs) -> Callable:
    if (len(decorator_args) > 0) and callable(decorator_args[0]):
        print(f"CODE ERROR: Single schema name argument required for"
              f" @structured_data_validator_sheet_hook decorator: {decorator_args[0].__name__}")
        exit(1)
    def decorator(wrapped_function: Callable) -> Callable:  # noqa
        nonlocal decorator_args, decorator_kwargs
        if not ((len(decorator_args) == 1) and
                isinstance(schemas := decorator_args[0], (str, list)) and schemas):
            print(f"CODE ERROR: Single sheet name argument required for"
                  f" @structured_data_validator_sheet_hook decorator: {wrapped_function.__name__}")
            exit(1)
        if isinstance(schemas, str):
            schemas = [schemas]
        for schema in schemas:
            if _SHEET_VALIDATORS.get(schema):
                print(f"CODE ERROR: duplicate @structured_data_validator_sheet_hook decorator: {schema}")
                exit(1)
            _SHEET_VALIDATORS[schema] = wrapped_function
    return decorator


def define_structured_data_validator_sheet_hook() -> Callable:
    def hook(structured_data: StructuredDataSet, schema: str, data: dict) -> None:
        if validator := _SHEET_VALIDATORS.get(schema):
            validator(structured_data, schema, data)
    return hook
