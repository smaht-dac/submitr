"""Tests for ProtectedDonor transform functionality."""

import os
import pytest
import tempfile
from unittest import mock
from dcicutils.portal_utils import Portal
from ..submission import _prepare_protected_donor_transform


def test_protected_donor_transform_overwrites_existing_file():
    """Test that transformed workbook is auto-overwritten when it exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake input workbook
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx content")
        
        # Create a fake transformed workbook that should be overwritten
        transformed_file = os.path.join(tmpdir, "test.transformed.xlsx")
        with open(transformed_file, "wb") as f:
            f.write(b"old transformed content")
        
        original_mtime = os.path.getmtime(transformed_file)
        
        # Mock the necessary functions to isolate the overwrite behavior
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            with mock.patch('submitr.submission.PRINT'):
                                # Call with no_query=True to avoid interactive prompts
                                mock_portal = mock.MagicMock(spec=Portal)
                                apply_transform, output_path = _prepare_protected_donor_transform(
                                    portal=mock_portal,
                                    ingestion_filename=input_file,
                                    submission_centers=['ndri_tpc'],
                                    validation=False,
                                    no_query=True,
                                    transform_protected_donor=True,
                                    transformed_workbook_path=None,
                                )
                            
                            # Verify transform is applied and file was removed (to be recreated)
                            assert apply_transform is True
                            assert output_path == transformed_file
                            # File should have been removed (will be recreated by actual transform)
                            assert not os.path.exists(transformed_file)


def test_protected_donor_transform_overwrites_during_validation():
    """Test that transformed workbook is auto-overwritten during validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx content")
        
        transformed_file = os.path.join(tmpdir, "test.transformed.xlsx")
        with open(transformed_file, "wb") as f:
            f.write(b"old content")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            with mock.patch('submitr.submission.y_or_n', return_value=True):  # Mock user saying yes
                                with mock.patch('submitr.submission.PRINT'):
                                    mock_portal = mock.MagicMock(spec=Portal)
                                    # Call with validation=True
                                    apply_transform, output_path = _prepare_protected_donor_transform(
                                        portal=mock_portal,
                                        ingestion_filename=input_file,
                                        submission_centers=['ndri_tpc'],
                                        validation=True,
                                        no_query=False,  # Even with False, should auto-overwrite
                                        transform_protected_donor=True,
                                        transformed_workbook_path=None,
                                    )
                                
                                assert apply_transform is True
                                assert not os.path.exists(transformed_file)


def test_protected_donor_transform_message_for_validation():
    """Test that validation messaging includes both --submit and --no-transform-protected-donor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx content")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            with mock.patch('submitr.submission.PRINT') as mock_print:
                                mock_portal = mock.MagicMock(spec=Portal)
                                _prepare_protected_donor_transform(
                                    portal=mock_portal,
                                    ingestion_filename=input_file,
                                    submission_centers=['ndri_tpc'],
                                    validation=True,
                                    no_query=True,
                                    transform_protected_donor=True,
                                    transformed_workbook_path=None,
                                )
                            
                            # Check that messaging includes both --submit and --no-transform-protected-donor
                            # Extract the actual message strings from call arguments
                            messages = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
                            # Specifically check for the two expected messages
                            assert any('--submit' in msg and 'original workbook' in msg for msg in messages), \
                                f"Expected message about --submit not found in: {messages}"
                            assert any('--no-transform-protected-donor' in msg for msg in messages), \
                                f"Expected message about --no-transform-protected-donor not found in: {messages}"


def test_protected_donor_transform_message_for_submit():
    """Test that submit messaging includes --no-transform-protected-donor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx content")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            with mock.patch('submitr.submission.PRINT') as mock_print:
                                mock_portal = mock.MagicMock(spec=Portal)
                                _prepare_protected_donor_transform(
                                    portal=mock_portal,
                                    ingestion_filename=input_file,
                                    submission_centers=['ndri_tpc'],
                                    validation=False,
                                    no_query=True,
                                    transform_protected_donor=True,
                                    transformed_workbook_path=None,
                                )
                            
                            # Check that messaging includes --no-transform-protected-donor
                            messages = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
                            assert any('--no-transform-protected-donor' in msg for msg in messages), \
                                f"Expected message about --no-transform-protected-donor not found in: {messages}"


def test_protected_donor_transform_error_on_locked_file():
    """Test clean error exit when existing transformed workbook cannot be removed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "test.xlsx")
        with open(input_file, "wb") as f:
            f.write(b"fake xlsx content")
        
        transformed_file = os.path.join(tmpdir, "test.transformed.xlsx")
        with open(transformed_file, "wb") as f:
            f.write(b"old content")
        
        with mock.patch('submitr.submission._is_excel_workbook', return_value=True):
            with mock.patch('submitr.submission._workbook_appears_already_transformed', return_value=False):
                with mock.patch('submitr.submission._workbook_has_visible_donor_sheet', return_value=True):
                    with mock.patch('submitr.submission._resolve_submission_center_identifiers', return_value=['ndri_tpc']):
                        with mock.patch('submitr.submission._is_tpc_submission_center_identifiers', return_value=True):
                            # Mock os.remove to raise PermissionError
                            with mock.patch('submitr.submission.os.remove', side_effect=PermissionError("Permission denied")):
                                with mock.patch('submitr.submission.PRINT') as mock_print:
                                    mock_portal = mock.MagicMock(spec=Portal)
                                    # Should exit with sys.exit(1)
                                    with pytest.raises(SystemExit) as excinfo:
                                        _prepare_protected_donor_transform(
                                            portal=mock_portal,
                                            ingestion_filename=input_file,
                                            submission_centers=['ndri_tpc'],
                                            validation=False,
                                            no_query=True,
                                            transform_protected_donor=True,
                                            transformed_workbook_path=None,
                                        )
                                
                                # Verify exit code is 1
                                assert excinfo.value.code == 1
                                
                                # Verify error messages are clear and helpful
                                messages = [call[0][0] if call[0] else '' for call in mock_print.call_args_list]
                                assert any('ERROR: Cannot overwrite' in msg for msg in messages), \
                                    f"Expected error message about overwrite failure not found in: {messages}"
                                assert any('locked, read-only, or protected' in msg for msg in messages), \
                                    f"Expected message about file being locked/protected not found in: {messages}"
                                assert any('Permission denied' in msg for msg in messages), \
                                    f"Expected permission denied details not found in: {messages}"
