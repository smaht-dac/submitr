import pytest
from unittest.mock import Mock, patch
from dcicutils.structured_data import StructuredDataSet
from submitr.validators.tissue_validator import (
    _tissue_external_id_validator,
    _tissue_preservation_type_validator,
    _get_term_info,
)


@pytest.fixture
def mock_structured_data():
    """Create a mock StructuredDataSet object."""
    mock_data = Mock(spec=StructuredDataSet)
    mock_data.data = {}
    mock_data.note_validation_error = Mock()
    mock_data.portal = Mock()
    mock_data.portal.key = {"key": "test_key"}
    return mock_data


# Tests for _tissue_external_id_validator


def test_tissue_external_id_validator_no_tissue_data(mock_structured_data):
    """Test validator when no Tissue data exists."""
    mock_structured_data.data = {}
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_tissue_data_not_list(
        mock_structured_data):
    """Test validator when Tissue data is not a list."""
    mock_structured_data.data = {"Tissue": "not a list"}
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_tissue_without_donor(
        mock_structured_data):
    """Test validator when Tissue has no donor property."""
    mock_structured_data.data = {
        "Tissue": [{"submitted_id": "NDRI_001", "external_id": "EXT001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_tissue_without_submitted_id(
        mock_structured_data):
    """Test validator when Tissue has no submitted_id."""
    mock_structured_data.data = {
        "Tissue": [{"donor": "NDRI_DONOR001", "external_id": "EXT001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_matching_external_ids_ndri_tissue(
    mock_structured_data,
):
    """Test validator with matching external IDs for NDRI tissue."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "DONOR001-T1",
            }
        ],
        "Donor": [{"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_matching_external_ids_ndri_donor(
    mock_structured_data,
):
    """Test validator with matching external IDs for NDRI donor."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "OTHER_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "DONOR001-T1",
            }
        ],
        "Donor": [{"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_mismatched_external_ids_ndri_tissue(
    mock_structured_data,
):
    """Test validator with mismatched external IDs for NDRI tissue."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "WRONG001-T1",
            }
        ],
        "Donor": [{"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "NDRI_TISSUE001" in error_msg
    assert "WRONG001-T1" in error_msg
    assert "DONOR001" in error_msg


def test_tissue_external_id_validator_mismatched_external_ids_ndri_donor(
    mock_structured_data,
):
    """Test validator with mismatched external IDs for NDRI donor."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "OTHER_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "WRONG001-T1",
            }
        ],
        "Donor": [{"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()


def test_tissue_external_id_validator_non_ndri_submission_ignored(
        mock_structured_data):
    """Test validator ignores mismatches when neither is NDRI."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "OTHER_TISSUE001",
                "donor": "OTHER_DONOR001",
                "external_id": "WRONG001-T1",
            }
        ],
        "Donor": [{"submitted_id": "OTHER_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_donor_not_found(mock_structured_data):
    """Test validator when referenced donor is not found."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR999",
                "external_id": "EXT001-T1",
            }
        ],
        "Donor": [{"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"}]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_no_donor_data(mock_structured_data):
    """Test validator when Donor data is missing."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "EXT001-T1",
            }
        ]
    }
    _tissue_external_id_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_external_id_validator_multiple_tissues(mock_structured_data):
    """Test validator with multiple tissues, some valid, some invalid."""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "DONOR001-T1",  # Valid
            },
            {
                "submitted_id": "NDRI_TISSUE002",
                "donor": "NDRI_DONOR002",
                "external_id": "WRONG002-T1",  # Invalid
            },
            {
                "submitted_id": "OTHER_TISSUE003",
                "donor": "OTHER_DONOR003",
                "external_id": "WRONG003-T1",  # Ignored (not NDRI)
            },
        ],
        "Donor": [
            {"submitted_id": "NDRI_DONOR001", "external_id": "DONOR001"},
            {"submitted_id": "NDRI_DONOR002", "external_id": "DONOR002"},
            {"submitted_id": "OTHER_DONOR003", "external_id": "DONOR003"},
        ],
    }
    _tissue_external_id_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 1
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "NDRI_TISSUE002" in error_msg


def test_tissue_external_id_validator_donor_without_external_id(
        mock_structured_data):
    """Test validator when donor is missing external_id"""
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "NDRI_TISSUE001",
                "donor": "NDRI_DONOR001",
                "external_id": "EXT001-T1",
            }
        ],
        "Donor": [
            {
                "submitted_id": "NDRI_DONOR001"
                # Missing external_id
            }
        ],
    }
    _tissue_external_id_validator(mock_structured_data)
    # Should report error because external_id doesn't match None
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "NDRI_TISSUE001" in error_msg
    assert "None" in error_msg


# Tests for _get_term_info


@patch("submitr.validators.tissue_validator.ff_utils.search_metadata")
def test_get_term_info_success(mock_search):
    """Test _get_term_info with valid term."""
    mock_search.return_value = [
        {
            "identifier": "UBERON:0001234",
            "valid_protocol_ids": ["OCT_frozenTissue", "PAX_FFPE"],
        }
    ]
    mock_key = {"key": "test_key"}

    result = _get_term_info("UBERON:0001234", mock_key)

    assert result == {"OCT": "frozenTissue", "PAX": "FFPE"}
    mock_search.assert_called_once_with(
        "/search/?type=OntologyTerm&identifier=UBERON:0001234", mock_key
    )


@patch("submitr.validators.tissue_validator.ff_utils.search_metadata")
def test_get_term_info_no_results(mock_search):
    """Test _get_term_info when no term found."""
    mock_search.return_value = []
    mock_key = {"key": "test_key"}

    result = _get_term_info("UBERON:9999999", mock_key)

    assert result == {}


@patch("submitr.validators.tissue_validator.ff_utils.search_metadata")
def test_get_term_info_multiple_results(mock_search):
    """Test _get_term_info with multiple results (should handle first only)."""
    mock_search.return_value = [
        {"identifier": "UBERON:0001234", "valid_protocol_ids": ["OCT_frozenTissue"]},
        {"identifier": "UBERON:0001234", "valid_protocol_ids": ["PAX_FFPE"]},
    ]
    mock_key = {"key": "test_key"}

    result = _get_term_info("UBERON:0001234", mock_key)

    assert result == {}  # Multiple results, doesn't match len == 1 condition


@patch("submitr.validators.tissue_validator.ff_utils.search_metadata")
def test_get_term_info_no_valid_protocol_ids(mock_search):
    """Test _get_term_info when term has no valid_protocol_ids."""
    mock_search.return_value = [{"identifier": "UBERON:0001234"}]
    mock_key = {"key": "test_key"}

    result = _get_term_info("UBERON:0001234", mock_key)

    assert result == {}


@patch("submitr.validators.tissue_validator.ff_utils.search_metadata")
def test_get_term_info_protocol_without_underscore(mock_search):
    """Test _get_term_info with protocol ID without underscore."""
    mock_search.return_value = [
        {"identifier": "UBERON:0001234", "valid_protocol_ids": ["OCT", "PAX_FFPE"]}
    ]
    mock_key = {"key": "test_key"}

    result = _get_term_info("UBERON:0001234", mock_key)

    assert result == {"OCT": "", "PAX": "FFPE"}


# Tests for _tissue_preservation_type_validator


def test_tissue_preservation_type_validator_no_tissue_data(
        mock_structured_data):
    """Test validator when no Tissue data exists."""
    mock_structured_data.data = {}
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_preservation_type_validator_tissue_data_not_list(
        mock_structured_data):
    """Test validator when Tissue data is not a list."""
    mock_structured_data.data = {"Tissue": "not a list"}
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_tissue_preservation_type_validator_tissue_without_uberon_id(
    mock_structured_data,
):
    """Test validator when Tissue has no uberon_id."""
    mock_structured_data.data = {
        "Tissue": [
            {"submitted_id": "TEST_TISSUE001",
             "preservation_type": "frozenTissue"}
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_tissue_without_preservation_type(
    mock_get_term, mock_structured_data
):
    """Test validator when Tissue has no preservation_type."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_matching_preservation_type(
    mock_get_term, mock_structured_data
):
    """Test validator with matching preservation type."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "frozenTissue",
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_mismatched_preservation_type(
    mock_get_term, mock_structured_data
):
    """Test validator with mismatched preservation type."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "FFPE",
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "TEST_TISSUE001" in error_msg
    assert "FFPE" in error_msg
    assert "frozenTissue" in error_msg
    assert "OCT" in error_msg
    assert "UBERON:0001234" in error_msg


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_code_not_in_external_id(
    mock_get_term, mock_structured_data
):
    """Test validator when code is not in external_id."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "PAX-001",  # Different code
                "preservation_type": "FFPE",
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_empty_expected_preservation_type(
    mock_get_term, mock_structured_data
):
    """Test validator when expected preservation type is empty."""
    mock_get_term.return_value = {"OCT": ""}  # Empty preservation type
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "FFPE",
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_preservation_type_substring_match(
    mock_get_term, mock_structured_data
):
    """Test validator with preservation type as substring."""
    mock_get_term.return_value = {"OCT": "frozen"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "frozenTissue",  # Contains 'frozen'
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_multiple_tissues_mixed_validation(
    mock_get_term, mock_structured_data
):
    """Test validator with multiple tissues, some valid, some invalid."""
    mock_get_term.return_value = {"OCT": "frozenTissue", "PAX": "FFPE"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "frozenTissue",  # Valid
            },
            {
                "submitted_id": "TEST_TISSUE002",
                "uberon_id": "UBERON:0001234",
                "external_id": "PAX-002",
                "preservation_type": "frozenTissue",  # Invalid
            },
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 1
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "TEST_TISSUE002" in error_msg


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_term_info_caching(
    mock_get_term, mock_structured_data
):
    """Test that term info is cached for same uberon_id."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-001",
                "preservation_type": "frozenTissue",
            },
            {
                "submitted_id": "TEST_TISSUE002",
                "uberon_id": "UBERON:0001234",  # Same uberon_id
                "external_id": "OCT-002",
                "preservation_type": "frozenTissue",
            },
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    # Should only call _get_term_info once due to caching
    mock_get_term.assert_called_once()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_tissue_without_external_id(
    mock_get_term, mock_structured_data
):
    """Test validator when tissue has no external_id."""
    mock_get_term.return_value = {"OCT": "frozenTissue"}
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "preservation_type": "frozenTissue",
                # Missing external_id
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@patch("submitr.validators.tissue_validator._get_term_info")
def test_tissue_preservation_type_validator_multiple_codes_in_term_info(
    mock_get_term, mock_structured_data
):
    """Test validator with multiple protocol codes."""
    mock_get_term.return_value = {
        "OCT": "frozenTissue",
        "PAX": "FFPE",
        "RNA": "RNAlater",
    }
    mock_structured_data.data = {
        "Tissue": [
            {
                "submitted_id": "TEST_TISSUE001",
                "uberon_id": "UBERON:0001234",
                "external_id": "OCT-PAX-001",  # Contains multiple codes
                "preservation_type": "frozenTissue",  # Matches OCT but not PAX
            }
        ]
    }
    _tissue_preservation_type_validator(mock_structured_data)
    # error because PAX code in external_id but preservation_type not FFPE
    assert mock_structured_data.note_validation_error.call_count == 1
