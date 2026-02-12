from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook


# Validator that reports if any TissueSample items are linked to Tissue items
# with an external_id that does not contain the external_id of the Tissue
# if at least one of the two items is TPC-submitted

_TISSUE_SAMPLE_SCHEMA_NAME = "TissueSample"
_SAMPLE_SOURCE_PROPERTY_NAME = "sample_sources"
_EXTERNAL_ID_PROPERTY_NAME = "external_id"
_TISSUE_SCHEMA_NAME = "Tissue"
_NDRI_SUBMISSION_CENTER = "NDRI"


@structured_data_validator_finish_hook
def _tissue_sample_external_id_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    if not isinstance(data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list):
        return
    for item in data:
        if _SAMPLE_SOURCE_PROPERTY_NAME in item and (
            submitted_id := item.get("submitted_id")
        ):
            tissue_sample_sc = submitted_id.split('_')[0]
            if (tissue_items := [
                tissue
                for tissue in structured_data.data.get(_TISSUE_SCHEMA_NAME, [])
                if tissue.get("submitted_id") in item.get(_SAMPLE_SOURCE_PROPERTY_NAME)
            ]):
                tissue_sc = tissue_items[0].get("submitted_id", "").split('_')[0]
                if tissue_sample_sc == _NDRI_SUBMISSION_CENTER or tissue_sc == _NDRI_SUBMISSION_CENTER:
                    tissue_external_id = tissue_items[0].get(_EXTERNAL_ID_PROPERTY_NAME)
                    tissue_sample_external_id = item.get(_EXTERNAL_ID_PROPERTY_NAME)
                    if "-".join(tissue_sample_external_id.split("-")[0:2]) != tissue_external_id:
                        structured_data.note_validation_error(
                            f"{_TISSUE_SAMPLE_SCHEMA_NAME}:"
                            f" item {submitted_id}"
                            f" external_id {tissue_sample_external_id} does not"
                            f" match {_TISSUE_SCHEMA_NAME} external_id"
                            f" {tissue_external_id}."
                        )


from typing import Dict, List, Optional, Any
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.decorators import structured_data_validator_finish_hook
from submitr.validators.utils import portal_queries, item_utils

# ... existing code remains unchanged ...

# New constants for TPC metadata validation
_NDRI_TPC_ID = "ndri_tpc"
_NDRI_TPC_DISPLAY_TITLE = "NDRI TPC"
_VALIDATING_STUDIES = ["Benchmarking", "Production"]
_METADATA_COMPARISON_PROPERTIES = ["category", "preservation_type"]
_CATEGORY_PROPERTY_NAME = "category"
_PRESERVATION_TYPE_PROPERTY_NAME = "preservation_type"


def _get_or_fetch_tissue_samples(
    external_id: str, 
    cache: Dict[str, List[Dict]], 
    portal_key: Dict, 
    fail_on_error: bool
) -> Optional[List[Dict]]:
    """Get tissue samples from cache or fetch from portal, caching result."""
    if external_id in cache:
        return cache[external_id]
    
    samples = portal_queries.search_tissue_samples_by_external_id(
        external_id, portal_key, fail_on_error
    )
    if samples is not None:
        cache[external_id] = samples
    
    return samples


def _get_or_fetch_tissue(
    tissue_id: str, 
    tissue_cache: Dict[str, Dict], 
    structured_data: StructuredDataSet,
    portal_key: Dict, 
    fail_on_error: bool
) -> Optional[Dict]:
    """Get tissue from cache, structured_data, or fetch from portal."""
    if tissue_id in tissue_cache:
        return tissue_cache[tissue_id]
    
    # First check if tissue is in current submission
    if tissues := structured_data.data.get(_TISSUE_SCHEMA_NAME, []):
        for tissue in tissues:
            if item_utils.get_submitted_id(tissue) == tissue_id:
                tissue_cache[tissue_id] = tissue
                return tissue
    
    # Fetch from portal
    tissue = portal_queries.get_item_by_identifier(
        tissue_id, "Tissue", portal_key, fail_on_error
    )
    if tissue:
        tissue_cache[tissue_id] = tissue
    
    return tissue


def _get_or_fetch_study(
    tissue_id: str, 
    study_cache: Dict[str, str],
    tissue_cache: Dict[str, Dict],
    structured_data: StructuredDataSet,
    portal_key: Dict, 
    fail_on_error: bool
) -> Optional[str]:
    """Get study from cache or fetch from portal, caching result."""
    if tissue_id in study_cache:
        return study_cache[tissue_id]
    
    # Get tissue first
    tissue = _get_or_fetch_tissue(tissue_id, tissue_cache, structured_data, portal_key, fail_on_error)
    if not tissue:
        return None
    
    # Extract study from tissue
    study = tissue.get("study")
    if isinstance(study, dict):
        study_name = study.get("display_title") or study.get("name")
    else:
        study_name = study
    
    if study_name:
        study_cache[tissue_id] = study_name
    
    return study_name


def _should_validate_for_study(study: Optional[str]) -> bool:
    """Check if study requires strict validation (Benchmarking or Production)."""
    return study in _VALIDATING_STUDIES


def _is_tpc_submission(item: Dict[str, Any], portal_key: Dict, fail_on_error: bool) -> bool:
    """
    Determine if item is from TPC submission.
    
    First tries to use submission_centers if present, then falls back to
    submitted_id prefix.
    """
    # Try submission_centers first
    center_identifiers = item_utils.get_submission_center_identifiers(item)
    for center_id in center_identifiers:
        display_title = portal_queries.get_submission_center_display_title(
            center_id, portal_key, fail_on_error
        )
        if display_title == _NDRI_TPC_DISPLAY_TITLE:
            return True
    
    # Fall back to submitted_id prefix
    submitted_id = item_utils.get_submitted_id(item)
    if submitted_id:
        center_code = item_utils.extract_submission_center_from_submitted_id(submitted_id)
        return item_utils.is_tpc_submission_center(center_code)
    
    return False


def _categorize_samples_by_submission_center(
    samples: List[Dict], 
    portal_key: Dict, 
    fail_on_error: bool
) -> tuple[List[Dict], List[Dict]]:
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
        
        # Fall back to querying if needed
        if not is_tpc and submission_centers:
            is_tpc = _is_tpc_submission(sample, portal_key, fail_on_error)
        
        # Last resort: check submitted_id prefix
        if not is_tpc:
            submitted_id = item_utils.get_submitted_id(sample)
            if submitted_id:
                center_code = item_utils.extract_submission_center_from_submitted_id(submitted_id)
                is_tpc = item_utils.is_tpc_submission_center(center_code)
        
        if is_tpc:
            tpc_samples.append(sample)
        else:
            non_tpc_samples.append(sample)
    
    return tpc_samples, non_tpc_samples


def _validate_tpc_duplicate(
    external_id: str, 
    submitted_id: str, 
    tpc_samples: List[Dict], 
    structured_data: StructuredDataSet
) -> bool:
    """
    Validate TPC submission doesn't create duplicate.
    Returns True if validation passes, False if error found.
    """
    if len(tpc_samples) > 0:
        structured_data.note_validation_error(
            f"TissueSample: TPC Tissue Sample with external_id {external_id} already exists"
        )
        return False
    return True


def _validate_gcc_baseline_exists(
    external_id: str, 
    tpc_samples: List[Dict], 
    structured_data: StructuredDataSet
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
    structured_data: StructuredDataSet
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


def _validate_metadata_consistency(
    item: Dict, 
    tpc_sample: Dict, 
    structured_data: StructuredDataSet
) -> None:
    """
    Validate GCC metadata matches TPC baseline for category, preservation_type, sample_sources.
    """
    tpc_accession = item_utils.get_accession(tpc_sample)
    found = tpc_accession or item_utils.get_submitted_id(tpc_sample)
    
    # Compare category and preservation_type
    for prop in _METADATA_COMPARISON_PROPERTIES:
        gcc_value = item.get(prop)
        tpc_value = tpc_sample.get(prop)
        
        if gcc_value and tpc_value and tpc_value != gcc_value:
            structured_data.note_validation_error(
                f"TissueSample: metadata mismatch, {prop} {gcc_value} "
                f"does not match value {tpc_value} in TPC Tissue Sample {found}"
            )
    
    # Compare sample_sources - get first source's uuid
    gcc_sources = item.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])
    tpc_sources = tpc_sample.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])
    
    if gcc_sources and tpc_sources:
        gcc_source = gcc_sources[0]
        tpc_source = tpc_sources[0]
        
        # Extract uuid from source (might be string identifier or dict)
        if isinstance(tpc_source, dict):
            tpc_source_uuid = tpc_source.get("uuid")
        else:
            tpc_source_uuid = tpc_source
        
        # gcc_source in submission will be string identifier
        gcc_source_identifier = gcc_source
        
        # We need to compare UUIDs, but gcc_source might be submitted_id
        # For now, compare directly if both are strings
        # In practice, the portal validation uses UUIDs, but in submitr
        # we're working with identifiers before submission
        # This is a limitation - we'll compare what we have
        if tpc_source_uuid and gcc_source_identifier:
            # If gcc_source looks like a UUID, compare directly
            # Otherwise, we can't easily validate this without more portal queries
            if len(gcc_source_identifier) == 36 and '-' in gcc_source_identifier:
                # Looks like a UUID
                if tpc_source_uuid != gcc_source_identifier:
                    structured_data.note_validation_error(
                        f"TissueSample: metadata mismatch, sample_source {gcc_source_identifier} "
                        f"does not match TPC Tissue Sample {found} sample_source {tpc_source_uuid}"
                    )


@structured_data_validator_finish_hook
def tissue_sample_tpc_metadata_validator(structured_data: StructuredDataSet, **kwargs) -> None:
    """
    Validate TissueSample metadata consistency with TPC baseline samples.
    
    This validator queries the portal to compare against existing samples and ensures:
    - TPC submissions don't create duplicate samples
    - GCC submissions have a corresponding TPC baseline sample
    - GCC submissions don't create duplicate non-TPC samples
    - GCC metadata (category, preservation_type, sample_sources) matches TPC baseline
    
    Only applies to Benchmarking and Production studies.
    """
    # Check if we should skip validation on portal errors
    fail_on_error = kwargs.get("fail_on_portal_error", True)
    
    # Get TissueSample items from submission
    if not isinstance(data := structured_data.data.get(_TISSUE_SAMPLE_SCHEMA_NAME), list):
        return
    
    # Initialize caches
    portal_samples_cache: Dict[str, List[Dict]] = {}
    tissue_cache: Dict[str, Dict] = {}
    study_cache: Dict[str, str] = {}
    seen_external_ids: Dict[str, str] = {}  # external_id -> submitted_id
    
    portal_key = structured_data.portal.key
    
    for item in data:
        submitted_id = item_utils.get_submitted_id(item)
        external_id = item_utils.get_external_id(item)
        
        # Skip if missing required fields
        if not external_id or not submitted_id:
            continue
        
        # Get sample_sources
        sample_sources = item.get(_SAMPLE_SOURCE_PROPERTY_NAME, [])
        if not sample_sources:
            continue
        
        tissue_id = sample_sources[0]
        
        # Get study to determine if we should validate
        study = _get_or_fetch_study(
            tissue_id, study_cache, tissue_cache, structured_data, portal_key, fail_on_error
        )
        
        if not _should_validate_for_study(study):
            continue
        
        # Determine if this is TPC or GCC submission
        is_tpc = _is_tpc_submission(item, portal_key, fail_on_error)
        
        # Query portal for existing samples with this external_id
        existing_samples = _get_or_fetch_tissue_samples(
            external_id, portal_samples_cache, portal_key, fail_on_error
        )
        
        if existing_samples is None:
            # Portal query failed
            if fail_on_error:
                structured_data.note_validation_error(
                    f"TissueSample: Unable to validate {submitted_id} - "
                    f"portal query failed for external_id {external_id}"
                )
            continue
        
        # Categorize existing samples
        tpc_samples, non_tpc_samples = _categorize_samples_by_submission_center(
            existing_samples, portal_key, fail_on_error
        )
        
        # Validate based on submission type
        if is_tpc:
            # TPC submission - check for duplicates
            _validate_tpc_duplicate(external_id, submitted_id, tpc_samples, structured_data)
        else:
            # GCC submission - check baseline exists and no duplicates
            if not _validate_gcc_baseline_exists(external_id, tpc_samples, structured_data):
                continue
            
            if not _validate_gcc_duplicate(
                external_id, submitted_id, non_tpc_samples, seen_external_ids, structured_data
            ):
                continue
            
            # Compare metadata with TPC baseline
            if tpc_samples:
                _validate_metadata_consistency(item, tpc_samples[0], structured_data)
        
        # Track this external_id
        seen_external_ids[external_id] = submitted_id