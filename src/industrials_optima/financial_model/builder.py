"""Build a parameterized industrial 3-statement model from the base template.

The base template (templates/base_model.xlsx) is the Moog Inc. workbook
provided as the reference. This builder:

  1. Loads the base workbook (Model / Moog-Bull-Base-Bear / Moog-DCF /
     Moog-Charts plus the unrelated DSV reference tabs).
  2. Removes the DSV reference tabs and renames the Moog-prefixed tabs to
     generic names (Bull-Base-Bear, DCF, Charts).
  3. Clears all hardcoded numeric inputs in the time-period columns of the
     Model tab while leaving every formula in place — when historicals
     from SEC filings are dropped in, the formulas recompute automatically.
  4. Replaces Moog-specific text labels (company name, segment names,
     modeling-comment text) with values from CompanyConfig.
  5. Stamps DCF / scenario assumptions from CompanyConfig.

The four time-period columns are laid out the same as in the source
(Q1/10 → FY30E with FY totals every fifth column), so every cross-sheet
reference like ``Model!CD150`` continues to resolve to the same cell.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from .config import CompanyConfig, SegmentLine

BASE_TEMPLATE_PATH = Path(__file__).parent / "templates" / "base_model.xlsx"

# Sheets in the source workbook that belong to an unrelated DSV reference
# model and should be dropped from the output.
SHEETS_TO_DROP = ("Model_DSV_ref", "Bull-Base-Bear", "DCF", "Charts")

# Mapping of source-tab name to the generic tab name we want in the output.
SHEET_RENAME = {
    "Moog-Bull-Base-Bear": "Bull-Base-Bear",
    "Moog-DCF": "DCF",
    "Moog-Charts": "Charts",
}

# Time-period column range to scrub of hardcoded numeric values
# (Q1/10 in column C through FY30E in column CM).
TIME_PERIOD_COL_START = column_index_from_string("C")
TIME_PERIOD_COL_END = column_index_from_string("CM")

# Header / label rows in the Model tab that should never be cleared.
MODEL_LABEL_COL = column_index_from_string("B")
MODEL_HEADER_ROW = 6  # Q1/10, Q2/10, ... FY30E period labels

# Anchor rows in the Model tab's column B where each segment header lives.
# Identified by row, not by string match, so we don't rely on the exact Moog
# wording (which includes parenthetical notes) and can't accidentally
# rewrite a legacy header after the current header was already renamed.
LEGACY_SEGMENT_ROWS = (11, 19, 26, 33, 38)
CURRENT_SEGMENT_ROWS = (53, 64, 75, 86)


def build_template(config: CompanyConfig, output_path: str | Path) -> Path:
    """Build the parameterized model template and write it to ``output_path``.

    Returns the path the workbook was written to.
    """
    output_path = Path(output_path)
    wb = load_workbook(BASE_TEMPLATE_PATH)

    _drop_reference_sheets(wb)
    _rename_sheets(wb)

    model = wb["Model"]
    _stamp_header(model, config)
    _rename_segments(model, config)
    _clear_hardcoded_numerics(model)
    _clear_modeling_comments(model)
    _clear_scenario_assumption_tables(model)
    _replace_company_text_everywhere(wb, config)
    _stamp_scenario_sheet(wb["Bull-Base-Bear"], config)
    _stamp_dcf_sheet(wb["DCF"], config)
    _stamp_charts_sheet(wb["Charts"], config)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# Sheet management
# ---------------------------------------------------------------------------

def _drop_reference_sheets(wb: Workbook) -> None:
    for name in SHEETS_TO_DROP:
        if name in wb.sheetnames:
            del wb[name]


def _rename_sheets(wb: Workbook) -> None:
    for old, new in SHEET_RENAME.items():
        if old in wb.sheetnames:
            wb[old].title = new


# ---------------------------------------------------------------------------
# Model tab transforms
# ---------------------------------------------------------------------------

def _stamp_header(ws: Worksheet, config: CompanyConfig) -> None:
    """Overwrite the top-of-sheet title block (B2:B4)."""
    ws["B2"] = f"{config.company_name} ({config.ticker}) — {config.description_line}"
    ws["B3"] = config.header_subtitle()
    # Row 4 in the source carries a Moog-specific footnote about the FY22
    # segment realignment. Replace with a generic, editable note.
    ws["B4"] = (
        "Drop SEC filing data into the historical columns (C–CD). Forecast "
        "columns (CE–CM) recompute from the assumption tables on the right."
    )


def _rename_segments(ws: Worksheet, config: CompanyConfig) -> None:
    """Replace Moog segment headers (column B) by row anchor.

    Each segment occupies a known row in the Moog layout; the surrounding
    block of P&L line items (Net sales, EBIT, etc.) is defined relative to
    that header row. We overwrite just the header label.
    """
    current = list(config.segments_current) or [
        SegmentLine(name=f"[Segment {i + 1}]") for i in range(len(CURRENT_SEGMENT_ROWS))
    ]
    legacy = list(config.segments_legacy) or [
        SegmentLine(name=f"[Legacy Segment {i + 1}]") for i in range(len(LEGACY_SEGMENT_ROWS))
    ]
    for row, seg in zip(LEGACY_SEGMENT_ROWS, legacy):
        ws.cell(row=row, column=MODEL_LABEL_COL).value = seg.name
    for row, seg in zip(CURRENT_SEGMENT_ROWS, current):
        ws.cell(row=row, column=MODEL_LABEL_COL).value = seg.name


def _clear_hardcoded_numerics(ws: Worksheet) -> None:
    """Blank out every hardcoded numeric input in the time-period columns.

    Formulas (anything starting with ``=``) are left intact so that, once
    SEC-filing data is dropped into the cleared cells, every downstream
    calculation flows through.
    """
    for row in range(MODEL_HEADER_ROW + 1, ws.max_row + 1):
        for col in range(TIME_PERIOD_COL_START, TIME_PERIOD_COL_END + 1):
            cell = ws.cell(row=row, column=col)
            value = cell.value
            if value is None:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell.value = None


def _clear_modeling_comments(ws: Worksheet) -> None:
    """Strip the Moog-specific "Modeling Comments & Assumptions" column (CQ).

    The column header is preserved so the modeler can write their own notes.
    """
    col = column_index_from_string("CQ")
    for row in range(MODEL_HEADER_ROW + 1, ws.max_row + 1):
        cell = ws.cell(row=row, column=col)
        if isinstance(cell.value, str):
            cell.value = None


def _clear_scenario_assumption_tables(ws: Worksheet) -> None:
    """Clear Moog's Base/Bull/Bear scenario assumption tables (CT:CY).

    Row labels in column CT are kept so the modeler can plug in their own
    growth-rate / margin assumptions for whichever segments they have.
    """
    col_start = column_index_from_string("CU")
    col_end = column_index_from_string("CY")
    for row in range(54, 90):
        for col in range(col_start, col_end + 1):
            cell = ws.cell(row=row, column=col)
            if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                cell.value = None
    # Genericize the segment-keyed labels in column CT (Moog has
    # "Military Aircraft sales y/y %" etc.).
    ct_col = column_index_from_string("CT")
    for row in range(56, 90):
        label = ws.cell(row=row, column=ct_col).value
        if isinstance(label, str):
            new_label = _genericize_segment_label(label)
            if new_label != label:
                ws.cell(row=row, column=ct_col).value = new_label


def _genericize_segment_label(label: str) -> str:
    replacements = {
        "Military Aircraft": "[Segment 1]",
        "Commercial Aircraft": "[Segment 2]",
        "Space and Defense": "[Segment 3]",
        "Industrial": "[Segment 4]",
    }
    out = label
    for old, new in replacements.items():
        out = out.replace(old, new)
    return out


# ---------------------------------------------------------------------------
# Cross-sheet text replacement
# ---------------------------------------------------------------------------

# Order matters: longer / more-specific phrases first so we don't partially
# rewrite them with a shorter substitution.
def _company_text_replacements(config: CompanyConfig) -> list[tuple[str, str]]:
    return [
        ("Moog Inc.", f"{config.company_name} ({config.ticker})"),
        ("Moog Inc", f"{config.company_name} ({config.ticker})"),
        ("Moog's", f"{config.company_name}'s"),
        ("Moog", config.company_name),
    ]


def _replace_company_text_everywhere(wb: Workbook, config: CompanyConfig) -> None:
    replacements = _company_text_replacements(config)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                value = cell.value
                if not isinstance(value, str):
                    continue
                new_value = value
                for old, new in replacements:
                    if old in new_value:
                        new_value = new_value.replace(old, new)
                if new_value != value:
                    cell.value = new_value


# ---------------------------------------------------------------------------
# Bull / Base / Bear, DCF, Charts: light parameterization
# ---------------------------------------------------------------------------

def _stamp_scenario_sheet(ws: Worksheet, config: CompanyConfig) -> None:
    # K2 holds the "current share price" anchor used by upside / IRR formulas.
    ws["K2"] = config.current_share_price
    # B2 / B3 carry the title and subtitle.
    ws["B2"] = f"{config.company_name} ({config.ticker}) — Bull / Base / Bear Case P&L Summary"
    ws["B3"] = (
        f"Adjusted figures · {config.currency_symbol} {config.currency_units} · "
        "Linked to Model — edit scenario assumptions on the Model tab."
    )


def _stamp_dcf_sheet(ws: Worksheet, config: CompanyConfig) -> None:
    ws["B2"] = f"DCF VALUATION — {config.company_name} ({config.ticker})"
    ws["C5"] = config.risk_free_rate
    ws["C6"] = config.equity_risk_premium
    ws["C7"] = config.levered_beta
    ws["C9"] = config.pretax_cost_of_debt
    ws["C10"] = config.tax_rate
    ws["C12"] = config.target_debt_to_value
    ws["C27"] = config.terminal_growth
    ws["C42"] = config.current_share_price
    # The reverse-DCF section repeats current price at C106.
    if ws["C106"].value is not None:
        ws["C106"] = config.current_share_price


def _stamp_charts_sheet(ws: Worksheet, config: CompanyConfig) -> None:
    ws["B2"] = (
        f"{config.company_name} ({config.ticker}) — Historical Operating "
        "Performance (FY15–FY25)"
    )
    ws["B3"] = (
        f"All historicals · {config.currency_symbol} {config.currency_units} · "
        "Linked to Model."
    )
