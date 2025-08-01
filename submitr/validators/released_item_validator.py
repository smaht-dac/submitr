from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports any released items that are being modified

_RELEASED = "released"



@structured_data_validator_finish_hook
def _released_item_validator(structured_data: StructuredDataSet, **kwargs) -> None:

    diffs = structured_data.compare()

    for object_type in diffs:
        for object_info in diffs[object_type]:
            if object_info.uuid:
                if object_info.diffs:
                    if object_info.status == _RELEASED:
                        structured_data.note_validation_error(
                            f"{object_info.path} is not permitted to be modified because"
                            f" it is {_RELEASED} item. Please double-check this."
                        )