import pytest
from unittest import mock

from submitr.validators.brain_path_report_validator import (
    _brain_pathology_neuropathology_present_validator,
    _brain_pathology_subregions_validator,
    _brain_pathology_age_related_staining_validator,
)

from .datafixtures import make_structured_data_mock

SCHEMA_NAME = "BrainPathologyReport"
SAMPLE_SUBMITTED_ID = "DAC_BRAIN-PATHOLOGY-REPORT_001"


# ============================================================================
# Test _brain_pathology_neuropathology_present_validator
# ============================================================================


def test_neuropathology_present_yes_with_description_valid():
    """Valid case: present=Yes with description provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "developmental_neuropathology_present": "Yes",
                "developmental_neuropathology_description": "Some developmental finding",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_neuropathology_present_no_without_description_valid():
    """Valid case: present=No without description."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "developmental_neuropathology_present": "No",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_neuropathology_present_yes_missing_description():
    """Error: present=Yes but description is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "infectious_neuropathology_present": "Yes",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "infectious_neuropathology_present" in error_msg
    assert "infectious_neuropathology_description must be provided" in error_msg


def test_neuropathology_present_yes_empty_description():
    """Error: present=Yes but description is empty string."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "inflammatory_neuropathology_present": "Yes",
                "inflammatory_neuropathology_description": "",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "inflammatory_neuropathology_description must be provided" in error_msg


def test_neuropathology_present_yes_whitespace_description():
    """Error: present=Yes but description is only whitespace."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "neoplastic_neuropathology_present": "Yes",
                "neoplastic_neuropathology_description": "   ",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "neoplastic_neuropathology_description must be provided" in error_msg


def test_neuropathology_multiple_present_fields_all_valid():
    """Valid case: multiple present=Yes fields all with descriptions."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "vascular_neuropathology_present": "Yes",
                "vascular_neuropathology_description": "Some vascular finding",
                "artifacts_present": "Yes",
                "artifacts_description": "Freeze artifact noted",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_neuropathology_multiple_present_fields_multiple_errors():
    """Multiple errors reported when multiple present=Yes fields lack descriptions."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "tbi_neuropathology_present": "Yes",
                "neurodegenerative_neuropathology_present": "Yes",
                "metabolic_neuropathology_present": "Yes",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 3


def test_neuropathology_other_pathology_present_yes_missing_description():
    """Error: other_pathology_present=Yes but description missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "other_pathology_present": "Yes",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "other_pathology_description must be provided" in error_msg


def test_neuropathology_no_present_fields():
    """No error when no _present fields exist in item."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "tissue_name": "Brain",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_neuropathology_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _brain_pathology_neuropathology_present_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


# ============================================================================
# Test _brain_pathology_subregions_validator
# ============================================================================


def test_subregions_present_yes_with_autolysis_valid():
    """Valid case: is_present=Yes with tissue_autolysis_score provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "subregion": "Cerebellum Left Hemisphere",
                        "is_present": "Yes",
                        "tissue_autolysis_score": 1,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_subregions_present_no_without_autolysis_valid():
    """Valid case: is_present=No with no tissue_autolysis_score."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "subregion": "Frontal Lobe Left Hemisphere",
                        "is_present": "No",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_subregions_present_yes_missing_autolysis():
    """Error: is_present=Yes but tissue_autolysis_score is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "subregion": "Hippocampus Left Hemisphere",
                        "is_present": "Yes",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "tissue_autolysis_score must be provided" in error_msg
    assert "subregion: Hippocampus Left Hemisphere" in error_msg


def test_subregions_present_no_with_autolysis():
    """Error: is_present=No but tissue_autolysis_score is present."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "subregion": "Hippocampus Right Hemisphere",
                        "is_present": "No",
                        "tissue_autolysis_score": 2,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "tissue_autolysis_score must be absent" in error_msg
    assert "subregion: Hippocampus Right Hemisphere" in error_msg


def test_subregions_multiple_errors():
    """Multiple errors reported across multiple subregions."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "subregion": "Cerebellum Left Hemisphere",
                        "is_present": "Yes",
                        # missing autolysis_score
                    },
                    {
                        "subregion": "Frontal Lobe Left Hemisphere",
                        "is_present": "No",
                        "tissue_autolysis_score": 1,  # should be absent
                    },
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 2


def test_subregions_missing_array():
    """No error when brain_subregions array is missing."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID}]}
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_subregions_empty_array():
    """No error when brain_subregions array is empty."""
    data = {
        SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID, "brain_subregions": []}]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_subregions_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _brain_pathology_subregions_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_subregions_missing_subregion_name():
    """Uses 'unknown' when subregion name is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "brain_subregions": [
                    {
                        "is_present": "Yes",
                        # missing subregion name
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_subregions_validator(mock_structured_data)
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "subregion: unknown" in error_msg


# ============================================================================
# Test _brain_pathology_age_related_staining_validator
# ============================================================================


def test_age_related_staining_yes_no_fields():
    """Error: staining=Yes but no age-related staining fields populated."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "additional_age-related_staining_performed": "Yes",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "additional_age-related_staining_performed" in error_msg
    assert "at least one" in error_msg


def test_age_related_staining_yes_with_multiple_fields_valid():
    """Valid case: staining=Yes with multiple fields provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "additional_age-related_staining_performed": "Yes",
                "abc_score_A": 1,
                "abc_score_B": 2,
                "braak_pd": 3,
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_age_related_staining_no_no_validation():
    """No error when staining=No."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "additional_age-related_staining_performed": "No",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_age_related_staining_field_absent_no_validation():
    """No error when additional_age-related_staining_performed is not present."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID}]}
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_age_related_staining_final_diagnosis_excluded():
    """Error: staining=Yes but only final_neuropathological_diagnosis is populated."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "additional_age-related_staining_performed": "Yes",
                "final_neuropathological_diagnosis": "Some diagnosis",
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()


def test_age_related_staining_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("abc_score_A", 1),
        ("abc_score_B", 2),
        ("abc_score_C", 3),
        ("cerad_score", 50),
        ("ad_neuropathologic_change_level", "Low"),
        ("braak_pd", 3),
        ("small_vessel_disease", "Mild"),
        ("braak_and_braak_ad", "III"),
        ("thal", 2),
        ("caa_vonsattel", 1),
        ("mckeith", 2),
        ("vonsattel_hd", 1),
    ],
)
def test_age_related_staining_each_field_individually_sufficient(field, value):
    """Each individual age-related staining field is sufficient on its own."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "additional_age-related_staining_performed": "Yes",
                field: value,
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _brain_pathology_age_related_staining_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()