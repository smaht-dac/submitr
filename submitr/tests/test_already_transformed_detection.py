"""Tests for analysis-based already-transformed detection."""

from ..submission import (
    _analyze_protected_donor_workbook,
    _workbook_appears_already_transformed,
)
from .test_protected_donor_transform import make_workbook


def test_valid_fully_transformed_workbook_is_detected(tmp_path):
    path = make_workbook(
        tmp_path / "transformed.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        protected_rows=[["D_PROTECTED-DONOR_1", "one", "in review"]],
        references={"Demographic": ["D_PROTECTED-DONOR_1"]},
    )
    assert _workbook_appears_already_transformed(path) is True


def test_partially_transformed_workbook_is_not_treated_as_complete(tmp_path):
    path = make_workbook(
        tmp_path / "partial.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"], ["D_DONOR_2", "two", "active"]],
        protected_rows=[["D_PROTECTED-DONOR_2", "two", "in review"]],
        references={"Demographic": ["D_DONOR_1", "D_PROTECTED-DONOR_2"]},
    )
    analysis = _analyze_protected_donor_workbook(path, None)
    assert analysis.needs_transformation
    assert _workbook_appears_already_transformed(path) is False


def test_invalid_workbook_is_not_treated_as_complete(tmp_path):
    path = make_workbook(
        tmp_path / "invalid.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        references={"Demographic": ["bad-reference"]},
    )
    analysis = _analyze_protected_donor_workbook(path, None)
    assert analysis.invalid_references == frozenset({"bad-reference"})
    assert _workbook_appears_already_transformed(path) is False


def test_reference_on_non_protected_sheet_does_not_count(tmp_path):
    path = make_workbook(
        tmp_path / "unrelated.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        extra_reference_sheet=("Other", "D_DONOR_1"),
    )
    analysis = _analyze_protected_donor_workbook(path, None)
    assert analysis.references == {}
    assert _workbook_appears_already_transformed(path) is False
