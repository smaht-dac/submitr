"""Pre-upload filename protections for workbook and portal file names."""

import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote


def normalize_upload_filename(value: Any) -> Optional[str]:
    """Return the normalized basename used to compare upload filenames."""
    if not isinstance(value, str) or not value.strip():
        return None
    return os.path.basename(value.strip().replace("\\", "/").rstrip("/")) or None


def _identity(value: dict) -> Optional[str]:
    for key in ("uuid", "@id"):
        if isinstance(value.get(key), str) and value[key]:
            return value[key]
    return None


def _is_file_schema(portal: Any, schema: str) -> bool:
    try:
        return bool(portal.is_schema_file_type(schema))
    except Exception:
        return False


def _file_entries(value: Any, location: str, portal: Any,
                  top_level_file_schema: bool,
                  inherited_identity: Optional[str] = None) -> Iterable[Tuple[str, str, Optional[str]]]:
    """Yield filename, location, and owning-item identity from nested row data."""
    if isinstance(value, dict):
        item_identity = _identity(value) or inherited_identity
        for key, child in value.items():
            if key == "filename" and isinstance(child, str):
                if filename := normalize_upload_filename(child):
                    yield filename, location, item_identity
            elif key == "file" and isinstance(child, str):
                # ``file`` is the normalized upload entry shape emitted by
                # StructuredDataSet.upload_files. Only accept it for a known
                # file sheet or a nested entry explicitly typed as a file schema.
                child_type = value.get("type")
                if top_level_file_schema or (isinstance(child_type, str) and _is_file_schema(portal, child_type)):
                    if filename := normalize_upload_filename(child):
                        yield filename, location, item_identity
            elif isinstance(child, (dict, list)):
                child_location = f"{location}.{key}"
                yield from _file_entries(child, child_location, portal,
                                         top_level_file_schema, item_identity)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _file_entries(child, f"{location}[{index}]", portal,
                                     top_level_file_schema, inherited_identity)


def duplicate_upload_filename_errors(structured_data: Any, portal: Any) -> List[str]:
    """Find duplicate upload basenames and return actionable workbook locations.

    A repeated filename is allowed when every occurrence identifies the same portal
    item, which is the normal shape of an update represented in more than one
    workbook location.
    """
    data = getattr(structured_data, "data", structured_data)
    if not isinstance(data, dict):
        return []

    occurrences: Dict[str, List[Tuple[str, Optional[str]]]] = defaultdict(list)
    for sheet, rows in data.items():
        if not isinstance(rows, list) or not _is_file_schema(portal, sheet):
            continue
        for index, row in enumerate(rows):
            location = f"{sheet} row {index + 2}"
            for filename, entry_location, item_identity in _file_entries(
                row, location, portal, top_level_file_schema=True
            ):
                occurrences[filename].append(
                    (f"{entry_location} ({filename})", item_identity)
                )

    errors = []
    for normalized_name, entries in occurrences.items():
        if len(entries) < 2:
            continue
        identities = {identity for _, identity in entries}
        if len(identities) == 1 and None not in identities:
            continue
        displayed_name = normalized_name
        locations = "; ".join(location for location, _ in entries)
        errors.append(
            f"Duplicate upload filename '{displayed_name}' referenced at {locations}. "
            "Use a unique filename for each portal item."
        )
    return errors


def _center_tokens(value: Any) -> set:
    if isinstance(value, (list, tuple, set)):
        result = set()
        for child in value:
            result.update(_center_tokens(child))
        return result
    if isinstance(value, dict):
        result = set()
        for key in ("@id", "uuid", "identifier", "name", "display_title"):
            result.update(_center_tokens(value.get(key)))
        return result
    if not isinstance(value, str) or not value.strip():
        return set()
    normalized = value.strip().casefold().rstrip("/")
    tokens = {normalized}
    if "/" in normalized:
        tokens.add(normalized.rsplit("/", 1)[-1])
    return tokens


def _record_submission_centers(record: dict) -> Any:
    return record.get("submission_centers", record.get("submission_center"))


def _item_tokens(value: Any) -> set:
    if not isinstance(value, str) or not value:
        return set()
    normalized = value.casefold().rstrip("/")
    tokens = {normalized}
    if "/" in normalized:
        tokens.add(normalized.rsplit("/", 1)[-1])
    return tokens


def _portal_file_records(filename: str, portal: Any) -> List[dict]:
    try:
        response = portal.get(f"/search/?filename={quote(filename)}&type=File")
        if not response or response.status_code != 200:
            return []
        payload = response.json()
        graph = payload.get("@graph", []) if isinstance(payload, dict) else []
        records = []
        for result in graph if isinstance(graph, list) else []:
            if not isinstance(result, dict):
                continue
            summary = result.get("file_summary")
            record = dict(summary) if isinstance(summary, dict) else {}
            record.update(result)
            uuid = record.get("uuid") or record.get("@id")
            if not _record_submission_centers(record) and uuid:
                metadata = portal.get_metadata(uuid, raise_exception=False)
                if isinstance(metadata, dict):
                    merged = dict(metadata)
                    merged.update(record)
                    record = merged
            if record:
                records.append(record)
        return records
    except Exception:
        # A lookup failure must not change the established behavior for an
        # inaccessible or out-of-scope portal record.
        return []


class FilenameCollisionError(ValueError):
    """Raised when a filename is already owned by another same-center file."""


def check_portal_filename_collision(file: Any, portal: Any,
                                    submission_centers: Any = None) -> None:
    """Raise if ``file.name`` belongs to another file in a submitting center."""
    centers = _center_tokens(submission_centers)
    if not centers or not getattr(file, "name", None):
        return

    for record in _portal_file_records(file.name, portal):
        record_centers = _center_tokens(_record_submission_centers(record))
        if not centers.intersection(record_centers):
            continue
        record_uuid = record.get("uuid") or record.get("@id")
        if record_uuid and _item_tokens(record_uuid).intersection(_item_tokens(getattr(file, "uuid", None))):
            continue
        raise FilenameCollisionError(
            f"A portal file named '{file.name}' already exists for submission center "
            f"'{sorted(centers)[0]}' ({record_uuid or 'unknown item'}). "
            "Choose a unique filename."
        )
