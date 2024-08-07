from typing import Any, Optional, Tuple
from dcicutils.misc_utils import run_concurrently  # noqa
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorator import validator


@validator("submitted_id")
def _validator_submitted_id(structured_data: StructuredDataSet,
                            schema_name: str, column_name: str, row_number: int,
                            value: Any, **kwargs) -> Tuple[Any, Optional[str]]:

    if not hasattr(structured_data, "__validator_submitted_ids__"):
        setattr(structured_data, "__validator_submitted_ids__", [])
    structured_data.__validator_submitted_ids__.append({"submitted_id": value, "schema_name": schema_name})
    path = f"/validators/submitted_id/{value}"
    if valid_submission_centers := kwargs["valid_submission_centers"]:
        path += f"?submission_centers={valid_submission_centers}"
    if result := structured_data.portal.get_metadata(path):
        if (result := result.get("status")) != "OK":
            return value, result
    return value, None


@validator("submitted_id", finish=True)
def _validator_finish_submitted_id(structured_data: StructuredDataSet) -> None:
    if hasattr(structured_data, "__validator_submitted_ids__"):
        import pdb ; pdb.set_trace()  # noqa
        validator_submitted_ids = structured_data.__validator_submitted_ids__  # noqa
        # TODO
