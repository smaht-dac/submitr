from dcicutils import ff_utils

from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# Validator that reports if any UnalignedRead items that are from ONT sequencers
# are missing the software property, or if any linked software items are missing
# ONT-specific properties
# Also checks if derived_from is missing for ONT fastq files
_UNALIGNED_READS_SCHEMA_NAME = "UnalignedReads"
_FILE_SETS_PROPERTY_NAME = "file_sets"
_FILE_FORMAT_PROPERTY_NAME = "file_format"
_FILE_SET_SCHEMA_NAME = "FileSet"
_SEQUENCING_PROPERTY_NAME = "sequencing"
_SEQUENCING_SCHEMA_NAME = "Sequencing"
_SEQUENCER_PROPERTY_NAME = "sequencer"
_DERIVED_FROM_PROPERTY_NAME = "derived_from"
_SOFTWARE_PROPERTY_NAME = "software"
_SOFTWARE_SCHEMA_NAME = "Software"
_GPU_PROPERTY_NAME = "gpu_architecture"
_MODEL_PROPERTY_NAME = "model"
_TAGS_PROPERTY_NAME = "modification_tags"

_ONT_SPECIFIC_PROPERTIES = [
    _GPU_PROPERTY_NAME,
    _MODEL_PROPERTY_NAME,
    _TAGS_PROPERTY_NAME
]

_FASTQ_FILE_FORMAT = "fastq_gz"


@structured_data_validator_finish_hook
def _ont_unaligned_reads_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    search = "search/?type=Sequencer&platform=ONT"
    sequencers = ff_utils.search_metadata(search, key=structured_data.portal.key)
    ont_identifiers = [seq.get("identifier", "") for seq in sequencers]
    if not isinstance(data := structured_data.data.get(_UNALIGNED_READS_SCHEMA_NAME), list):
        return
    for item in data:
        if _FILE_SETS_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            if (file_sets := [
                    file_set_item
                    for file_set_item in structured_data.data.get(_FILE_SET_SCHEMA_NAME, [])
                    if file_set_item.get("submitted_id")
                    in item.get(_FILE_SETS_PROPERTY_NAME)
            ]):
                for file_set in file_sets:
                    if (sequencings := [
                        sequencing_item
                        for sequencing_item in structured_data.data.get(_SEQUENCING_SCHEMA_NAME, [])
                        if sequencing_item.get("submitted_id")
                        in file_set.get(_SEQUENCING_PROPERTY_NAME)
                    ]):
                        for sequencing in sequencings:
                            if sequencing.get(_SEQUENCER_PROPERTY_NAME) in ont_identifiers:
                                # ONT unaligned reads file
                                if item.get(_FILE_FORMAT_PROPERTY_NAME) == _FASTQ_FILE_FORMAT:
                                    if _DERIVED_FROM_PROPERTY_NAME not in item:
                                        # fastq file missing derived_from
                                        structured_data.note_validation_error(
                                            f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                                            f" item {submitted_id}"
                                            f" property derived_from is required for ONT fastq files."
                                        )
                                if _SOFTWARE_PROPERTY_NAME not in item:
                                    # missing software
                                    structured_data.note_validation_error(
                                        f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                                        f" item {submitted_id}"
                                        f" property software is required for ONT files."
                                    )
                                elif (softwares := [
                                    software_item
                                    for software_item in structured_data.data.get(_SOFTWARE_SCHEMA_NAME, [])
                                    if software_item.get("submitted_id")
                                    in item.get(_SOFTWARE_PROPERTY_NAME)
                                ]):
                                    for software in softwares:
                                        missing = [
                                            prop for prop in _ONT_SPECIFIC_PROPERTIES
                                            if prop not in software
                                        ]
                                        if missing:
                                            # missing ONT-specific properties
                                            structured_data.note_validation_error(
                                                f"{_UNALIGNED_READS_SCHEMA_NAME}:"
                                                f" item {submitted_id}"
                                                f" Sequencer-specific software properties not found."
                                                f" The following Software properties are required for ONT files: "
                                                f" {_ONT_SPECIFIC_PROPERTIES}"
                                            )
