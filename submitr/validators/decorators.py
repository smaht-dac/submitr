from typing import Any, Callable
from dcicutils.structured_data import StructuredDataSet

_VALIDATORS = {}
_FINISH_VALIDATORS = []
_SHEET_VALIDATORS = {}


# Decorator for per-column per-schema/type/sheet validators. Called by StructuredData
# for each column/value within each sheet for post-processing. Usage like this:
#
#   @structured_data_validator_hook("submitted_id")
#   def your_validator(structured_data: StructuredDataSet,
#                      schema: str, column: str, row: int, value: Any, **kwargs) -> None:
#
#   @structured_data_validator_hook("Analyte.concentration")
#   def your_validator(structured_data: StructuredDataSet,
#                      schema: str, column: str, row: int, value: Any, **kwargs) -> None:
#
# The @structured_data_validator_hook argument may be either a column name, e.g. submitted_id, in
# which case the validator will be called for each value of the named column for ALL schemas; or a
# schema name (aka type or sheet name) followed by dot and a column name, e.g. Analyte.concentration,
# in which case the validator will be called for each value of the named column within the named
# schema. The return value is the desired column value.
#
# Call define_structured_data_validator_hook to get the main validator hook
# to pass as the validator_hook argument to the StructuredDataSet constructor;
# any kwargs passed to it will also be passed along to the validator functions).
# That will also include a "finish" function/callback property which, if set,
# StructuredDataSet will call at the end of processing; "finish" validator functions
# may be defined via the @structured_data_validator_finish_hook decorator (below).
#
def structured_data_validator_hook(*decorator_args, **decorator_kwargs) -> Callable:
    if (len(decorator_args) > 0) and callable(decorator_args[0]):
        print(f"CODE ERROR: Missing column or schema.column argument for"
              f" @structured_data_validator_hook: {decorator_args[0].__name__}")
        exit(1)
    def decorator(wrapped_function: Callable) -> Callable:  # noqa
        nonlocal decorator_args, decorator_kwargs
        if not ((len(decorator_args) == 1) and
                isinstance(arg := decorator_args[0], str) and arg and (not decorator_kwargs)):
            print(f"CODE ERROR: Only a column or schema.column argument permitted for"
                  f" @structured_data_validator_hook: {wrapped_function.__name__}")
            exit(1)
        _VALIDATORS[arg] = wrapped_function
    return decorator


# Decorator for finish validator. Called by StructuredData at the end of processing. Usage like this:
#
#   @structured_data_validator_finish_hook
#   def your_finish_validator(structured_data: StructuredDataSet, *kwargs) -> None:
#
def structured_data_validator_finish_hook(*decorator_args, **decorator_kwargs) -> Callable:
    # Reminder of how decorators works:
    # - @structured_data_validator_finish_hook -> decorator_args == tuple(wrapped_function)
    #   And the decorator function below does NOT get called.
    # - @structured_data_validator_finish_hook() -> decorator_args == tuple()
    # - @structured_data_validator_finish_hook(arg) -> decorator_args == tuple(arg)
    #   And the decorator function below DOES get called with the wrapped_function.
    if (len(decorator_args) == 1) and callable(wrapped_function := decorator_args[0]) and (not decorator_kwargs):
        _FINISH_VALIDATORS.append(wrapped_function)
    def decorator(wrapped_function: Callable) -> Callable:  # noqa
        nonlocal decorator_args, decorator_kwargs
        if (((len(decorator_args) != 0) and
             (not (len(decorator_args) == 1 and
                   ([f for f in _FINISH_VALIDATORS if f == wrapped_function]))))) or decorator_kwargs:
            print(f"CODE ERROR: No arguments permitted for"
                  f" @structured_data_validator_finish_hook: {wrapped_function.__name__}")
            exit(1)
        _FINISH_VALIDATORS.append(wrapped_function)
    return decorator


# Decorator for per-schema/type/sheeet validators. Called from StructuredDataSet
# at the end of processing for each sheet for post-processing. Usage like this:
#
#   @structured_data_validator_sheet_hook(["Analyte", "CellLine"])
#   def some_validator(structured_data: StructuredDataSet, schema: str, data: dict) -> None:
#
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


# Define the main per-column/value StructuredDataSet hook (including the "finish" hook as a property thereof).
#
def define_structured_data_validator_hook(**kwargs) -> Callable:
    def hook(structured_data: StructuredDataSet, schema: str,
             column: str, row: int, value: Any) -> Any:
        if ((validator := _VALIDATORS.get(column)) or
            (validator := _VALIDATORS.get(f"{schema}.{column}"))):  # noqa
            return validator(structured_data, schema, column, row, value=value, **kwargs)
        return value
    def finish_hook(structured_data: StructuredDataSet) -> None:  # noqa
        nonlocal kwargs
        for validator in _FINISH_VALIDATORS:
            validator(structured_data, **kwargs)
    setattr(hook, "finish", finish_hook)
    return hook


# Define the main StructuredDataSet per-sheet hook.
#
def define_structured_data_validator_sheet_hook() -> Callable:
    def hook(structured_data: StructuredDataSet, schema: str, data: dict) -> None:
        if validator := _SHEET_VALIDATORS.get(schema):
            validator(structured_data, schema, data)
    return hook
