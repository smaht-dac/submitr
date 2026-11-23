from typing import Dict, List, Any


def get_external_id(item: Dict[str, Any]) -> str:
    """Extract external_id from item, return empty string if not present."""
    return item.get("external_id", "")


def get_submitted_id(item: Dict[str, Any]) -> str:
    """Extract submitted_id from item."""
    return item.get("submitted_id", "")


def get_uuid(item: Dict[str, Any]) -> str:
    """Extract uuid from item."""
    return item.get("uuid", "")


def get_accession(item: Dict[str, Any]) -> str:
    """Extract accession from item."""
    return item.get("accession", "")


def extract_submission_center_from_submitted_id(submitted_id: str) -> str:
    """Extract submission center code from submitted_id (prefix before first underscore)."""
    if not submitted_id:
        return ""
    return submitted_id.split("_")[0]


def is_tpc_submission_center(submission_center_code: str) -> bool:
    """Check if submission center code indicates TPC (NDRI) submission."""
    return submission_center_code == "NDRI"


def get_submission_center_identifiers(item: Dict[str, Any]) -> List[str]:
    """
    Get submission center identifiers from item.
    Returns:
        List of submission center identifiers (submitted_ids, uuids, or accessions)
    """
    centers = item.get("submission_centers", [])
    if not centers:
        return []

    # Centers might be strings (identifiers) or dicts with embedded data
    identifiers = []
    for center in centers:
        if isinstance(center, str):
            identifiers.append(center)
        elif isinstance(center, dict):
            # Try to get identifier from embedded object
            identifier = (
                center.get("submitted_id") or center.get("uuid") or center.get("@id")
            )
            if identifier:
                identifiers.append(identifier)

    return identifiers
