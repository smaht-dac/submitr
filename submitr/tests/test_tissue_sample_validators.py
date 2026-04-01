from unittest import mock
import pytest
from submitr.validators.tissue_sample_validator import (
    _tissue_sample_external_id_validator,
    _tissue_sample_metadata_validator,
    _is_tpc_submission,
    _get_or_fetch_tissue_samples,
    _categorize_samples_by_submission_center,
    _validate_tpc_duplicate,
    _validate_gcc_baseline_exists,
    _validate_gcc_duplicate,
    _is_tissue_submitted_id,
    _get_tissue_submitted_id,
    _validate_metadata_consistency,
    _tissue_sample_external_id_category_match_validator,
    _text_before_nth,
    _text_after_nth,
    _extract_donor_tissue_prefix,
    _extract_donor_tissue_prefix_from_sample_source,
    _tissue_sample_external_id_in_submitted_id_validator,
    _tissue_sample_external_id_sample_source_consistency_validator,
    _note_validation_warning,
)

from .datafixtures import (
    NDRI_TISSUE_SUBMITTED_ID,
    NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    GCC_TISSUE_SUBMITTED_ID,
    GCC_TISSUE_SAMPLE_SUBMITTED_ID,
    BENCHMARKING_EXTERNAL_ID,
    PRODUCTION_EXTERNAL_ID,
    NON_PRODUCTION_EXTERNAL_ID,
    MOCK_PORTAL_KEY,
    TISSUE_EXTERNAL_ID,
    TISSUE_SAMPLE_EXTERNAL_ID,
    TISSUE_UUID,
    NDRI_TPC_CENTER,
    GCC_CENTER,
    BWH_CENTER,
    make_structured_data_mock,
    make_tissue_sample,
    make_tissue,
)


# ============================================================================
# Test _is_tpc_submission()
# ============================================================================


def test_is_tpc_submission_ndri_prefix():
    """Returns True for NDRI prefix."""
    assert _is_tpc_submission("NDRI_TISSUE_SAMPLE_001") is True
    assert _is_tpc_submission("NDRI_ANYTHING") is True


def test_is_tpc_submission_gcc_prefix():
    """Returns False for non-NDRI prefix."""
    assert _is_tpc_submission("DAC_TISSUE_SAMPLE_001") is False
    assert _is_tpc_submission("BWH_TISSUE_SAMPLE_001") is False
    assert _is_tpc_submission("UW_SAMPLE") is False


def test_is_tpc_submission_empty_string():
    """Returns False for empty string."""
    assert _is_tpc_submission("") is False


# ============================================================================
# Test _is_tissue_submitted_id()
# ============================================================================


def test_is_tissue_submitted_id_valid():
    """Returns True for NDRI_TISSUE_* pattern."""
    assert _is_tissue_submitted_id("NDRI_TISSUE_SMHT001") is True
    assert _is_tissue_submitted_id("NDRI_TISSUE_ST001") is True


def test_is_tissue_submitted_id_invalid():
    """Returns False for other patterns."""
    assert _is_tissue_submitted_id("DAC_TISSUE_001") is False
    assert _is_tissue_submitted_id("NDRI_SOMETHING") is False


def test_is_tissue_submitted_id_tissue_sample():
    """Returns False for NDRI_TISSUE_SAMPLE_*."""
    assert _is_tissue_submitted_id("NDRI_TISSUE_SAMPLE_001") is False


def test_is_tissue_submitted_id_empty():
    """Returns False for empty string."""
    assert _is_tissue_submitted_id("") is False


# ============================================================================
# Test _categorize_samples_by_submission_center()
# ============================================================================


def test_categorize_all_tpc_samples():
    """All samples have NDRI TPC center."""
    samples = [
        {"submitted_id": "NDRI_SAMPLE_001", "submission_centers": [NDRI_TPC_CENTER]},
        {"submitted_id": "NDRI_SAMPLE_002", "submission_centers": [NDRI_TPC_CENTER]},
    ]
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 2
    assert len(gcc) == 0


def test_categorize_all_gcc_samples():
    """All samples have non-TPC center."""
    samples = [
        {"submitted_id": "DAC_SAMPLE_001", "submission_centers": [GCC_CENTER]},
        {"submitted_id": "BWH_SAMPLE_002", "submission_centers": [BWH_CENTER]},
    ]
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 0
    assert len(gcc) == 2


def test_categorize_mixed_samples():
    """Mix of TPC and GCC samples."""
    samples = [
        {"submitted_id": "NDRI_SAMPLE_001", "submission_centers": [NDRI_TPC_CENTER]},
        {"submitted_id": "DAC_SAMPLE_002", "submission_centers": [GCC_CENTER]},
        {"submitted_id": "NDRI_SAMPLE_003", "submission_centers": [NDRI_TPC_CENTER]},
    ]
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 2
    assert len(gcc) == 1


def test_categorize_empty_list():
    """Returns two empty lists."""
    tpc, gcc = _categorize_samples_by_submission_center([])
    assert tpc == []
    assert gcc == []


@pytest.mark.parametrize("samples", [
    # empty submission_centers list present
    [
        {"submitted_id": "NDRI_SAMPLE_001", "submission_centers": []},
        {"submitted_id": "DAC_SAMPLE_002", "submission_centers": []},
    ],
    # submission_centers key absent entirely
    [
        {"submitted_id": "NDRI_SAMPLE_001"},
        {"submitted_id": "DAC_SAMPLE_002"},
    ],
])
def test_categorize_falls_back_to_submitted_id_prefix(samples):
    """Falls back to submitted_id prefix when submission_centers is absent or empty."""
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 1
    assert len(gcc) == 1
    assert tpc[0]["submitted_id"] == "NDRI_SAMPLE_001"
    assert gcc[0]["submitted_id"] == "DAC_SAMPLE_002"


# ============================================================================
# Test _get_or_fetch_tissue_samples()
# ============================================================================


def test_get_tissue_samples_cache_hit():
    """Returns cached value without portal call."""
    cache = {PRODUCTION_EXTERNAL_ID: [{"sample": "data"}]}
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id"
    ) as mock_search:
        result = _get_or_fetch_tissue_samples(
            PRODUCTION_EXTERNAL_ID, cache, MOCK_PORTAL_KEY
        )
        assert result == [{"sample": "data"}]
        mock_search.assert_not_called()


def test_get_tissue_samples_cache_miss_failure():
    """Returns None on portal failure."""
    cache = {}
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=None,
    ) as mock_search:
        result = _get_or_fetch_tissue_samples(
            PRODUCTION_EXTERNAL_ID, cache, MOCK_PORTAL_KEY
        )
        assert result is None
        mock_search.assert_called_once()


@pytest.mark.parametrize("portal_return,expected_cached", [
    ([{"data": "test"}], [{"data": "test"}]),
    (None, None),
])
def test_get_tissue_samples_caches_portal_result(portal_return, expected_cached):
    """Portal result (including None) is written into the cache."""
    cache = {}
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=portal_return,
    ):
        result = _get_or_fetch_tissue_samples(
            PRODUCTION_EXTERNAL_ID, cache, MOCK_PORTAL_KEY
        )
    assert result == expected_cached
    assert cache[PRODUCTION_EXTERNAL_ID] == expected_cached


# ============================================================================
# Test _get_tissue_submitted_id()
# ============================================================================


def test_get_tissue_submitted_id_cache_hit():
    """Returns cached submitted_id without portal call."""
    cache = {TISSUE_UUID: NDRI_TISSUE_SUBMITTED_ID}
    with mock.patch(
        "submitr.validators.utils.portal.get_item_by_identifier"
    ) as mock_get_item:
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id"
        ) as mock_get_submitted_id:
            result = _get_tissue_submitted_id(TISSUE_UUID, cache, MOCK_PORTAL_KEY)
            assert result == NDRI_TISSUE_SUBMITTED_ID
            mock_get_item.assert_not_called()
            mock_get_submitted_id.assert_not_called()


def test_get_tissue_submitted_id_not_found():
    """Returns None when tissue not found."""
    cache = {}
    with mock.patch(
        "submitr.validators.utils.portal.get_item_by_identifier", return_value=None
    ):
        result = _get_tissue_submitted_id(TISSUE_UUID, cache, MOCK_PORTAL_KEY)
        assert result is None


@pytest.mark.parametrize("portal_return,expected_cached", [
    ({"uuid": TISSUE_UUID}, NDRI_TISSUE_SUBMITTED_ID),
    (None, None),
])
def test_get_tissue_submitted_id_caches_portal_result(portal_return, expected_cached):
    """Portal result (including None) is written into the cache."""
    cache = {}
    with mock.patch(
        "submitr.validators.utils.portal.get_item_by_identifier",
        return_value=portal_return,
    ):
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id",
            return_value=NDRI_TISSUE_SUBMITTED_ID,
        ):
            result = _get_tissue_submitted_id(TISSUE_UUID, cache, MOCK_PORTAL_KEY)
    assert result == expected_cached
    assert cache[TISSUE_UUID] == expected_cached


# ============================================================================
# Test _validate_tpc_duplicate()
# ============================================================================


def test_validate_tpc_duplicate_no_existing():
    """No error when no existing samples."""
    mock_data = make_structured_data_mock()
    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID, [], mock_data
    )
    mock_data.note_validation_error.assert_not_called()


def test_validate_tpc_duplicate_same_item_update():
    """No error when updating same item."""
    mock_data = make_structured_data_mock()
    existing_tpc = [{"submitted_id": NDRI_TISSUE_SAMPLE_SUBMITTED_ID}]
    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_tpc, mock_data
    )
    mock_data.note_validation_error.assert_not_called()


def test_validate_tpc_duplicate_different_item():
    """Error when different TPC sample exists."""
    mock_data = make_structured_data_mock()
    existing_tpc = [{"submitted_id": "NDRI_OTHER_SAMPLE"}]
    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_tpc, mock_data
    )
    expected_message = (
        f"TissueSample: TPC Tissue Sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_tpc_duplicate_multiple_existing():
    """Error when multiple TPC samples exist."""
    mock_data = make_structured_data_mock()
    existing_tpc = [
        {"submitted_id": "NDRI_SAMPLE_001"},
        {"submitted_id": "NDRI_SAMPLE_002"},
    ]
    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_tpc, mock_data
    )
    expected_message = (
        f"TissueSample: TPC Tissue Sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


# ============================================================================
# Test _validate_gcc_baseline_exists()
# ============================================================================


def test_validate_gcc_baseline_exists_found():
    """Returns True when TPC sample exists."""
    mock_data = make_structured_data_mock()
    tpc_samples = [{"submitted_id": NDRI_TISSUE_SAMPLE_SUBMITTED_ID}]
    result = _validate_gcc_baseline_exists(
        PRODUCTION_EXTERNAL_ID, tpc_samples, mock_data
    )
    assert result is True
    mock_data.note_validation_error.assert_not_called()


def test_validate_gcc_baseline_no_tpc_sample():
    """Returns False and logs error when no TPC sample."""
    mock_data = make_structured_data_mock()
    result = _validate_gcc_baseline_exists(PRODUCTION_EXTERNAL_ID, [], mock_data)
    assert result is False
    expected_message = (
        f"TissueSample: No TPC Tissue Sample found with "
        f"external_id {PRODUCTION_EXTERNAL_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_gcc_baseline_multiple_tpc():
    """Returns True when multiple TPC samples exist."""
    mock_data = make_structured_data_mock()
    tpc_samples = [
        {"submitted_id": "NDRI_SAMPLE_001"},
        {"submitted_id": "NDRI_SAMPLE_002"},
    ]
    result = _validate_gcc_baseline_exists(
        PRODUCTION_EXTERNAL_ID, tpc_samples, mock_data
    )
    assert result is True
    mock_data.note_validation_error.assert_not_called()


# ============================================================================
# Test _validate_gcc_duplicate()
# ============================================================================


def test_validate_gcc_duplicate_no_existing():
    """Returns True when no existing GCC samples."""
    mock_data = make_structured_data_mock()
    seen = {}
    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID, [],
        seen, mock_data
    )
    assert result is True
    mock_data.note_validation_error.assert_not_called()


def test_validate_gcc_duplicate_same_item_update():
    """Returns True when updating same item."""
    mock_data = make_structured_data_mock()
    seen = {}
    existing_gcc = [{"submitted_id": GCC_TISSUE_SAMPLE_SUBMITTED_ID}]
    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc, seen, mock_data,
    )
    assert result is True
    mock_data.note_validation_error.assert_not_called()


def test_validate_gcc_duplicate_different_item_in_portal():
    """Returns False when different GCC sample exists in portal."""
    mock_data = make_structured_data_mock()
    seen = {}
    existing_gcc = [{"submitted_id": "DAC_OTHER_SAMPLE"}]
    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc, seen, mock_data,
    )
    assert result is False
    expected_message = (
        f"TissueSample: A non-TPC sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_gcc_duplicate_different_item_in_batch():
    """Returns False when different GCC sample in current batch."""
    mock_data = make_structured_data_mock()
    seen = {PRODUCTION_EXTERNAL_ID: "DAC_OTHER_SAMPLE"}
    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID, [],
        seen, mock_data
    )
    assert result is False
    expected_message = (
        f"TissueSample: A non-TPC sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists in this submission"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_gcc_duplicate_multiple_existing():
    """Returns False when multiple GCC samples exist."""
    mock_data = make_structured_data_mock()
    seen = {}
    existing_gcc = [
        {"submitted_id": "DAC_SAMPLE_001"},
        {"submitted_id": "BWH_SAMPLE_002"},
    ]
    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc, seen, mock_data,
    )
    assert result is False
    expected_message = (
        f"TissueSample: A non-TPC sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


# ============================================================================
# Test _validate_metadata_consistency()
# ============================================================================


def test_validate_metadata_consistency_all_match():
    """No errors when all metadata matches."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Specimen", preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier",
            return_value={"submitted_id": GCC_TISSUE_SUBMITTED_ID},
        ):
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id",
                return_value=GCC_TISSUE_SUBMITTED_ID,
            ):
                _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    mock_data.note_validation_error.assert_not_called()


def test_validate_metadata_consistency_category_mismatch():
    """Error on category mismatch."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Homogenate", preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id"
    ) as mock_get_submitted:
        mock_get_submitted.return_value = NDRI_TISSUE_SAMPLE_SUBMITTED_ID
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            mock_get_item.return_value = {"submitted_id": GCC_TISSUE_SUBMITTED_ID}
            _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    expected_message = (
        f"TissueSample: metadata mismatch, category Homogenate "
        f"does not match value Specimen in TPC Tissue Sample "
        f"{NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_metadata_consistency_preservation_type_mismatch():
    """Error on preservation_type mismatch."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Specimen", preservation_type="Frozen",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id"
    ) as mock_get_submitted:
        mock_get_submitted.return_value = NDRI_TISSUE_SAMPLE_SUBMITTED_ID
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            mock_get_item.return_value = {"submitted_id": GCC_TISSUE_SUBMITTED_ID}
            _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    expected_message = (
        f"TissueSample: metadata mismatch, preservation_type "
        f"Frozen does not match value Fresh in TPC Tissue"
        f" Sample {NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_metadata_consistency_both_mismatch():
    """Multiple errors for multiple mismatches."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Homogenate", preservation_type="Frozen",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier",
            return_value={"submitted_id": GCC_TISSUE_SUBMITTED_ID},
        ):
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id",
                return_value=GCC_TISSUE_SUBMITTED_ID,
            ):
                _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    assert mock_data.note_validation_error.call_count == 2
    calls = [call[0][0] for call in mock_data.note_validation_error.call_args_list]
    assert any("category Homogenate does not match value Specimen" in c for c in calls)
    assert any("preservation_type Frozen does not match value Fresh" in c for c in calls)


def test_validate_metadata_consistency_sample_source_mismatch():
    """Error when sample_sources don't match."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        ["DAC_TISSUE_DIFFERENT"], category="Specimen", preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            def get_item_side_effect(identifier, key):
                if identifier == TISSUE_UUID:
                    return {"submitted_id": NDRI_TISSUE_SUBMITTED_ID}
                elif identifier == "DAC_TISSUE_DIFFERENT":
                    return {"submitted_id": "DAC_TISSUE_DIFFERENT"}
                return None
            mock_get_item.side_effect = get_item_side_effect
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id"
            ) as mock_get_submitted:
                mock_get_submitted.side_effect = lambda item: item.get("submitted_id")
                _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    expected_message = (
        f"TissueSample: metadata mismatch: sample_source "
        f"DAC_TISSUE_DIFFERENT does not match TPC "
        f"TissueSample sample_source {NDRI_TISSUE_SUBMITTED_ID}"
    )
    mock_data.note_validation_error.assert_called_with(expected_message)


def test_validate_metadata_consistency_missing_values():
    """No error when GCC value is None/missing."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Specimen", preservation_type="Fresh",
    )
    gcc_item["category"] = None
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier",
            return_value={"submitted_id": GCC_TISSUE_SUBMITTED_ID},
        ):
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id",
                return_value=GCC_TISSUE_SUBMITTED_ID,
            ):
                _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
    mock_data.note_validation_error.assert_not_called()


def test_validate_metadata_consistency_uses_tissue_cache():
    """Verifies caching behavior for tissue lookups."""
    mock_data = make_structured_data_mock()
    tissue_cache = {TISSUE_UUID: NDRI_TISSUE_SUBMITTED_ID}
    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], category="Specimen", preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}], category="Specimen", preservation_type="Fresh",
    )
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id",
                return_value=GCC_TISSUE_SUBMITTED_ID,
            ):
                _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)
            assert mock_get_item.call_count <= 1


# ============================================================================
# Test _tissue_sample_external_id_validator()
# ============================================================================


def test_external_id_validator_no_tissue_samples():
    """Returns early if no TissueSample data."""
    mock_data = make_structured_data_mock({"Tissue": []})
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_no_sample_sources():
    """Skips items without sample_sources."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, TISSUE_SAMPLE_EXTERNAL_ID, []
    )
    del tissue_sample["sample_sources"]
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_matching_ids():
    """No error when external_ids match."""
    tissue = make_tissue(NDRI_TISSUE_SUBMITTED_ID, TISSUE_EXTERNAL_ID)
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, TISSUE_SAMPLE_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_mismatch_tpc_tissue_sample():
    """Error when TPC TissueSample external_id doesn't match Tissue."""
    tissue = make_tissue(NDRI_TISSUE_SUBMITTED_ID, "SMHT999-3A")
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3A-001",
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    _tissue_sample_external_id_validator(mock_data)
    expected_message = (
        f"TissueSample: item {NDRI_TISSUE_SAMPLE_SUBMITTED_ID} external_id "
        f"SMHT001-3A-001 does not match Tissue external_id SMHT999-3A."
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_external_id_validator_mismatch_tpc_tissue():
    """Error when TPC Tissue linked from non-TPC TissueSample."""
    tissue = make_tissue(NDRI_TISSUE_SUBMITTED_ID, "SMHT999-3A")
    tissue_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3A-001",
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    _tissue_sample_external_id_validator(mock_data)
    expected_message = (
        f"TissueSample: item {GCC_TISSUE_SAMPLE_SUBMITTED_ID} external_id"
        f" SMHT001-3A-001 does not match Tissue external_id SMHT999-3A."
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_external_id_validator_non_tpc_submission():
    """No validation when neither is TPC."""
    tissue = make_tissue(GCC_TISSUE_SUBMITTED_ID, "SMHT999-3A")
    tissue_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3A-001",
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_tissue_not_in_data():
    """Handles missing Tissue gracefully."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, TISSUE_SAMPLE_EXTERNAL_ID,
        ["NONEXISTENT_TISSUE"], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_no_submitted_id():
    """Skips items without submitted_id."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, TISSUE_SAMPLE_EXTERNAL_ID, [NDRI_TISSUE_SUBMITTED_ID],
    )
    del tissue_sample["submitted_id"]
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


# ============================================================================
# Test _tissue_sample_metadata_validator()
# ============================================================================


def test_metadata_validator_no_tissue_samples():
    """Returns early if no TissueSample data."""
    mock_data = make_structured_data_mock({"Tissue": []})
    _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_missing_required_fields():
    """Skips items missing submitted_id or external_id."""
    sample_no_submitted_id = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [NDRI_TISSUE_SUBMITTED_ID],
    )
    del sample_no_submitted_id["submitted_id"]
    sample_no_external_id = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [GCC_TISSUE_SUBMITTED_ID],
    )
    del sample_no_external_id["external_id"]
    mock_data = make_structured_data_mock(
        {"TissueSample": [sample_no_submitted_id, sample_no_external_id]}
    )
    _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_non_production_external_id():
    """Skips validation for non-Benchmarking/Production samples."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, NON_PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_tpc_new_submission():
    """Allows new TPC sample."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ):
        _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_tpc_update_same_item():
    """Allows TPC to update own sample."""
    existing_tpc = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[existing_tpc],
    ):
        _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_tpc_duplicate():
    """Rejects duplicate TPC submission."""
    existing_tpc = make_tissue_sample(
        "NDRI_OTHER_SAMPLE", PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[existing_tpc],
    ):
        _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: TPC Tissue Sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_new_with_tpc_baseline():
    """Allows new GCC when TPC exists with matching metadata."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [{"uuid": TISSUE_UUID}],
        category="Specimen", preservation_type="Fresh", submission_centers=[NDRI_TPC_CENTER],
    )
    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen", preservation_type="Fresh", submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample],
    ):
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id",
            return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        ):
            with mock.patch(
                "submitr.validators.utils.portal.get_item_by_identifier",
                return_value={"submitted_id": GCC_TISSUE_SUBMITTED_ID},
            ):
                with mock.patch(
                    "submitr.validators.utils.item.get_submitted_id",
                    return_value=GCC_TISSUE_SUBMITTED_ID,
                ):
                    _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_gcc_update_same_item():
    """Allows GCC to update own sample."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [{"uuid": TISSUE_UUID}],
        category="Specimen", preservation_type="Fresh", submission_centers=[NDRI_TPC_CENTER],
    )
    existing_gcc = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [{"uuid": "gcc-tissue-uuid"}],
        category="Specimen", preservation_type="Fresh", submission_centers=[GCC_CENTER],
    )
    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen", preservation_type="Fresh", submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample, existing_gcc],
    ):
        _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_gcc_no_tpc_baseline():
    """Rejects GCC without TPC baseline."""
    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ):
        _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: No TPC Tissue Sample found with "
        f"external_id {PRODUCTION_EXTERNAL_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_duplicate():
    """Rejects duplicate GCC submission."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    existing_gcc = make_tissue_sample(
        "DAC_OTHER_SAMPLE", PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample, existing_gcc],
    ):
        _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: A non-TPC sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_metadata_mismatch():
    """Rejects GCC when metadata doesn't match TPC."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [{"uuid": TISSUE_UUID}],
        category="Specimen", preservation_type="Fresh", submission_centers=[NDRI_TPC_CENTER],
    )
    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [GCC_TISSUE_SUBMITTED_ID],
        category="Homogenate", preservation_type="Fresh", submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample],
    ):
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id"
        ) as mock_get_submitted:
            mock_get_submitted.side_effect = lambda item: item.get("submitted_id")
            with mock.patch(
                "submitr.validators.utils.portal.get_item_by_identifier"
            ) as mock_get_item:
                mock_get_item.return_value = {
                    "submitted_id": GCC_TISSUE_SUBMITTED_ID,
                    "uuid": TISSUE_UUID,
                }
                _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: metadata mismatch, category Homogenate does not match "
        f"value Specimen in TPC Tissue Sample {NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_multiple_items_mixed():
    """Processes multiple TissueSamples correctly."""
    sample1 = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    sample2 = make_tissue_sample(
        "NDRI_SAMPLE_002", BENCHMARKING_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [sample1, sample2]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ):
        _tissue_sample_metadata_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_intra_batch_duplicate():
    """Detects duplicates within submission batch."""
    sample1 = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    sample2 = make_tissue_sample(
        "DAC_DIFFERENT_SAMPLE", PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID], submission_centers=[GCC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [sample1, sample2]})
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID, [{"uuid": TISSUE_UUID}],
        category="Specimen", preservation_type="Fresh", submission_centers=[NDRI_TPC_CENTER],
    )
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample],
    ):
        _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: A sample with external_id "
        f"{PRODUCTION_EXTERNAL_ID} already exists in this submission"
    )
    assert mock_data.note_validation_error.call_count == 1
    mock_data.note_validation_error.assert_called_with(expected_message)


def test_metadata_validator_caching_behavior():
    """Verifies portal queries are cached."""
    sample1 = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    sample2 = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [sample1, sample2]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ) as mock_search:
        _tissue_sample_metadata_validator(mock_data)
        assert mock_search.call_count == 1


def test_metadata_validator_portal_query_failure():
    """Handles portal query failure gracefully."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID], submission_centers=[NDRI_TPC_CENTER],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=None,
    ):
        _tissue_sample_metadata_validator(mock_data)
    expected_message = (
        f"TissueSample: Unable to validate {NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
        f" - portal query failed for external_id {PRODUCTION_EXTERNAL_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


# ============================================================================
# Test _tissue_sample_external_id_category_match_validator()
# ============================================================================

_VALID_CATEGORY_EXTERNAL_IDS = [
    ("Tissue Aliquot", "SMHT001-3AT-001"),
    ("Cells", "SMHT001-3AC-001X"),
    ("Core", "SMHT001-3AT-001A1"),
    ("Homogenate", "SMHT001-1AT-001X"),
    ("Specimen", "SMHT001-3AT-001S1"),
    ("Liquid", "SMHT001-3A-001X"),
]

_INVALID_CATEGORY_EXTERNAL_IDS = [
    ("Tissue Aliquot", "SMHT001-2AT-001", "2 not in [13]"),
    ("Cells", "SMHT001-3AC-001", "missing trailing X"),
    ("Core", "SMHT001-3AT-001G1", "G not in [A-F]"),
    ("Homogenate", "SMHT001-3AT-001X", "3 not valid, only 1 permitted"),
    ("Specimen", "SMHT001-3AT-001", "missing [S-W][1-9] suffix"),
    ("Liquid", "SMHT001-3C-001X", "C not in [AB]"),
]


def test_ext_id_category_no_schema_data():
    """Returns early when no TissueSample data."""
    mock_data = make_structured_data_mock({})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_category_empty_list():
    """No error when TissueSample list is empty."""
    mock_data = make_structured_data_mock({"TissueSample": []})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_category_unknown_category():
    """No error when category is not in _TISSUE_CATEGORIES."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3AT-001", [], category="Unknown",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("category,external_id", _VALID_CATEGORY_EXTERNAL_IDS)
def test_ext_id_category_valid(category, external_id):
    """No error when external_id matches the expected pattern for its category."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, external_id, [], category=category,
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("category,external_id,reason", _INVALID_CATEGORY_EXTERNAL_IDS)
def test_ext_id_category_invalid(category, external_id, reason):
    """Error when external_id does not match the expected pattern for its category."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, external_id, [], category=category,
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert f"has category {category}" in error_msg
    assert f"external_id {external_id}" in error_msg
    assert "does not match expected pattern" in error_msg


def test_ext_id_category_error_includes_submitted_id():
    """Error message includes the item submitted_id."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-2AT-001", [], category="Tissue Aliquot",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert NDRI_TISSUE_SAMPLE_SUBMITTED_ID in error_msg


def test_ext_id_category_cross_category_core_as_tissue_aliquot():
    """Error when Core-format external_id is submitted under Tissue Aliquot category."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3AT-001A1", [], category="Tissue Aliquot",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()


def test_ext_id_category_cross_category_tissue_aliquot_as_core():
    """Error when Tissue Aliquot-format external_id is submitted under Core category."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3AT-001", [], category="Core",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()


def test_ext_id_category_valid_and_invalid_in_same_batch():
    """Only invalid items produce errors when mixed with valid ones."""
    valid_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-3AT-001", [], category="Tissue Aliquot",
    )
    invalid_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID, "SMHT001-2AT-001", [], category="Tissue Aliquot",
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [valid_sample, invalid_sample]}
    )
    _tissue_sample_external_id_category_match_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 1
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert GCC_TISSUE_SAMPLE_SUBMITTED_ID in error_msg


def test_ext_id_category_multiple_invalid_items():
    """Each invalid item independently produces an error."""
    samples = [
        make_tissue_sample(
            f"NDRI_SAMPLE_{i:03d}", "SMHT001-2AT-001", [], category="Tissue Aliquot"
        )
        for i in range(3)
    ]
    mock_data = make_structured_data_mock({"TissueSample": samples})
    _tissue_sample_external_id_category_match_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 3


@pytest.mark.parametrize("external_id", [
    "SMHT001-3AT-001",
    "SMHT001-3AT-125",
    "SMHT001-3AT-010",
    "SMHT001-3AT-100",
])
def test_ext_id_category_range_valid_boundaries(external_id):
    """No error for valid boundary and mid-range values 001-125."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, external_id, [], category="Tissue Aliquot",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("external_id", [
    "SMHT001-3AT-000",
    "SMHT001-3AT-126",
    "SMHT001-3AT-999",
])
def test_ext_id_category_range_invalid_boundaries(external_id):
    """Error for out-of-range values outside 001-125."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID, external_id, [], category="Tissue Aliquot",
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_category_match_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()


# ============================================================================
# Test _text_before_nth()
# ============================================================================


@pytest.mark.parametrize("text,delimiter,n,expected", [
    ("SMHT001-3G-001D2", "-", 2, "SMHT001-3G"),
    ("SMHT001-3G-001D2", "-", 1, "SMHT001"),
    ("NDRI_TISSUE_SMHT001", "_", 2, "NDRI_TISSUE"),
    ("A-B-C-D-E", "-", 3, "A-B-C"),
])
def test_text_before_nth_returns_expected(text, delimiter, n, expected):
    """Returns correct prefix for valid inputs."""
    assert _text_before_nth(text, delimiter, n) == expected


@pytest.mark.parametrize("text,delimiter,n", [
    ("SMHT001-3G", "-", 3),   # n exceeds delimiter count
    ("A-B", "-", 2),           # exactly n parts (n-1 delimiters present)
    ("SMHT001", "-", 1),       # delimiter absent
    ("", "-", 1),              # empty string
])
def test_text_before_nth_returns_none(text, delimiter, n):
    """Returns None for all insufficient-delimiter inputs."""
    assert _text_before_nth(text, delimiter, n) is None


def test_text_before_nth_same_result_across_samples_same_tissue():
    """Two samples from the same tissue produce identical prefixes."""
    assert _text_before_nth("SMHT001-3G-001D2", "-", 2) == \
           _text_before_nth("SMHT001-3G-002D1", "-", 2)


# ============================================================================
# Test _text_after_nth()
# ============================================================================


@pytest.mark.parametrize("text,delimiter,n,expected", [
    ("NDRI_TISSUE_SMHT001-3G-DESCEN_COLON", "_", 2, "SMHT001-3G-DESCEN_COLON"),
    ("NDRI_TISSUE_SMHT001", "_", 1, "TISSUE_SMHT001"),
    ("SMHT001-3G-001D2", "-", 2, "001D2"),
    ("A_B", "_", 1, "B"),
])
def test_text_after_nth_returns_expected(text, delimiter, n, expected):
    """Returns correct suffix for valid inputs."""
    assert _text_after_nth(text, delimiter, n) == expected


@pytest.mark.parametrize("text,delimiter,n", [
    ("NDRI_TISSUE", "_", 3),   # n exceeds delimiter count
    ("SMHT001", "_", 1),        # delimiter absent
    ("", "_", 1),               # empty string
])
def test_text_after_nth_returns_none(text, delimiter, n):
    """Returns None for all insufficient-delimiter inputs."""
    assert _text_after_nth(text, delimiter, n) is None


def test_text_after_nth_preserves_remaining_delimiters():
    """Remaining delimiters in the suffix are preserved intact."""
    result = _text_after_nth("NDRI_TISSUE_SMHT001-3G-DESCEN_COLON", "_", 2)
    assert result is not None
    assert "-" in result
    assert "_" in result


# ============================================================================
# Test _extract_donor_tissue_prefix()
# ============================================================================


@pytest.mark.parametrize("external_id,expected", [
    ("SMHT001-3G-001D2", "SMHT001-3G"),
    ("SMHT001-3G-001", "SMHT001-3G"),
    ("ST001-3G-001", "ST001-3G"),
    ("SMHT001-3AT-001", "SMHT001-3AT"),
])
def test_extract_donor_tissue_prefix_returns_expected(external_id, expected):
    """Returns correct donor-tissue prefix."""
    assert _extract_donor_tissue_prefix(external_id) == expected


@pytest.mark.parametrize("external_id", [
    "SMHT001-3G",   # only one hyphen
    "SMHT001",      # no hyphens
    "",             # empty string
])
def test_extract_donor_tissue_prefix_returns_none(external_id):
    """Returns None for inputs with fewer than two hyphens."""
    assert _extract_donor_tissue_prefix(external_id) is None


def test_extract_donor_tissue_prefix_same_across_samples_same_tissue():
    """Two samples from the same tissue yield the same prefix."""
    assert _extract_donor_tissue_prefix("SMHT001-3G-001D2") == \
           _extract_donor_tissue_prefix("SMHT001-3G-002D1")


# ============================================================================
# Test _extract_donor_tissue_prefix_from_sample_source()
# ============================================================================


@pytest.mark.parametrize("sample_source,expected", [
    ("NDRI_TISSUE_SMHT001-3G-DESCEN_COLON", "SMHT001-3G"),
    ("NDRI_TISSUE_ST001-3G-DESCEN_COLON", "ST001-3G"),
    ("NDRI_TISSUE_SMHT001-3G-CAUD_CORTEX", "SMHT001-3G"),
    ("NDRI_TISSUE_SMHT001-3AT-DESCEN_COLON", "SMHT001-3AT"),
])
def test_extract_prefix_from_sample_source_returns_expected(sample_source, expected):
    """Returns correct donor-tissue prefix from tissue sample_source identifier."""
    assert _extract_donor_tissue_prefix_from_sample_source(sample_source) == expected


@pytest.mark.parametrize("sample_source", [
    "NDRI_TISSUE",           # too few underscores
    "NDRI_TISSUE_SMHT001",   # no hyphen in extracted segment
    "",                       # empty string
])
def test_extract_prefix_from_sample_source_returns_none(sample_source):
    """Returns None for unparseable inputs."""
    assert _extract_donor_tissue_prefix_from_sample_source(sample_source) is None


def test_extract_prefix_from_sample_source_matches_external_id_prefix():
    """Prefix from sample_source equals prefix from external_id for the same donor-tissue."""
    assert _extract_donor_tissue_prefix_from_sample_source(
        "NDRI_TISSUE_SMHT001-3G-DESCEN_COLON"
    ) == _extract_donor_tissue_prefix("SMHT001-3G-001D2")


# ============================================================================
# Test _note_validation_warning()
# ============================================================================


def test_note_validation_warning_logs_at_warning_level():
    """
    _note_validation_warning emits logging.WARNING — not an error —
    so structured_data.note_validation_error is never called.
    """
    mock_data = make_structured_data_mock({"TissueSample": []})
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _note_validation_warning(mock_data, "test warning message")
        mock_logger.warning.assert_called_once()
        call_args = " ".join(str(a) for a in mock_logger.warning.call_args[0])
        assert "test warning message" in call_args
    mock_data.note_validation_error.assert_not_called()


# ============================================================================
# Test _tissue_sample_external_id_in_submitted_id_validator()
# ============================================================================


def test_ext_id_in_submitted_id_no_schema_data():
    """Returns early when TissueSample key is absent from structured data."""
    mock_data = make_structured_data_mock({})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_empty_list():
    """No error for empty TissueSample list."""
    mock_data = make_structured_data_mock({"TissueSample": []})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_valid_ndri():
    """No error when external_id is a substring of NDRI submitted_id."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2", [],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_valid_benchmarking():
    """No error for valid NDRI benchmarking (ST) format."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_ST001-3G-001", "ST001-3G-001", [],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("submitted_id,external_id,description", [
    (
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT999-3G-001D2",
        "donor mismatch",
    ),
    (
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3Z-001D2",
        "tissue code mismatch",
    ),
    (
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "smht001-3g-001d2",
        "case mismatch — FIND is case-sensitive",
    ),
])
def test_ext_id_in_submitted_id_ndri_mismatch_produces_error(
    submitted_id, external_id, description
):
    """NDRI items with any external_id mismatch produce a blocking error."""
    tissue_sample = make_tissue_sample(submitted_id, external_id, [])
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()


def test_ext_id_in_submitted_id_error_contains_submitted_id():
    """Error message identifies the offending item by submitted_id."""
    submitted_id = "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2"
    tissue_sample = make_tissue_sample(submitted_id, "SMHT999-3G-001D2", [])
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert submitted_id in error_msg


def test_ext_id_in_submitted_id_error_contains_external_id_and_description():
    """Error message includes the problematic external_id and failure reason."""
    external_id = "SMHT999-3G-001D2"
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", external_id, []
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert external_id in error_msg
    assert "is not contained within submitted_id" in error_msg


@pytest.mark.parametrize("field_to_delete", ["submitted_id", "external_id"])
def test_ext_id_in_submitted_id_missing_required_field_skipped(field_to_delete):
    """Items missing submitted_id or external_id are silently skipped."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT999-3G-001D2", [],
    )
    del tissue_sample[field_to_delete]
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_mixed_batch():
    """Only the invalid NDRI item in a mixed NDRI batch produces an error."""
    valid_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2", [],
    )
    invalid_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D1", "SMHT999-3Z-001D1", [],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [valid_sample, invalid_sample]}
    )
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 1
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D1" in error_msg


def test_ext_id_in_submitted_id_multiple_invalid_items():
    """Each invalid NDRI item independently produces its own error."""
    samples = [
        make_tissue_sample(
            f"NDRI_TISSUE-SAMPLE_SMHT00{i}-3G-001D2", "SMHT999-3Z-001D2", []
        )
        for i in range(1, 4)
    ]
    mock_data = make_structured_data_mock({"TissueSample": samples})
    _tissue_sample_external_id_in_submitted_id_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 3


def test_ext_id_in_submitted_id_non_ndri_mismatch_is_warning_not_error():
    """Non-NDRI items with mismatch produce a warning, not a blocking error."""
    tissue_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT999-3G-001D2", [],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_in_submitted_id_validator(mock_data)
        mock_logger.warning.assert_called_once()
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_non_ndri_warning_message_content():
    """Warning message for non-NDRI items contains submitted_id and external_id."""
    submitted_id = "BWH_TISSUE-SAMPLE_SMHT001-3G-001D2"
    external_id = "SMHT999-3G-001D2"
    tissue_sample = make_tissue_sample(submitted_id, external_id, [])
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_in_submitted_id_validator(mock_data)
        call_args = " ".join(str(a) for a in mock_logger.warning.call_args[0])
        assert submitted_id in call_args
        assert external_id in call_args
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_non_ndri_valid_no_warning():
    """Non-NDRI items with matching external_id produce neither error nor warning."""
    tissue_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2", [],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_in_submitted_id_validator(mock_data)
        mock_logger.warning.assert_not_called()
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_in_submitted_id_mixed_batch_ndri_error_gcc_warning():
    """NDRI mismatch → error; GCC mismatch → warning in the same batch."""
    ndri_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT999-3G-001D2", [],
    )
    gcc_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D1", "SMHT999-3G-001D1", [],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [ndri_sample, gcc_sample]}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_in_submitted_id_validator(mock_data)
        mock_logger.warning.assert_called_once()
    mock_data.note_validation_error.assert_called_once()


# ============================================================================
# Test _tissue_sample_external_id_sample_source_consistency_validator()
# ============================================================================


def test_ext_id_sample_source_no_schema_data():
    """Returns early when TissueSample key is absent from structured data."""
    mock_data = make_structured_data_mock({})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_empty_list():
    """No error for empty TissueSample list."""
    mock_data = make_structured_data_mock({"TissueSample": []})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("submitted_id,external_id,sample_source", [
    (
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2",
        "SMHT001-3G-001D2",
        "NDRI_TISSUE_SMHT001-3G-DESCEN_COLON",
    ),
    (
        "NDRI_TISSUE-SAMPLE_ST001-3G-001",
        "ST001-3G-001",
        "NDRI_TISSUE_ST001-3G-DESCEN_COLON",
    ),
])
def test_ext_id_sample_source_valid_ndri(submitted_id, external_id, sample_source):
    """No error when external_id and sample_source share the donor-tissue prefix (NDRI)."""
    tissue_sample = make_tissue_sample(submitted_id, external_id, [sample_source])
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("external_id,sample_source,ext_prefix,src_prefix", [
    (
        "SMHT001-3G-001D2",
        "NDRI_TISSUE_SMHT999-3G-DESCEN_COLON",
        "'SMHT001-3G'",
        "'SMHT999-3G'",
    ),
    (
        "SMHT001-3G-001D2",
        "NDRI_TISSUE_SMHT001-3Z-DESCEN_COLON",
        "'SMHT001-3G'",
        "'SMHT001-3Z'",
    ),
])
def test_ext_id_sample_source_ndri_mismatch_produces_error(
    external_id, sample_source, ext_prefix, src_prefix
):
    """NDRI items with prefix mismatch produce a blocking error with informative message."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", external_id, [sample_source],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert ext_prefix in error_msg
    assert src_prefix in error_msg


def test_ext_id_sample_source_skips_non_production_prefix():
    """Skips items whose external_id is not a benchmarking or production prefix."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_OTHER001-3G-001", "OTHER001-3G-001",
        ["NDRI_TISSUE_SMHT001-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize("field_to_delete", ["submitted_id", "external_id", "sample_sources"])
def test_ext_id_sample_source_missing_required_field_skipped(field_to_delete):
    """Items missing submitted_id, external_id, or sample_sources are silently skipped."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    del tissue_sample[field_to_delete]
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_empty_sample_sources_skipped():
    """Items with an empty sample_sources list are silently skipped."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2", [],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_unparseable_sample_source_skipped():
    """Gracefully skips when sample_source cannot be parsed."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2", ["UNPARSEABLE"],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_unparseable_external_id_prefix_skipped():
    """Gracefully skips when external_id has insufficient hyphens for extraction."""
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001", "SMHT001",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_guard_skips_ndri_when_tissue_in_submission():
    """
    NDRI item is deferred to _tissue_sample_external_id_validator when
    the Tissue submitted_id is present in the same submission.
    """
    tissue_source_submitted_id = "NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        [tissue_source_submitted_id],
    )
    tissue = make_tissue(tissue_source_submitted_id, "SMHT999-3G")
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_guard_does_not_skip_ndri_tissue_not_in_submission():
    """
    NDRI item IS validated (and errors) when no matching Tissue is in the
    submission — guard only activates when Tissue is also present.
    """
    tissue_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    mock_data.note_validation_error.assert_called_once()


def test_ext_id_sample_source_error_message_content():
    """Error message includes submitted_id, both prefixes (repr), and sample_source."""
    submitted_id = "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2"
    sample_source = "NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"
    tissue_sample = make_tissue_sample(submitted_id, "SMHT001-3G-001D2", [sample_source])
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert submitted_id in error_msg
    assert "'SMHT001-3G'" in error_msg
    assert "'SMHT999-3G'" in error_msg
    assert sample_source in error_msg


def test_ext_id_sample_source_mixed_batch():
    """Only the invalid NDRI item in a mixed batch produces an error."""
    valid_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT001-3G-DESCEN_COLON"],
    )
    invalid_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D1", "SMHT001-3G-001D1",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [valid_sample, invalid_sample], "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 1
    error_msg = mock_data.note_validation_error.call_args[0][0]
    assert "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D1" in error_msg


def test_ext_id_sample_source_multiple_invalid_items():
    """Each invalid NDRI item independently produces its own error."""
    samples = [
        make_tissue_sample(
            f"NDRI_TISSUE-SAMPLE_SMHT00{i}-3G-001D2",
            f"SMHT00{i}-3G-001D2",
            ["NDRI_TISSUE_SMHT999-3Z-DESCEN_COLON"],
        )
        for i in range(1, 4)
    ]
    mock_data = make_structured_data_mock(
        {"TissueSample": samples, "Tissue": []}
    )
    _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
    assert mock_data.note_validation_error.call_count == 3


def test_ext_id_sample_source_non_ndri_mismatch_is_warning_not_error():
    """Non-NDRI items with prefix mismatch produce a warning, not a blocking error."""
    tissue_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
        mock_logger.warning.assert_called_once()
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_non_ndri_warning_message_content():
    """Warning message for non-NDRI items contains submitted_id and both prefixes."""
    submitted_id = "BWH_TISSUE-SAMPLE_SMHT001-3G-001D2"
    sample_source = "NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"
    tissue_sample = make_tissue_sample(submitted_id, "SMHT001-3G-001D2", [sample_source])
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
        call_args = " ".join(str(a) for a in mock_logger.warning.call_args[0])
        assert submitted_id in call_args
        assert "'SMHT001-3G'" in call_args
        assert "'SMHT999-3G'" in call_args
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_non_ndri_valid_no_warning():
    """Non-NDRI items with matching prefixes produce neither error nor warning."""
    tissue_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT001-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
        mock_logger.warning.assert_not_called()
    mock_data.note_validation_error.assert_not_called()


def test_ext_id_sample_source_mixed_batch_ndri_error_gcc_warning():
    """NDRI mismatch → error; GCC mismatch → warning in the same batch."""
    ndri_sample = make_tissue_sample(
        "NDRI_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    gcc_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D1", "SMHT001-3G-001D1",
        ["NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"],
    )
    mock_data = make_structured_data_mock(
        {"TissueSample": [ndri_sample, gcc_sample], "Tissue": []}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
        mock_logger.warning.assert_called_once()
    mock_data.note_validation_error.assert_called_once()


def test_ext_id_sample_source_guard_does_not_skip_gcc_with_tissue_in_submission():
    """
    GCC items are NOT guarded by the same-submission Tissue check.
    A mismatch produces a WARNING (not a blocking error) even when Tissue
    is present in the same submission.
    """
    tissue_source_submitted_id = "NDRI_TISSUE_SMHT999-3G-DESCEN_COLON"
    tissue_sample = make_tissue_sample(
        "DAC_TISSUE-SAMPLE_SMHT001-3G-001D2", "SMHT001-3G-001D2",
        [tissue_source_submitted_id],
    )
    tissue = make_tissue(tissue_source_submitted_id, "SMHT999-3G")
    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )
    with mock.patch(
        "submitr.validators.tissue_sample_validator._logger"
    ) as mock_logger:
        _tissue_sample_external_id_sample_source_consistency_validator(mock_data)
        mock_logger.warning.assert_called_once()
    mock_data.note_validation_error.assert_not_called()