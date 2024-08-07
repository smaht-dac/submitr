from typing import Any, Callable, Optional, Tuple
from dcicutils.structured_data import StructuredDataSet


_VALIDATORS = {}
_FINISH_VALIDATORS = {}


def validator(*decorator_args, **decorator_kwargs) -> Callable:
    def validator_decorator(wrapped_function: Callable) -> Callable:
        nonlocal decorator_args, decorator_kwargs
        if len(decorator_args) != 1:
            print("CODE ERROR: column or schema.column argument required for @validation decorator")
            exit(1)
        if decorator_kwargs.get("finish") is True:
            _FINISH_VALIDATORS[decorator_args[0]] = wrapped_function
        else:
            _VALIDATORS[decorator_args[0]] = wrapped_function
        def function_wrapper(*args, **kwargs) -> Any:  # noqa
            nonlocal wrapped_function
            return wrapped_function(*args, **kwargs)
        return function_wrapper
    return validator_decorator


def define_validators_hook(**kwargs) -> Callable:

    def validators(structured_data: StructuredDataSet,
                   schema_name: Optional[str] = None,
                   column_name: Optional[str] = None,
                   row_number: Optional[int] = None,
                   value: Any = None) -> Tuple[Any, Optional[str]]:
        if validator := find_validator(schema_name=schema_name, column_name=column_name):
            return validator(structured_data,
                             schema_name=schema_name,
                             column_name=column_name,
                             row_number=row_number,
                             value=value,
                             **kwargs)
        return value, None

    def find_validator(schema_name: str, column_name: str) -> Optional[Callable]:
        if ((validator := _VALIDATORS.get(column_name)) or
            (validator := _VALIDATORS.get(f"{schema_name}.{column_name}"))):  # noqa
            return validator
        return None

    return validators


def finish_validators_hook(structured_data: StructuredDataSet, **kwargs) -> None:
    for validator in _FINISH_VALIDATORS:
        _FINISH_VALIDATORS[validator](structured_data, **kwargs)
