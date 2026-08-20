"""Submitr integration tests for dcicutils ProtectedDonor transformation."""

from pathlib import Path
from unittest.mock import Mock, patch

import openpyxl
import pytest

from dcicutils.submitr.custom_excel import CustomExcel
from dcicutils.submitr import donor_transformer as _donor_transformer_module

if not hasattr(_donor_transformer_module, "DonorReferenceKind"):
    # The pinned dcicutils dependency (4dn-dcic/utils branch ajs/protected-donor-transform,
    # tracked at https://github.com/4dn-dcic/utils/pull/337) has not yet landed the analyze()/
    # DonorReferenceKind/portal-aware ProtectedDonor API these tests exercise. Skip rather than
    # fail collection until that dependency catches up.
    pytest.skip(
        "dcicutils.submitr.donor_transformer.DonorReferenceKind is not available in the "
        "pinned dcicutils dependency; see 4dn-dcic/utils PR #337.",
        allow_module_level=True,
    )

from dcicutils.submitr.donor_transformer import (
    DonorReferenceKind,
    ProtectedDonorTransformError,
    ProtectedDonorWorkbookTransformer,
)

from ..submission import (
    _analyze_protected_donor_workbook,
    _prepare_protected_donor_transform,
)


PROTECTED_SHEETS = [
    "Demographic",
    "DeathCircumstances",
    "FamilyHistory",
    "MedicalHistory",
    "TissueCollection",
]


def make_workbook(path: Path, *, references=None, donor_rows=None, protected_rows=None,
                  extra_reference_sheet=None):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    donor = workbook.create_sheet("Donor")
    donor.append(["submitted_id", "name", "status"])
    for row in donor_rows or []:
        donor.append(row)
    if protected_rows is not None:
        protected = workbook.create_sheet("ProtectedDonor")
        protected.append(["submitted_id", "name", "status"])
        for row in protected_rows:
            protected.append(row)
    for sheet_name in PROTECTED_SHEETS:
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(["donor", "value"])
        for reference in (references or {}).get(sheet_name, []):
            sheet.append([reference, "x"])
    if extra_reference_sheet:
        sheet = workbook.create_sheet(extra_reference_sheet[0])
        sheet.append(["donor"])
        sheet.append([extra_reference_sheet[1]])
    workbook.save(path)
    return path


def test_transform_only_referenced_donors_and_only_five_protected_sheets(tmp_path):
    path = make_workbook(
        tmp_path / "input.xlsx",
        donor_rows=[["D_DONOR_1", "referenced", "active"],
                    ["D_DONOR_2", "untouched", "active"]],
        references={"Demographic": ["D_DONOR_1"]},
        extra_reference_sheet=("Other", "D_DONOR_2"),
    )
    workbook = openpyxl.load_workbook(path)
    changed = ProtectedDonorWorkbookTransformer().transform(workbook)

    assert changed is True
    donor = workbook["Donor"]
    headers = [cell.value for cell in donor[1]]
    assert donor.cell(2, headers.index("protected_donor") + 1).value == "D_PROTECTED-DONOR_1"
    assert all(cell.value != "D_PROTECTED-DONOR_2" for cell in donor[3])
    assert workbook["Demographic"]["A2"].value == "D_PROTECTED-DONOR_1"
    assert workbook["Other"]["A2"].value == "D_DONOR_2"
    assert workbook["ProtectedDonor"].max_row == 2


def test_mixed_references_are_analyzed_and_transformed_incrementally(tmp_path):
    path = make_workbook(
        tmp_path / "mixed.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"], ["D_DONOR_2", "two", "active"]],
        protected_rows=[["D_PROTECTED-DONOR_2", "two", "in review"]],
        references={"Demographic": ["D_DONOR_1", "D_PROTECTED-DONOR_2"]},
    )
    workbook = openpyxl.load_workbook(path)
    analysis = ProtectedDonorWorkbookTransformer().analyze(workbook)
    assert analysis.references["D_DONOR_1"] == DonorReferenceKind.PLAIN_DONOR
    assert analysis.references["D_PROTECTED-DONOR_2"] == DonorReferenceKind.PROTECTED_DONOR
    assert analysis.needs_transformation

    ProtectedDonorWorkbookTransformer().transform(workbook)
    assert workbook["Demographic"]["A2"].value == "D_PROTECTED-DONOR_1"
    assert workbook["Demographic"]["A3"].value == "D_PROTECTED-DONOR_2"
    assert workbook["ProtectedDonor"].max_row == 3

    # A second pass is incremental: it does not duplicate existing rows.
    assert ProtectedDonorWorkbookTransformer().transform(workbook) is False
    assert workbook["ProtectedDonor"].max_row == 3


def test_missing_workbook_donor_is_an_error(tmp_path):
    path = tmp_path / "missing.xlsx"
    workbook = openpyxl.Workbook()
    workbook.active.title = "Demographic"
    workbook.active.append(["donor"])
    workbook.active.append(["D_DONOR_MISSING"])
    workbook.save(path)

    with pytest.raises(ProtectedDonorTransformError, match="absent from the workbook Donor sheet"):
        transformer = ProtectedDonorWorkbookTransformer()
        transformer.transform(openpyxl.load_workbook(path))


def test_protected_donor_can_be_resolved_from_workbook_or_portal(tmp_path):
    path = make_workbook(
        tmp_path / "portal.xlsx",
        references={"Demographic": ["D_PROTECTED-DONOR_PORTAL"]},
        protected_rows=None,
    )
    portal = Mock()
    portal.ref_exists.return_value = True
    analysis = _analyze_protected_donor_workbook(path, portal)
    assert analysis.references["D_PROTECTED-DONOR_PORTAL"] == DonorReferenceKind.PROTECTED_DONOR
    assert not analysis.needs_transformation


def test_submitr_analysis_distinguishes_partial_and_invalid_workbooks(tmp_path):
    partial = make_workbook(
        tmp_path / "partial.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        protected_rows=[["D_PROTECTED-DONOR_2", "two", "in review"]],
        references={"Demographic": ["D_DONOR_1", "D_PROTECTED-DONOR_2"]},
    )
    invalid = make_workbook(
        tmp_path / "invalid.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        references={"Demographic": ["not-an-id"]},
    )
    assert _prepare_protected_donor_transform(
        portal=None, ingestion_filename=str(partial), submission_centers=None,
        validation=False, no_query=False, transform_protected_donor=True,
        transformed_workbook_path=None,
    )[0] is True
    invalid_analysis = _analyze_protected_donor_workbook(invalid, None)
    assert invalid_analysis.invalid_references == frozenset({"not-an-id"})
    with pytest.raises(ProtectedDonorTransformError, match="Invalid donor reference"):
        _prepare_protected_donor_transform(
            portal=None, ingestion_filename=str(invalid), submission_centers=None,
            validation=False, no_query=False, transform_protected_donor=True,
            transformed_workbook_path=None,
        )


def test_prepare_auto_transforms_without_prompt_without_printing_output_path(tmp_path):
    path = make_workbook(
        tmp_path / "input.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        references={"Demographic": ["D_DONOR_1"]},
    )
    with patch("submitr.submission.yes_or_no") as prompt, \
            patch("submitr.submission.PRINT") as output:
        apply, output_path = _prepare_protected_donor_transform(
            portal=None, ingestion_filename=str(path), submission_centers=None,
            validation=False, no_query=False, transform_protected_donor=True,
            transformed_workbook_path=None,
        )
    assert apply is True
    assert output_path.endswith("input.transformed.xlsx")
    prompt.assert_not_called()
    messages = [str(call.args[0]) for call in output.call_args_list]
    assert not any("transformation is occurring" in message for message in messages)
    assert not any("Transformed workbook path:" in message for message in messages)


def test_custom_excel_saves_the_transformed_workbook(tmp_path):
    source = make_workbook(
        tmp_path / "source.xlsx",
        donor_rows=[["D_DONOR_1", "one", "active"]],
        references={"Demographic": ["D_DONOR_1"]},
    )
    destination = tmp_path / "source.transformed.xlsx"
    CustomExcel.with_portal(
        None, transform_protected_donor=True,
        transformed_workbook_path=str(destination),
    )(str(source))
    transformed = openpyxl.load_workbook(destination)
    assert transformed["Demographic"]["A2"].value == "D_PROTECTED-DONOR_1"
