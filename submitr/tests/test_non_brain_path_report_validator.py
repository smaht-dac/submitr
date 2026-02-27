import pytest
from unittest import mock

# Import validator functions being tested
from submitr.validators.non_brain_path_report_validator import (
    _non_brain_pathology_target_tissues_validator,
    _non_brain_pathology_non_target_tissues_validator,
    _non_brain_pathology_findings_validator,
)

# Import fixtures and helpers from datafixtures
from .datafixtures import make_structured_data_mock


# Test Constants
SCHEMA_NAME = "NonBrainPathologyReport"
SAMPLE_SUBMITTED_ID = "DAC_NON-BRAIN-PATHOLOGY-REPORT_001"


# ============================================================================
# Test  _non_brain_pathology_target_tissues_validator
# ============================================================================


def test_target_tissues_present_no_valid():
    """Valid case: present=No, percentage=0, autolysis_score absent."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Cortex",
                        "target_tissue_present": "No",
                        "target_tissue_percentage": "0",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_target_tissues_present_no_invalid_percentage():
    """Error: present=No but percentage is not 0."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Cortex",
                        "target_tissue_present": "No",
                        "target_tissue_percentage": "[0-10]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_percentage must be '0'" in error_msg
    assert "target_tissue_subtype: Cortex" in error_msg


def test_target_tissues_present_no_invalid_autolysis_score():
    """Error: present=No but autolysis_score is present."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Dermis",
                        "target_tissue_present": "No",
                        "target_tissue_percentage": "0",
                        "target_tissue_autolysis_score": 1,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_autolysis_score must be empty" in error_msg
    assert "target_tissue_subtype: Dermis" in error_msg


def test_target_tissues_present_yes_valid():
    """Valid case: present=Yes, percentage non-zero, autolysis_score present."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Liver",
                        "target_tissue_present": "Yes",
                        "target_tissue_percentage": "[50-100]",
                        "target_tissue_autolysis_score": 2,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_target_tissues_present_yes_invalid_percentage_zero():
    """Error: present=Yes but percentage is 0."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Lung",
                        "target_tissue_present": "Yes",
                        "target_tissue_percentage": "0",
                        "target_tissue_autolysis_score": 1,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_percentage cannot be '0'" in error_msg
    assert "target_tissue_subtype: Lung" in error_msg


def test_target_tissues_present_yes_missing_percentage():
    """Error: present=Yes but percentage is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Myocardium",
                        "target_tissue_present": "Yes",
                        "target_tissue_autolysis_score": 0,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_percentage must be provided" in error_msg
    assert "target_tissue_subtype: Myocardium" in error_msg


def test_target_tissues_present_yes_missing_autolysis_score():
    """Error: present=Yes but autolysis_score is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Epidermis",
                        "target_tissue_present": "Yes",
                        "target_tissue_percentage": "[26-49]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_autolysis_score must be provided" in error_msg
    assert "target_tissue_subtype: Epidermis" in error_msg


def test_target_tissues_multiple_errors():
    """Multiple errors should all be reported."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_subtype": "Cortex",
                        "target_tissue_present": "No",
                        "target_tissue_percentage": "[0-10]",
                        "target_tissue_autolysis_score": 1,
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 2


def test_target_tissues_missing_array():
    """No error when target_tissues array is missing."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID}]}
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_target_tissues_empty_array():
    """No error when target_tissues array is empty."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID, "target_tissues": []}]}
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_target_tissues_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_target_tissues_missing_subtype():
    """Uses 'unknown' when subtype is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "target_tissues": [
                    {
                        "target_tissue_present": "No",
                        "target_tissue_percentage": "[0-10]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_target_tissues_validator(mock_structured_data)
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "target_tissue_subtype: unknown" in error_msg


# ============================================================================
# Test _non_brain_pathology_non_target_tissues_validator
# ============================================================================


def test_non_target_tissues_present_yes_valid():
    """Valid case: present=Yes, percentage provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "non_target_tissues": [
                    {
                        "non_target_tissue_subtype": "Fibroadipose",
                        "non_target_tissue_present": "Yes",
                        "non_target_tissue_percentage": "[0-10]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_non_target_tissues_present_yes_missing_percentage():
    """Error: present=Yes but percentage is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "non_target_tissues": [
                    {
                        "non_target_tissue_subtype": "Lymphoid",
                        "non_target_tissue_present": "Yes",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "non_target_tissue_percentage must be provided" in error_msg
    assert "non_target_tissue_subtype: Lymphoid" in error_msg


def test_non_target_tissues_present_yes_empty_percentage():
    """Error: present=Yes but percentage is empty string."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "non_target_tissues": [
                    {
                        "non_target_tissue_subtype": "Other",
                        "non_target_tissue_present": "Yes",
                        "non_target_tissue_percentage": "",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "non_target_tissue_percentage must be provided" in error_msg


def test_non_target_tissues_present_no_valid():
    """Valid case: present=No, percentage absent."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "non_target_tissues": [
                    {
                        "non_target_tissue_subtype": "Epididymis",
                        "non_target_tissue_present": "No",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_non_target_tissues_present_no_invalid_percentage():
    """Error: present=No but percentage is provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "non_target_tissues": [
                    {
                        "non_target_tissue_subtype": "Rete testes",
                        "non_target_tissue_present": "No",
                        "non_target_tissue_percentage": "[11-25]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "non_target_tissue_percentage must be empty" in error_msg
    assert "non_target_tissue_subtype: Rete testes" in error_msg


def test_non_target_tissues_missing_array():
    """No error when non_target_tissues array is missing."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID}]}
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_non_target_tissues_empty_array():
    """No error when non_target_tissues array is empty."""
    data = {
        SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID, "non_target_tissues": []}]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_non_target_tissues_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _non_brain_pathology_non_target_tissues_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


# ============================================================================
# Test _non_brain_pathology_findings_validator
# ============================================================================


def test_pathologic_findings_present_yes_valid():
    """Valid case: present=Yes, description and percentage provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Inflammation",
                        "finding_present": "Yes",
                        "finding_description": "Mild inflammation observed",
                        "finding_percentage": "[0-10]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_pathologic_findings_present_yes_missing_description():
    """Error: present=Yes but description is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Necrosis",
                        "finding_present": "Yes",
                        "finding_percentage": "[11-25]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_description must be provided" in error_msg
    assert "finding_type: Necrosis" in error_msg


def test_pathologic_findings_present_yes_empty_description():
    """Error: present=Yes but description is empty string."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Metaplasia",
                        "finding_present": "Yes",
                        "finding_description": "",
                        "finding_percentage": "[26-49]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_description must be provided" in error_msg
    assert "finding_type: Metaplasia" in error_msg


def test_pathologic_findings_present_yes_whitespace_description():
    """Error: present=Yes but description is only whitespace."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Other",
                        "finding_present": "Yes",
                        "finding_description": "   ",
                        "finding_percentage": "[50-100]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_description must be provided" in error_msg


def test_pathologic_findings_present_yes_missing_percentage():
    """Error: present=Yes but percentage is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Neoplasia/Tumor/Carcinoma",
                        "finding_present": "Yes",
                        "finding_description": "Tumor detected",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_percentage must be provided" in error_msg
    assert "finding_type: Neoplasia/Tumor/Carcinoma" in error_msg


def test_pathologic_findings_present_yes_multiple_errors():
    """Multiple errors should all be reported."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Inflammation",
                        "finding_present": "Yes",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    assert mock_structured_data.note_validation_error.call_count == 2


def test_pathologic_findings_present_no_valid():
    """Valid case: present=No, percentage absent."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Necrosis",
                        "finding_present": "No",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_pathologic_findings_present_no_invalid_percentage():
    """Error: present=No but percentage is provided."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_type": "Metaplasia",
                        "finding_present": "No",
                        "finding_percentage": "[0-10]",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_called_once()
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_percentage must be empty" in error_msg
    assert "finding_type: Metaplasia" in error_msg


def test_pathologic_findings_missing_array():
    """No error when pathologic_findings array is missing."""
    data = {SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID}]}
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_pathologic_findings_empty_array():
    """No error when pathologic_findings array is empty."""
    data = {
        SCHEMA_NAME: [{"submitted_id": SAMPLE_SUBMITTED_ID, "pathologic_findings": []}]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_pathologic_findings_no_schema_data():
    """No error when schema data doesn't exist."""
    mock_structured_data = make_structured_data_mock({})
    _non_brain_pathology_findings_validator(mock_structured_data)
    mock_structured_data.note_validation_error.assert_not_called()


def test_pathologic_findings_missing_finding_type():
    """Uses 'unknown' when finding_type is missing."""
    data = {
        SCHEMA_NAME: [
            {
                "submitted_id": SAMPLE_SUBMITTED_ID,
                "pathologic_findings": [
                    {
                        "finding_present": "Yes",
                        "finding_description": "Something found",
                    }
                ],
            }
        ]
    }
    mock_structured_data = make_structured_data_mock(data)
    _non_brain_pathology_findings_validator(mock_structured_data)
    error_msg = mock_structured_data.note_validation_error.call_args[0][0]
    assert "finding_type: unknown" in error_msg
