import pytest
from unittest import mock
from typing import Dict, List

# Test Constants
NDRI_TISSUE_SUBMITTED_ID = "NDRI_TISSUE_SMHT001-3A-LUNG"
NDRI_TISSUE_SAMPLE_SUBMITTED_ID = "NDRI_TISSUE_SAMPLE_001"
GCC_TISSUE_SUBMITTED_ID = "DAC_TISSUE_SMHT001-3A-LUNG"
GCC_TISSUE_SAMPLE_SUBMITTED_ID = "DAC_TISSUE_SAMPLE_001"
BWH_TISSUE_SAMPLE_SUBMITTED_ID = "BWH_TISSUE_SAMPLE_001"

BENCHMARKING_EXTERNAL_ID = "ST001-3A-001"
PRODUCTION_EXTERNAL_ID = "SMHT001-3A-001"
NON_PRODUCTION_EXTERNAL_ID = "TEST001-3A-001"

MOCK_PORTAL_KEY = {
    "key": "test_key",
    "secret": "test_secret",
    "server": "http://localhost",
}

TISSUE_EXTERNAL_ID = "SMHT001-3A"
TISSUE_SAMPLE_EXTERNAL_ID = "SMHT001-3A-001"
TISSUE_UUID = "tissue-uuid-001"

NDRI_TPC_CENTER = {"display_title": "NDRI TPC", "uuid": "ndri-tpc-uuid"}
GCC_CENTER = {"display_title": "DAC", "uuid": "gcc-uuid"}
BWH_CENTER = {"display_title": "BWH", "uuid": "bwh-uuid"}


@pytest.fixture
def mock_portal_key():
    """Mock portal authentication key."""
    return MOCK_PORTAL_KEY


@pytest.fixture
def mock_structured_data():
    """Mock StructuredDataSet with minimal setup."""
    mock_data = mock.Mock()
    mock_data.data = {}
    mock_data.portal = mock.Mock()
    mock_data.portal.key = MOCK_PORTAL_KEY
    mock_data.note_validation_error = mock.Mock()
    return mock_data


@pytest.fixture
def sample_tissue_item():
    """Sample Tissue item for testing."""
    return {
        "submitted_id": NDRI_TISSUE_SUBMITTED_ID,
        "external_id": TISSUE_EXTERNAL_ID,
        "uuid": TISSUE_UUID,
    }


@pytest.fixture
def sample_tissue_sample_tpc():
    """Sample TissueSample from TPC."""
    return {
        "submitted_id": NDRI_TISSUE_SAMPLE_SUBMITTED_ID,
        "external_id": TISSUE_SAMPLE_EXTERNAL_ID,
        "sample_sources": [NDRI_TISSUE_SUBMITTED_ID],
        "category": "Specimen",
        "preservation_type": "Fresh",
        "submission_centers": [NDRI_TPC_CENTER],
        "uuid": "tpc-sample-uuid-001",
    }


@pytest.fixture
def sample_tissue_sample_gcc():
    """Sample TissueSample from GCC."""
    return {
        "submitted_id": GCC_TISSUE_SAMPLE_SUBMITTED_ID,
        "external_id": TISSUE_SAMPLE_EXTERNAL_ID,
        "sample_sources": [GCC_TISSUE_SUBMITTED_ID],
        "category": "Specimen",
        "preservation_type": "Fresh",
        "submission_centers": [GCC_CENTER],
        "uuid": "gcc-sample-uuid-001",
    }


@pytest.fixture
def mock_samples_cache():
    """Empty samples cache for testing caching behavior."""
    return {}


@pytest.fixture
def mock_tissue_cache():
    """Empty tissue cache for testing caching behavior."""
    return {}


def make_structured_data_mock(data_dict: Dict = None, portal_key: Dict = None):
    """
    Create a mock StructuredDataSet with specified data.

    Returns mock with:
    - .data dict (defaults to empty dict)
    - .portal.key (defaults to MOCK_PORTAL_KEY)
    - .note_validation_error() as Mock for call tracking
    """
    mock_structured_data = mock.Mock()
    mock_structured_data.data = data_dict if data_dict is not None else {}
    mock_structured_data.portal = mock.Mock()
    mock_structured_data.portal.key = portal_key or MOCK_PORTAL_KEY
    mock_structured_data.note_validation_error = mock.Mock()
    return mock_structured_data


def make_tissue_sample(
    submitted_id: str,
    external_id: str,
    sample_sources: List[str],
    category: str = "Specimen",
    preservation_type: str = "Fresh",
    submission_centers: List[Dict] = None,
    uuid: str = None,
) -> Dict:
    """Convenience function to create test TissueSample data."""
    return {
        "submitted_id": submitted_id,
        "external_id": external_id,
        "sample_sources": sample_sources,
        "category": category,
        "preservation_type": preservation_type,
        "submission_centers": submission_centers or [GCC_CENTER],
        "uuid": uuid or f"sample-uuid-{submitted_id}",
    }


def make_tissue(submitted_id: str, external_id: str, uuid: str = None) -> Dict:
    """Convenience function to create test Tissue data."""
    return {
        "submitted_id": submitted_id,
        "external_id": external_id,
        "uuid": uuid or f"tissue-uuid-{submitted_id}",
    }
