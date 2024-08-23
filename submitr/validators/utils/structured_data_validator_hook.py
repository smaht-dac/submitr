from typing import Any, Callable, Optional, Tuple
from dcicutils.structured_data import StructuredDataSet

# Decorator for per-column per-schema/type/sheet validators. Usage like this:
#
#   @structured_data_validator_hook("submitted_id")
#   def validator_some_name(structured_data: StructuredDataSet,
#                           schema_name: str, column_name: str, row_number: int,
#                           value: Any, **kwargs) -> Tuple[Any, Optional[str]]:
#
#   @structured_data_validator_hook("submitted_id", finish=True)
#   def validator_finish_some_name(structured_data: StructuredDataSet, *kwargs) -> None:
#
# The @structured_data_validator_hook argument may be either a column name, e.g. submitted_id, in
# which case the validator will be called for each value of the named column for all schemas; or a
# schema name (aka type or sheet name) followed by dot and a column name, e.g. Analyte.submitted_id,
# in which case the validator will be called for each value of the named column within the
# named schema. The return value is a 2-tuple with the desired column value and a validation
# error message (or None if no error). If the finish decorator argument is True, then the
# validator function will be called only at the end of submission metadata processing.
#
# To get the main validator hook to pass as the validator_hook argument to the StructuredDataSet
# object (used to parse the submission metadata) constructor, call the define_validator_hook
# function (any kwargs passed to it will also be passed along to the validator functions).
# To ensure that the "finish" validators are called call the finish_validators_hook function
# after the StructureDataSet load function (load_file) is complete.
#
# Currently (2024-08-06) only used for submitted_id across all schemas/types/sheets.
# see validator_submitted_id.py.

_VALIDATORS = {}
_FINISH_VALIDATORS = {}


def structured_data_validator_hook(*decorator_args, **decorator_kwargs) -> Callable:
    def validator_decorator(wrapped_function: Callable) -> Callable:
        nonlocal decorator_args, decorator_kwargs
        if len(decorator_args) != 1:
            print("CODE ERROR: column or schema.column argument required for @validation decorator")
            exit(1)
        if decorator_kwargs.get("finish") is True:
            _FINISH_VALIDATORS[decorator_args[0]] = wrapped_function
        else:
            _VALIDATORS[decorator_args[0]] = wrapped_function
    return validator_decorator


def define_structured_data_validator_hook(**kwargs) -> Callable:

    def validators(structured_data: StructuredDataSet,
                   schema_name: Optional[str] = None,
                   column_name: Optional[str] = None,
                   row_number: Optional[int] = None,
                   value: Any = None) -> Tuple[Any, Optional[str]]:

        if ((validator := _VALIDATORS.get(column_name)) or
            (validator := _VALIDATORS.get(f"{schema_name}.{column_name}"))):  # noqa
            return validator(structured_data,
                             schema_name=schema_name,
                             column_name=column_name,
                             row_number=row_number,
                             value=value, **kwargs)
        return value, None

    def finish_validators(structured_data: StructuredDataSet) -> None:
        nonlocal kwargs
        for validator in _FINISH_VALIDATORS:
            _FINISH_VALIDATORS[validator](structured_data, **kwargs)

    setattr(validators, "finish", finish_validators)
    return validators


def structured_data_validator_sheet_hook(**kwargs) -> Callable:
    pass


def define_structured_data_validator_sheet_hook(**kwargs) -> Callable:
    def validators(structured_data: StructuredDataSet, sheet_name: str, data: dict) -> None:
        # TODO
        pass
    return validators
