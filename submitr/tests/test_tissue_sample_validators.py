from unittest import mock

# Import all validator functions being tested
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
)

# Import fixtures and helpers from datafixtures
from .datafixtures import (
    # Constants
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
    # Helper functions
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


def test_categorize_by_submitted_id_prefix():
    """Falls back to submitted_id when submission_centers missing."""
    samples = [
        {"submitted_id": "NDRI_SAMPLE_001", "submission_centers": []},
        {"submitted_id": "DAC_SAMPLE_002", "submission_centers": []},
    ]
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 1
    assert len(gcc) == 1
    assert tpc[0]["submitted_id"] == "NDRI_SAMPLE_001"
    assert gcc[0]["submitted_id"] == "DAC_SAMPLE_002"


def test_categorize_empty_list():
    """Returns two empty lists."""
    tpc, gcc = _categorize_samples_by_submission_center([])
    assert tpc == []
    assert gcc == []


def test_categorize_missing_submission_centers():
    """Uses submitted_id prefix as fallback."""
    samples = [{"submitted_id": "NDRI_SAMPLE_001"}, {"submitted_id": "DAC_SAMPLE_002"}]
    tpc, gcc = _categorize_samples_by_submission_center(samples)
    assert len(tpc) == 1
    assert len(gcc) == 1


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


def test_get_tissue_submitted_id_cache_miss_success():
    """Fetches from portal and caches."""
    cache = {}
    tissue_data = {"uuid": TISSUE_UUID, "submitted_id": NDRI_TISSUE_SUBMITTED_ID}
    with mock.patch(
        ("submitr.validators.tissue_sample_validator"
         ".portal_utils.get_item_by_identifier"),
        return_value=tissue_data,
    ) as mock_get_item:
        with mock.patch(
            ("submitr.validators.tissue_sample_validator"
             ".item_utils.get_submitted_id"),
            return_value=NDRI_TISSUE_SUBMITTED_ID,
        ):
            result = _get_tissue_submitted_id(
                TISSUE_UUID, cache, MOCK_PORTAL_KEY)

            assert result == NDRI_TISSUE_SUBMITTED_ID
            assert cache[TISSUE_UUID] == NDRI_TISSUE_SUBMITTED_ID
            mock_get_item.assert_called_once_with(TISSUE_UUID, MOCK_PORTAL_KEY)


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


def test_get_tissue_samples_caches_result():
    """Verify result is added to cache."""
    cache = {}
    sample_data = [{"data": "test"}]

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=sample_data,
    ):
        _get_or_fetch_tissue_samples(
            PRODUCTION_EXTERNAL_ID, cache, MOCK_PORTAL_KEY)

        assert PRODUCTION_EXTERNAL_ID in cache
        assert cache[PRODUCTION_EXTERNAL_ID] == sample_data


def test_get_tissue_samples_caches_none():
    """Verify None result is cached."""
    cache = {}

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=None,
    ):
        result = _get_or_fetch_tissue_samples(
            PRODUCTION_EXTERNAL_ID, cache, MOCK_PORTAL_KEY
        )

        assert result is None
        assert PRODUCTION_EXTERNAL_ID in cache
        assert cache[PRODUCTION_EXTERNAL_ID] is None


# ============================================================================
# Test _get_tissue_submitted_id()
# ============================================================================


def test_get_tissue_submitted_id_cache_hit():
    """Returns cached submitted_id."""
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


def test_get_tissue_submitted_id_caches_result():
    """Verify submitted_id cached."""
    cache = {}
    tissue_data = {"uuid": TISSUE_UUID}

    with mock.patch(
        "submitr.validators.utils.portal.get_item_by_identifier",
        return_value=tissue_data,
    ):
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id",
            return_value=NDRI_TISSUE_SUBMITTED_ID,
        ):
            _get_tissue_submitted_id(TISSUE_UUID, cache, MOCK_PORTAL_KEY)

            assert TISSUE_UUID in cache
            assert cache[TISSUE_UUID] == NDRI_TISSUE_SUBMITTED_ID


def test_get_tissue_submitted_id_caches_none():
    """Verify None result is cached."""
    cache = {}

    with mock.patch(
        "submitr.validators.utils.portal.get_item_by_identifier", return_value=None
    ):
        result = _get_tissue_submitted_id(TISSUE_UUID, cache, MOCK_PORTAL_KEY)

        assert result is None
        assert TISSUE_UUID in cache
        assert cache[TISSUE_UUID] is None


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
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID, existing_tpc, mock_data
    )

    mock_data.note_validation_error.assert_not_called()


def test_validate_tpc_duplicate_different_item():
    """Error when different TPC sample exists."""
    mock_data = make_structured_data_mock()
    existing_tpc = [{"submitted_id": "NDRI_OTHER_SAMPLE"}]

    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID, existing_tpc, mock_data
    )

    expected_message = f"TissueSample: TPC Tissue Sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_tpc_duplicate_multiple_existing():
    """Error when multiple TPC samples exist."""
    mock_data = make_structured_data_mock()
    existing_tpc = [
        {"submitted_id": "NDRI_SAMPLE_001"},
        {"submitted_id": "NDRI_SAMPLE_002"},
    ]

    _validate_tpc_duplicate(
        PRODUCTION_EXTERNAL_ID, NDRI_TISSUE_SAMPLE_SUBMITTED_ID, existing_tpc, mock_data
    )

    expected_message = f"TissueSample: TPC Tissue Sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
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
    expected_message = f"TissueSample: No TPC Tissue Sample found with external_id {PRODUCTION_EXTERNAL_ID}"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_gcc_baseline_multiple_tpc():
    """Returns True when multiple TPC samples."""
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
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID, [], seen, mock_data
    )

    assert result is True
    mock_data.note_validation_error.assert_not_called()


def test_validate_gcc_duplicate_same_item_update():
    """Returns True when updating same item."""
    mock_data = make_structured_data_mock()
    seen = {}
    existing_gcc = [{"submitted_id": GCC_TISSUE_SAMPLE_SUBMITTED_ID}]

    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID,
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc,
        seen,
        mock_data,
    )

    assert result is True
    mock_data.note_validation_error.assert_not_called()


def test_validate_gcc_duplicate_different_item_in_portal():
    """Returns False when different GCC sample exists in portal."""
    mock_data = make_structured_data_mock()
    seen = {}
    existing_gcc = [{"submitted_id": "DAC_OTHER_SAMPLE"}]

    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID,
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc,
        seen,
        mock_data,
    )

    assert result is False
    expected_message = f"TissueSample: A non-TPC sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_gcc_duplicate_different_item_in_batch():
    """Returns False when different GCC sample in current batch."""
    mock_data = make_structured_data_mock()
    seen = {PRODUCTION_EXTERNAL_ID: "DAC_OTHER_SAMPLE"}

    result = _validate_gcc_duplicate(
        PRODUCTION_EXTERNAL_ID, GCC_TISSUE_SAMPLE_SUBMITTED_ID, [], seen, mock_data
    )

    assert result is False
    expected_message = f"TissueSample: A non-TPC sample with external_id {PRODUCTION_EXTERNAL_ID} already exists in this submission"
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
        PRODUCTION_EXTERNAL_ID,
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        existing_gcc,
        seen,
        mock_data,
    )

    assert result is False
    expected_message = f"TissueSample: A non-TPC sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


# ============================================================================
# Test _validate_metadata_consistency()
# ============================================================================


def test_validate_metadata_consistency_all_match():
    """No errors when all metadata matches."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
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
                _validate_metadata_consistency(
                    gcc_item, tpc_item, mock_data, tissue_cache
                )

    mock_data.note_validation_error.assert_not_called()


def test_validate_metadata_consistency_category_mismatch():
    """Error on category mismatch."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Homogenate",
        preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
    )

    # Use side_effect to handle multiple calls
    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id"
    ) as mock_get_submitted:
        mock_get_submitted.return_value = NDRI_TISSUE_SAMPLE_SUBMITTED_ID
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            mock_get_item.return_value = {"submitted_id": GCC_TISSUE_SUBMITTED_ID}
            _validate_metadata_consistency(gcc_item, tpc_item, mock_data, tissue_cache)

    expected_message = f"TissueSample: metadata mismatch, category Homogenate does not match value Specimen in TPC Tissue Sample {NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_metadata_consistency_preservation_type_mismatch():
    """Error on preservation_type mismatch."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Frozen",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
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

    expected_message = f"TissueSample: metadata mismatch, preservation_type Frozen does not match value Fresh in TPC Tissue Sample {NDRI_TISSUE_SAMPLE_SUBMITTED_ID}"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_validate_metadata_consistency_both_mismatch():
    """Multiple errors for multiple mismatches."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Homogenate",
        preservation_type="Frozen",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
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
                _validate_metadata_consistency(
                    gcc_item, tpc_item, mock_data, tissue_cache
                )

    # Should have two error calls - one for category, one for preservation_type
    assert mock_data.note_validation_error.call_count == 2

    # Check both error messages were logged
    calls = [call[0][0] for call in mock_data.note_validation_error.call_args_list]
    assert any(
        "category Homogenate does not match value Specimen" in call for call in calls
    )
    assert any(
        "preservation_type Frozen does not match value Fresh" in call for call in calls
    )


def test_validate_metadata_consistency_sample_source_mismatch():
    """Error when sample_sources don't match."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        ["DAC_TISSUE_DIFFERENT"],
        category="Specimen",
        preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
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

                def get_submitted_side_effect(item):
                    return item.get("submitted_id")

                mock_get_submitted.side_effect = get_submitted_side_effect

                _validate_metadata_consistency(
                    gcc_item, tpc_item, mock_data, tissue_cache
                )

    expected_message = f"TissueSample: metadata mismatch: sample_source DAC_TISSUE_DIFFERENT does not match TPC TissueSample sample_source {NDRI_TISSUE_SUBMITTED_ID}"
    mock_data.note_validation_error.assert_called_with(expected_message)


def test_validate_metadata_consistency_missing_values():
    """No error when values are None/missing."""
    mock_data = make_structured_data_mock()
    tissue_cache = {}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Fresh",
    )
    # Remove category from gcc_item
    gcc_item["category"] = None

    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
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
                _validate_metadata_consistency(
                    gcc_item, tpc_item, mock_data, tissue_cache
                )

    # Should not error when GCC value is None
    mock_data.note_validation_error.assert_not_called()


def test_validate_metadata_consistency_uses_tissue_cache():
    """Verifies caching behavior for tissue lookups."""
    mock_data = make_structured_data_mock()
    tissue_cache = {TISSUE_UUID: NDRI_TISSUE_SUBMITTED_ID}

    gcc_item = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Fresh",
    )
    tpc_item = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
    )

    with mock.patch(
        "submitr.validators.utils.item.get_submitted_id",
        return_value=NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
    ):
        with mock.patch(
            "submitr.validators.utils.portal.get_item_by_identifier"
        ) as mock_get_item:
            # Should not be called since UUID is in cache
            with mock.patch(
                "submitr.validators.utils.item.get_submitted_id",
                return_value=GCC_TISSUE_SUBMITTED_ID,
            ):
                _validate_metadata_consistency(
                    gcc_item, tpc_item, mock_data, tissue_cache
                )

            # Verify cache was used (tissue lookup not called for cached UUID)
            # Only called for GCC tissue, not the cached TPC tissue
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        TISSUE_SAMPLE_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        "SMHT001-3A-001",
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )

    _tissue_sample_external_id_validator(mock_data)

    expected_message = (
        f"TissueSample: item {NDRI_TISSUE_SAMPLE_SUBMITTED_ID} "
        f"external_id SMHT001-3A-001 does not match Tissue external_id SMHT999-3A."
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_external_id_validator_mismatch_tpc_tissue():
    """Error when TPC Tissue linked from non-TPC TissueSample."""
    tissue = make_tissue(NDRI_TISSUE_SUBMITTED_ID, "SMHT999-3A")
    tissue_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        "SMHT001-3A-001",
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )

    _tissue_sample_external_id_validator(mock_data)

    expected_message = (
        f"TissueSample: item {GCC_TISSUE_SAMPLE_SUBMITTED_ID} "
        f"external_id SMHT001-3A-001 does not match Tissue external_id SMHT999-3A."
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_external_id_validator_non_tpc_submission():
    """No validation when neither is TPC."""
    tissue = make_tissue(GCC_TISSUE_SUBMITTED_ID, "SMHT999-3A")
    tissue_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        "SMHT001-3A-001",
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": [tissue]}
    )

    _tissue_sample_external_id_validator(mock_data)

    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_tissue_not_in_data():
    """Handles missing Tissue gracefully."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        TISSUE_SAMPLE_EXTERNAL_ID,
        ["NONEXISTENT_TISSUE"],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock(
        {"TissueSample": [tissue_sample], "Tissue": []}
    )

    _tissue_sample_external_id_validator(mock_data)

    mock_data.note_validation_error.assert_not_called()


def test_external_id_validator_no_submitted_id():
    """Skips items without submitted_id."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        TISSUE_SAMPLE_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
    )
    del sample_no_submitted_id["submitted_id"]

    sample_no_external_id = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        NON_PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})

    _tissue_sample_metadata_validator(mock_data)

    mock_data.note_validation_error.assert_not_called()


def test_metadata_validator_tpc_new_submission():
    """Allows new TPC sample."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
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
        "NDRI_OTHER_SAMPLE",
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[existing_tpc],
    ):
        _tissue_sample_metadata_validator(mock_data)

    expected_message = f"TissueSample: TPC Tissue Sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_new_with_tpc_baseline():
    """Allows new GCC when TPC exists with matching metadata."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[NDRI_TPC_CENTER],
    )

    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[GCC_CENTER],
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],  # Make sure this is dict format
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[NDRI_TPC_CENTER],
    )
    existing_gcc = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": "gcc-tissue-uuid"}],  # Make sure this is dict format
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[GCC_CENTER],
    )

    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[GCC_CENTER],
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
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ):
        _tissue_sample_metadata_validator(mock_data)

    expected_message = f"TissueSample: No TPC Tissue Sample found with external_id {PRODUCTION_EXTERNAL_ID}"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_duplicate():
    """Rejects duplicate GCC submission."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )
    existing_gcc = make_tissue_sample(
        "DAC_OTHER_SAMPLE",
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample, existing_gcc],
    ):
        _tissue_sample_metadata_validator(mock_data)

    expected_message = f"TissueSample: A non-TPC sample with external_id {PRODUCTION_EXTERNAL_ID} already exists"
    mock_data.note_validation_error.assert_called_once_with(expected_message)


def test_metadata_validator_gcc_metadata_mismatch():
    """Rejects GCC when metadata doesn't match TPC."""
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[NDRI_TPC_CENTER],
    )

    gcc_sample = make_tissue_sample(
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        category="Homogenate",
        preservation_type="Fresh",
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [gcc_sample]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample],
    ):
        with mock.patch(
            "submitr.validators.utils.item.get_submitted_id"
        ) as mock_get_submitted:
            # Return different values based on what dict is passed in
            def get_submitted_side_effect(item):
                return item.get("submitted_id")

            mock_get_submitted.side_effect = get_submitted_side_effect

            with mock.patch(
                "submitr.validators.utils.portal.get_item_by_identifier"
            ) as mock_get_item:
                # Return tissue object when TISSUE_UUID is requested
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
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )
    sample2 = make_tissue_sample(
        "NDRI_SAMPLE_002",
        BENCHMARKING_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
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
        GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )
    sample2 = make_tissue_sample(
        "DAC_DIFFERENT_SAMPLE",
        PRODUCTION_EXTERNAL_ID,
        [GCC_TISSUE_SUBMITTED_ID],
        submission_centers=[GCC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [sample1, sample2]})

    # Mock portal to return TPC sample with proper dict format for sample_sources
    tpc_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [{"uuid": TISSUE_UUID}],
        category="Specimen",
        preservation_type="Fresh",
        submission_centers=[NDRI_TPC_CENTER],
    )

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[tpc_sample],
    ):
        _tissue_sample_metadata_validator(mock_data)

    # Should be called once for the intra-batch duplicate
    expected_message = f"TissueSample: A sample with external_id {PRODUCTION_EXTERNAL_ID} already exists in this submission"
    assert mock_data.note_validation_error.call_count == 1
    mock_data.note_validation_error.assert_called_with(expected_message)


def test_metadata_validator_caching_behavior():
    """Verifies portal queries are cached."""
    sample1 = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )
    sample2 = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [sample1, sample2]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=[],
    ) as mock_search:
        _tissue_sample_metadata_validator(mock_data)

        # Should only query portal once due to caching
        assert mock_search.call_count == 1


def test_metadata_validator_portal_query_failure():
    """Handles portal query failure gracefully."""
    tissue_sample = make_tissue_sample(
        NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        PRODUCTION_EXTERNAL_ID,
        [NDRI_TISSUE_SUBMITTED_ID],
        submission_centers=[NDRI_TPC_CENTER],
    )

    mock_data = make_structured_data_mock({"TissueSample": [tissue_sample]})

    with mock.patch(
        "submitr.validators.utils.portal.search_tissue_samples_by_external_id",
        return_value=None,
    ):
        _tissue_sample_metadata_validator(mock_data)

    expected_message = (
        f"TissueSample: Unable to validate {NDRI_TISSUE_SAMPLE_SUBMITTED_ID} - "
        f"portal query failed for external_id {PRODUCTION_EXTERNAL_ID}"
    )
    mock_data.note_validation_error.assert_called_once_with(expected_message)
