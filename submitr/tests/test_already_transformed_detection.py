"""Tests for detecting and handling already-transformed workbooks."""

import os
import pytest
import tempfile
from unittest import mock
from dcicutils.portal_utils import Portal
from dcicutils.data_readers import Excel
from ..submission import (
    _workbook_appears_already_transformed,
    _prepare_protected_donor_transform,
)


def test_workbook_appears_already_transformed_with_protected_donor_sheet():
    """Test detection of already-transformed workbook with ProtectedDonor sheet."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.xlsx")
        with open(test_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission.Excel') as mock_excel_class:
            mock_excel = mock.MagicMock(spec=Excel)
            mock_excel.sheet_names = ["ProtectedDonor", "OtherSheet"]
            mock_excel_class.return_value = mock_excel
            
            result = _workbook_appears_already_transformed(test_file)
            assert result is True


def test_workbook_appears_already_transformed_with_prefixed_protected_donor_sheet():
    """Test detection of already-transformed workbook with prefixed ProtectedDonor sheet."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.xlsx")
        with open(test_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission.Excel') as mock_excel_class:
            mock_excel = mock.MagicMock(spec=Excel)
            mock_excel.sheet_names = ["01_ProtectedDonor", "01_Donor", "OtherSheet"]
            mock_excel_class.return_value = mock_excel
            
            result = _workbook_appears_already_transformed(test_file)
            assert result is True


def test_workbook_appears_already_transformed_without_protected_donor_sheet():
    """Test that workbooks without ProtectedDonor sheet are not detected as transformed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.xlsx")
        with open(test_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission.Excel') as mock_excel_class:
            mock_excel = mock.MagicMock(spec=Excel)
            mock_excel.sheet_names = ["Donor", "OtherSheet"]
            mock_excel_class.return_value = mock_excel
            
            result = _workbook_appears_already_transformed(test_file)
            assert result is False


def test_workbook_appears_already_transformed_non_excel():
    """Test that non-Excel files return False."""
    result = _workbook_appears_already_transformed("test.json")
    assert result is False


def test_already_transformed_interactive_mode_user_accepts():
    """Test that user can accept to skip transformation when workbook is already transformed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=True):
                with mock.patch('submitr.submission.yes_or_no', return_value=True):  # User says yes
                    with mock.patch('submitr.submission.PRINT'):
                        mock_portal = mock.MagicMock(spec=Portal)
                        
                        # Should return False (no transform) and None (no output path)
                        apply_transform, output_path = _prepare_protected_donor_transform(
                            portal=mock_portal,
                            ingestion_filename=input_file,
                            submission_centers=['ndri_tpc'],
                            validation=False,
                            no_query=False,
                            transform_protected_donor=True,
                            transformed_workbook_path=None,
                        )
                        
                        assert apply_transform is False
                        assert output_path is None


def test_already_transformed_interactive_mode_user_declines():
    """Test that process exits when user declines to use already-transformed workbook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=True):
                with mock.patch('submitr.submission.yes_or_no', return_value=False):  # User says no
                    with mock.patch('submitr.submission.PRINT'):
                        mock_portal = mock.MagicMock(spec=Portal)
                        
                        # Should exit with error
                        with pytest.raises(SystemExit) as excinfo:
                            _prepare_protected_donor_transform(
                                portal=mock_portal,
                                ingestion_filename=input_file,
                                submission_centers=['ndri_tpc'],
                                validation=False,
                                no_query=False,
                                transform_protected_donor=True,
                                transformed_workbook_path=None,
                            )
                        
                        assert excinfo.value.code == 1


def test_already_transformed_non_interactive_mode_exits_with_error():
    """Test that non-interactive mode exits with clear error for already-transformed workbook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=True):
                with mock.patch('submitr.submission.PRINT') as mock_print:
                    mock_portal = mock.MagicMock(spec=Portal)
                    
                    # Should exit with error in non-interactive mode
                    with pytest.raises(SystemExit) as excinfo:
                        _prepare_protected_donor_transform(
                            portal=mock_portal,
                            ingestion_filename=input_file,
                            submission_centers=['ndri_tpc'],
                            validation=False,
                            no_query=True,  # Non-interactive
                            transform_protected_donor=True,
                            transformed_workbook_path=None,
                        )
                    
                    assert excinfo.value.code == 1
                    
                    # Verify error messages are clear
                    messages = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
                    assert any('ERROR: Cannot proceed in non-interactive mode' in msg for msg in messages), \
                        f"Expected error about non-interactive mode not found in: {messages}"
                    assert any('--no-transform-protected-donor' in msg for msg in messages), \
                        f"Expected instruction to use --no-transform-protected-donor not found in: {messages}"


def test_already_transformed_validation_mode_messaging():
    """Test that validation mode shows appropriate messaging for already-transformed workbooks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=True):
                with mock.patch('submitr.submission.yes_or_no', return_value=True):
                    with mock.patch('submitr.submission.PRINT') as mock_print:
                        mock_portal = mock.MagicMock(spec=Portal)
                        
                        _prepare_protected_donor_transform(
                            portal=mock_portal,
                            ingestion_filename=input_file,
                            submission_centers=['ndri_tpc'],
                            validation=True,
                            no_query=False,
                            transform_protected_donor=True,
                            transformed_workbook_path=None,
                        )
                        
                        # Check that clear messaging is shown
                        messages = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
                        assert any('already been transformed' in msg for msg in messages), \
                            f"Expected message about already transformed not found in: {messages}"
                        assert any('Re-transforming' in msg and 'incorrect results' in msg for msg in messages), \
                            f"Expected warning about re-transforming not found in: {messages}"


def test_not_transformed_workbook_proceeds_normally():
    """Test that non-transformed workbooks proceed through normal flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            with mock.patch('submitr.submission.PRINT'):
                                mock_portal = mock.MagicMock(spec=Portal)
                                
                                # Should proceed normally through TPC transformation flow
                                apply_transform, output_path = _prepare_protected_donor_transform(
                                    portal=mock_portal,
                                    ingestion_filename=input_file,
                                    submission_centers=['ndri_tpc'],
                                    validation=False,
                                    no_query=True,
                                    transform_protected_donor=True,
                                    transformed_workbook_path=None,
                                )
                                
                                # Should apply transform for non-transformed workbook
                                assert apply_transform is True
                                assert output_path is not None
