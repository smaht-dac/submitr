from typing import Dict, List, Optional, Tuple
import re
from dcicutils.structured_data import StructuredDataSet

from submitr.validators.decorators import structured_data_validator_finish_hook

from submitr.validators.utils import portal as portal_utils, item as item_utils

# Validator that reports if any TissueSample items are linked to Tissue items
# with an external_id that does not contain the external_id of the Tissue
# if at least one of the two items is TPC-submitted

_TISSUE_SAMPLE_SCHEMA_NAME = "TissueSample"
_SAMPLE_SOURCE_PROPERTY_NAME = "sample_sources"
_EXTERNAL_ID_PROPERTY_NAME = "external_id"
_TISSUE_SCHEMA_NAME = "Tissue"
_NDRI_SUBMISSION_CENTER_PREFIX = "NDRI"
_NDRI_TPC_DISPLAY_TITLE = "NDRI TPC"
_BENCHMARKING_PREFIX = "ST"
_PRODUCTION_PREFIX = "SMHT"
_METADATA_COMPARISON_PROPERTIES = ["category", "preservation_type"]
_CATEGORY_REGEX_MAP = {
    "Tissue Aliquot": re.compile(
        r"-[13](?:A[A-Z]?|[B-Z])-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])$"
    ),
    "Cells": re.compile(
        r"-3AC-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])X$"
    ),
    "Core": re.compile(
        r"-[13](?:A[A-Z]?|[B-Z])-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])[A-F][1-6]$"
    ),
    "Homogenate": re.compile(
        r"-1(?:A[A-Z]?|[B-Z])-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])X$"
    ),
    "Specimen": re.compile(
        r"-[13](?:A[A-Z]?|[B-Z])-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])[S-W][1-9]$"
    ),
    "Liquid": re.compile(
        r"-3[AB]-(?:00[1-9]|0[1-9][0-9]|1[0-1][0-9]|12[0-5])X$"
    ),
}

_TISSUE_CATEGORIES = list(_CATEGORY_REGEX_MAP.keys())


@structured_data_validator_finish_hook
def _tissue_sample_external_id_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    if not isinstance(
        data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list
    ):
        return
    for item in data:
        if _SAMPLE_SOURCE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            tissue_sample_sc = submitted_id.split("_")[0]
            if tissue_items := [
                tissue
                for tissue in structured_data.data.get(_TISSUE_SCHEMA_NAME, [])
                if tissue.get("submitted_id") in item.get(_SAMPLE_SOURCE_PROPERTY_NAME)
            ]:
                tissue_sc = tissue_items[0].get("submitted_id", "").split("_")[0]
                if (
                    tissue_sample_sc == _NDRI_SUBMISSION_CENTER_PREFIX
                    or tissue_sc == _NDRI_SUBMISSION_CENTER_PREFIX
                ):
                    tissue_external_id = tissue_items[0].get(_EXTERNAL_ID_PROPERTY_NAME)
                    tissue_sample_external_id = item.get(_EXTERNAL_ID_PROPERTY_NAME)
                    if (
                        "-".join(tissue_sample_external_id.split("-")[0:2])
                        != tissue_external_id
                    ):
                        structured_data.note_validation_error(
                            f"{_TISSUE_SAMPLE_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" external_id {tissue_sample_external_id} does not"
                            f" match {_TISSUE_SCHEMA_NAME} external_id"
                            f" {tissue_external_id}."
                        )


@structured_data_validator_finish_hook
def _tissue_sample_metadata_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validate TissueSample metadata consistency with TPC baseline samples.

    This validator queries the portal to compare against existing samples and ensures:
    - TPC submissions don't create duplicate samples
    - GCC submissions have a corresponding TPC baseline sample
    - GCC submissions don't create duplicate non-TPC samples
    - GCC metadata (category, preservation_type, sample_sources) matches TPC baseline

    Only applies to Benchmarking and Production studies.
    """
    # Get TissueSample items from submission
    if not isinstance(
        data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list
    ):
        return

    # Initialize caches
    samples_cache: Dict[str, List[Dict]] = {}
    tissue_cache: Dict[str, str] = {}
    seen_external_ids: Dict[str, str] = {}  # external_id -> submitted_id

    portal_key = structured_data.portal.key

    for item in data:
        submitted_id = item_utils.get_submitted_id(item)
        external_id = item_utils.get_external_id(item)

        # Skip if missing required fields
        if not external_id or not submitted_id:
            continue

        if external_id in seen_external_ids:
            # This is OK if it's the same item (update), error if different item
            if seen_external_ids[external_id] != submitted_id:
                structured_data.note_validation_error(
                    f"TissueSample: A sample with external_id {external_id} already exists in this submission"
                )
            continue

        # Track this external_id
        seen_external_ids[external_id] = submitted_id

        if not (
            external_id.startswith(_BENCHMARKING_PREFIX)
            or external_id.startswith(_PRODUCTION_PREFIX)
        ):
            continue

        # Determine if this is TPC or GCC submission
        is_tpc = _is_tpc_submission(submitted_id)

        # Query portal for existing samples with this external_id
        existing_samples = _get_or_fetch_tissue_samples(
            external_id, samples_cache, portal_key
        )

        if existing_samples is None:
            # Portal query failed
            structured_data.note_validation_error(
                f"TissueSample: Unable to validate {submitted_id} - "
                f"portal query failed for external_id {external_id}"
            )
            continue

        # Categorize existing samples
        tpc_samples, non_tpc_samples = _categorize_samples_by_submission_center(
            existing_samples
        )

        # Validate based on submission type
        if is_tpc:
            # TPC submission - check for duplicates
            _validate_tpc_duplicate(
                external_id, submitted_id, tpc_samples, structured_data
            )
        else:
            # GCC submission - check for TPC exists and no other duplicates
            if not _validate_gcc_baseline_exists(
                external_id, tpc_samples, structured_data
            ):
                continue

            if not _validate_gcc_duplicate(
                external_id,
                submitted_id,
                non_tpc_samples,
                seen_external_ids,
                structured_data,
            ):
                continue

            # Compare metadata with TPC baseline
            if tpc_samples:
                _validate_metadata_consistency(
                    item, tpc_samples[0], structured_data, tissue_cache
                )

        # Track this external_id
        seen_external_ids[external_id] = submitted_id


# helper functions
def _is_tpc_submission(submitted_id: str) -> bool:
    """
    Based on submitted_id prefix, determine if this is a TPC submission.
    """
    if submitted_id.startswith(_NDRI_SUBMISSION_CENTER_PREFIX):
        return True
    return False


def _get_or_fetch_tissue_samples(
    external_id: str,
    cache: Dict[str, List[Dict]],
    portal_key: Dict,
) -> Optional[List[Dict]]:
    """Get tissue from cache or fetch from portal, caching result."""
    if external_id in cache:
        return cache[external_id]

    samples = portal_utils.search_tissue_samples_by_external_id(external_id, portal_key)

    cache[external_id] = samples

    return samples


def _categorize_samples_by_submission_center(
    samples: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """Separate samples into TPC and non-TPC lists based on submission_centers."""
    tpc_samples = []
    non_tpc_samples = []

    for sample in samples:
        # Check if any submission center is TPC
        is_tpc = False

        # Try embedded submission_centers data first
        if submission_centers := sample.get("submission_centers", []):
            for center in submission_centers:
                if isinstance(center, dict):
                    display_title = center.get("display_title")
                    if display_title == _NDRI_TPC_DISPLAY_TITLE:
                        is_tpc = True
                        break

        # check submitted_id prefix
        if not is_tpc:
            submitted_id = item_utils.get_submitted_id(sample)
            if submitted_id:
                is_tpc = _is_tpc_submission(submitted_id)

        if is_tpc:
            tpc_samples.append(sample)
        else:
            non_tpc_samples.append(sample)

    return tpc_samples, non_tpc_samples


def _validate_tpc_duplicate(
    external_id: str,
    submitted_id: str,
    tpc_samples: List[Dict],
    structured_data: StructuredDataSet,
):
    """
    Validate TPC submission doesn't create duplicate.
    Returns True if validation passes, False if error found.
    """
    if len(tpc_samples) > 0:
        if len(tpc_samples) == 1:
            # check if update to existing item
            existing_submitted_id = item_utils.get_submitted_id(tpc_samples[0])
            if existing_submitted_id == submitted_id:
                return
        structured_data.note_validation_error(
            f"TissueSample: TPC Tissue Sample with external_id {external_id} already exists"
        )
    return


def _validate_gcc_baseline_exists(
    external_id: str, tpc_samples: List[Dict], structured_data: StructuredDataSet
) -> bool:
    """
    Validate GCC submission has TPC baseline sample.
    Returns True if validation passes, False if error found.
    """
    if len(tpc_samples) == 0:
        structured_data.note_validation_error(
            f"TissueSample: No TPC Tissue Sample found with external_id {external_id}"
        )
        return False
    return True


def _validate_gcc_duplicate(
    external_id: str,
    submitted_id: str,
    non_tpc_samples: List[Dict],
    seen_external_ids: Dict[str, str],
    structured_data: StructuredDataSet,
) -> bool:
    """
    Validate GCC submission doesn't create duplicate non-TPC sample.
    Returns True if validation passes, False if error found.
    """
    # Check if we've already seen this external_id in current batch
    if external_id in seen_external_ids:
        # This is OK if it's the same item (update), error if different item
        if seen_external_ids[external_id] != submitted_id:
            structured_data.note_validation_error(
                f"TissueSample: A non-TPC sample with external_id {external_id} already exists in this submission"
            )
            return False

    # Check portal for existing non-TPC samples
    if len(non_tpc_samples) > 0:
        # If there's one non-TPC sample and it's this item (by submitted_id), that's OK (update)
        if len(non_tpc_samples) == 1:
            existing_submitted_id = item_utils.get_submitted_id(non_tpc_samples[0])
            if existing_submitted_id == submitted_id:
                return True

        # Otherwise it's a duplicate
        structured_data.note_validation_error(
            f"TissueSample: A non-TPC sample with external_id {external_id} already exists"
        )
        return False

    return True


def _is_tissue_submitted_id(identifier: str) -> bool:
    """
    Check if identifier is specifically a Tissue submitted_id.

    Tissue pattern: NDRI_TISSUE_{tissue_id}
    Non-Tissue patterns: NDRI_TISSUE_{SUBTYPE}_{id} where SUBTYPE is SAMPLE, COLLECTION, etc.

    Strategy: Check if the third segment (after second underscore) is NOT a known subtype.
    """
    if not isinstance(identifier, str):
        return False

    # Must start with NDRI_TISSUE_
    if not identifier.startswith(f"{_NDRI_SUBMISSION_CENTER_PREFIX}_TISSUE_"):
        return False

    parts = identifier.split("_")

    # Must have at least 3 parts
    if len(parts) < 3:
        return False

    # Known non-Tissue subtypes (expand as needed)
    NON_TISSUE_SUBTYPES = {"SAMPLE", "COLLECTION"}

    # Third segment should NOT be a known subtype
    third_segment = parts[2]
    return third_segment not in NON_TISSUE_SUBTYPES


def _get_tissue_submitted_id(
    tissue_id: str,
    tissue_cache: Dict[str, Dict],
    portal_key: Dict,
) -> Optional[Dict]:
    """Get tissue from cache, or fetch from portal with identifying property."""
    submitted_id = None
    if tissue_id in tissue_cache:
        return tissue_cache[tissue_id]
    tissue = portal_utils.get_item_by_identifier(tissue_id, portal_key)
    if tissue:
        submitted_id = item_utils.get_submitted_id(tissue)

    tissue_cache[tissue_id] = submitted_id
    return submitted_id


def _validate_metadata_consistency(
    item: Dict,
    tpc_sample: Dict,
    structured_data: StructuredDataSet,
    tissue_cache: Dict[str, Dict],
) -> None:
    """
    Validate GCC metadata matches TPC baseline for category, preservation_type, sample_sources.
    """
    # Compare category and preservation_type
    for prop in _METADATA_COMPARISON_PROPERTIES:
        gcc_value = item.get(prop)
        tpc_value = tpc_sample.get(prop)

        if gcc_value and tpc_value and tpc_value != gcc_value:
            structured_data.note_validation_error(
                f"TissueSample: metadata mismatch, {prop} {gcc_value} "
                f"does not match value {tpc_value} in TPC Tissue Sample {item_utils.get_submitted_id(tpc_sample)}"
            )

    # Compare sample_sources - assumes one source
    gcc_submitted_id = None
    tpc_source = tpc_sample.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])
    tpc_submitted_id = (
        _get_tissue_submitted_id(
            tpc_source[0].get("uuid"), tissue_cache, structured_data.portal.key
        )
        if tpc_source
        else None
    )
    gcc_sources = item.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])
    if gcc_sources:
        # this will most likely be submitted_id
        gcc_source = gcc_sources[0]
        if _is_tissue_submitted_id(gcc_source):
            gcc_submitted_id = gcc_source
        else:
            gcc_submitted_id = _get_tissue_submitted_id(
                gcc_source, tissue_cache, structured_data.portal.key
            )

    if tpc_submitted_id != gcc_submitted_id:
        structured_data.note_validation_error(
            f"TissueSample: metadata mismatch: sample_source {gcc_submitted_id} does not "
            f"match TPC TissueSample sample_source {tpc_submitted_id}"
        )


@structured_data_validator_finish_hook
def _tissue_sample_external_id_category_match_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:

    # Get TissueSample items from submission
    if not isinstance(
        data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list
    ):
        return

    for item in data:
        submitted_id = item_utils.get_submitted_id(item)
        external_id = item_utils.get_external_id(item)
        category = item.get("category")
        """Check that external_id pattern matches for category."""
        if category in _TISSUE_CATEGORIES and external_id:
            category_regex = _CATEGORY_REGEX_MAP.get(category)
            if category_regex and not category_regex.search(external_id):
                structured_data.note_validation_error(
                    f"TissueSample: item {submitted_id} has category {category} "
                    f"but external_id {external_id} does not match expected pattern "
                    f"for that category."
                )


def _text_before_nth(text: str, delimiter: str, n: int) -> Optional[str]:
    """
    Return text before the nth occurrence of delimiter.
    Equivalent to Excel's TEXTBEFORE(text, delimiter, n).

    Example: _text_before_nth("SMHT001-3G-001D2", "-", 2) -> "SMHT001-3G"
    """
    parts = text.split(delimiter)
    if len(parts) <= n:
        return None
    return delimiter.join(parts[:n])


def _text_after_nth(text: str, delimiter: str, n: int) -> Optional[str]:
    """
    Return text after the nth occurrence of delimiter.
    Equivalent to Excel's TEXTAFTER(text, delimiter, n).

    Example: _text_after_nth("NDRI_TISSUE_SMHT001-3G-DESCEN_COLON", "_", 2)
             -> "SMHT001-3G-DESCEN_COLON"
    """
    parts = text.split(delimiter, n)
    if len(parts) <= n:
        return None
    return parts[n]


def _extract_donor_tissue_prefix(external_id: str) -> Optional[str]:
    """
    Extract the donor-tissue prefix (e.g., 'SMHT001-3G') from an external_id.
    Returns text before the 2nd hyphen.

    Excel equivalent: TEXTBEFORE(C2, "-", 2)

    Example: _extract_donor_tissue_prefix("SMHT001-3G-001D2") -> "SMHT001-3G"
    """
    return _text_before_nth(external_id, "-", 2)


def _extract_donor_tissue_prefix_from_sample_source(sample_source: str) -> Optional[str]:
    """
    Extract the donor-tissue prefix from a tissue sample_source identifier.

    Excel equivalent: TEXTBEFORE(TEXTAFTER(K2, "_", 2), {"-", "_"}, 2)

    Example: _extract_donor_tissue_prefix_from_sample_source(
                 "NDRI_TISSUE_SMHT001-3G-DESCEN_COLON"
             ) -> "SMHT001-3G"

    Steps:
        TEXTAFTER("NDRI_TISSUE_SMHT001-3G-DESCEN_COLON", "_", 2)
            -> "SMHT001-3G-DESCEN_COLON"
        TEXTBEFORE("SMHT001-3G-DESCEN_COLON", "-", 2)
            -> "SMHT001-3G"
    """
    after_second_underscore = _text_after_nth(sample_source, "_", 2)
    if not after_second_underscore:
        return None
    return _text_before_nth(after_second_underscore, "-", 2)


@structured_data_validator_finish_hook
def _tissue_sample_external_id_in_submitted_id_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    """
    Validate that the external_id code is contained within the submitted_id.

    Excel equivalent: =ISNUMBER(FIND(C2, A2))
    where C2=external_id, A2=submitted_id

    FIND is case-sensitive, so a direct substring check is used.

    Example (VALID):
        submitted_id : NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2
        external_id  : SMHT001-3G-001D2
        -> "SMHT001-3G-001D2" is found in "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2"
    """
    if not isinstance(
        data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list
    ):
        return

    for item in data:
        submitted_id = item_utils.get_submitted_id(item)
        external_id = item_utils.get_external_id(item)

        if not submitted_id or not external_id:
            continue

        if external_id not in submitted_id:
            structured_data.note_validation_error(
                f"TissueSample: item {submitted_id} - "
                f"external_id {external_id} is not contained within submitted_id."
            )


@structured_data_validator_finish_hook
def _tissue_sample_external_id_sample_source_consistency_validator(
    structured_data: StructuredDataSet, **kwargs
) -> None:
    if not isinstance(
        data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list
    ):
        return

    for item in data:
        submitted_id = item_utils.get_submitted_id(item)
        external_id = item_utils.get_external_id(item)
        sample_sources = item.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])

        if not submitted_id or not external_id or not sample_sources:
            continue

        if not (
            external_id.startswith(_BENCHMARKING_PREFIX)
            or external_id.startswith(_PRODUCTION_PREFIX)
        ):
            continue

        # Guard: skip if any Tissue in this submission has its submitted_id in
        # sample_sources AND this is an NDRI item — _tissue_sample_external_id_validator
        # already covers that case and we avoid duplicate error messages
        is_ndri = submitted_id.startswith(_NDRI_SUBMISSION_CENTER_PREFIX)
        tissue_in_submission = any(
            tissue.get("submitted_id") in sample_sources
            for tissue in structured_data.data.get(_TISSUE_SCHEMA_NAME, [])
        )
        if is_ndri and tissue_in_submission:
            continue

        # Take first sample_source for prefix comparison (typically array of 1)
        sample_source = sample_sources[0] if isinstance(sample_sources, list) else sample_sources

        external_id_prefix = _extract_donor_tissue_prefix(external_id)
        if not external_id_prefix:
            continue

        sample_source_prefix = _extract_donor_tissue_prefix_from_sample_source(sample_source)
        if not sample_source_prefix:
            continue

        if external_id_prefix != sample_source_prefix:
            structured_data.note_validation_error(
                f"TissueSample: item {submitted_id} - "
                f"external_id donor-tissue prefix {external_id_prefix!r} does not match "
                f"sample_source donor-tissue prefix {sample_source_prefix!r} "
                f"(sample_source: {sample_source})."
            )