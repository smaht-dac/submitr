from typing import Dict, List, Optional, Any
from dcicutils import ff_utils


def search_tissue_samples_by_external_id(
    external_id: str, 
    portal_key: Dict, 
) -> Optional[List[Dict]]:
    """
    Query portal for TissueSample items with given external_id.
    
    Args:
        external_id: External ID to search for
        portal_key: Portal authentication key
    
    Returns:
        List of matching TissueSample items
    """
    try:
        query = f"/search/?type=TissueSample&status!=deleted&external_id={external_id}"
        result = ff_utils.search_metadata(query, portal_key)
        return result if result else []
    except Exception as e:
        return None


def get_item_by_identifier(
    identifier: str, 
    item_type: str, 
    portal_key: Dict, 
 ) -> Optional[Dict]:
    """
    Fetch item from portal by identifier.

    Args:
        identifier: submitted_id, uuid, or accession
        item_type: Item type for error messages
        portal_key: Portal authentication key

    Returns:
        Item dict or None on error
    """
    try:
        result = ff_utils.get_metadata(identifier, portal_key)
        return result
    except Exception as e:
         return None


def get_tissue_study(
    tissue_identifier: str, 
    portal_key: Dict, 
    fail_on_error: bool = True
) -> Optional[str]:
    """
    Get study name from Tissue item.
    
    Args:
        tissue_identifier: Tissue submitted_id, uuid, or accession
        portal_key: Portal authentication key
        fail_on_error: If False, return None on error instead of raising
    
    Returns:
        Study name string or None
    """
    try:
        tissue = get_item_by_identifier(tissue_identifier, "Tissue", portal_key, fail_on_error)
        if not tissue:
            return None
        
        # Study might be a link (dict) or just a string
        study = tissue.get("study")
        if isinstance(study, dict):
            return study.get("display_title") or study.get("name")
        return study
    except Exception as e:
        if fail_on_error:
            raise
        return None


def get_submission_center_display_title(
    center_identifier: str, 
    portal_key: Dict, 
) -> Optional[str]:
    """
    Get display_title for SubmissionCenter.

    Args:
        center_identifier: SubmissionCenter identifier
        portal_key: Portal authentication key
        fail_on_error: If False, return None on error instead of raising

    Returns:
        Display title string or None
    """
    try:
        center = get_item_by_identifier(center_identifier, "SubmissionCenter", portal_key, fail_on_error)
        if not center:
            return None
        return center.get("display_title")
    except Exception as e:
        return None