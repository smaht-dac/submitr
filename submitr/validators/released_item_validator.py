from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook

# Validator that reports any released items that are being modified

# NOTE: (WF) This check probably should not be a validator and would likely work
# best incorporated into the existing diff check. Running compare() takes some
# time, so probably best to not run it again
# NOTE: This code relies on an update to dcicutils where the diffs include
# the status of the existing items.


_NON_MODIFIABLE_STATUSES = {
    "retracted", "archived", "obsolete", "released",
    "open", "open-early", "open-network",
    "protected", "protected-early", "protected-network",
    "public",
}


@structured_data_validator_finish_hook
def _released_item_validator(structured_data: StructuredDataSet, **kwargs) -> None:

    diffs = structured_data.compare()

    for object_type in diffs:
        for object_info in diffs[object_type]:
            if object_info.uuid:
                if object_info.diffs:
                    if object_info.status in _NON_MODIFIABLE_STATUSES:
                        structured_data.note_validation_error(
                            f"{object_info.path} is not permitted to be modified because"
                            f" it is a {object_info.status} item. Please double-check this."
                        )
