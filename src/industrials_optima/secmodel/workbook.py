"""Render Copart's SEC data into a DSV-style, formula-driven equity model.

Mirrors the layout, formatting and methodology of the reference DSV model:

* One column block per fiscal year — Q1, Q2, 1H, Q3, Q4, FY — for 15 fiscal
  years, then five annual forecast columns (FY26E–FY30E), then Modelling Notes
  and CAGR columns.
* Colour convention: **blue = hard-coded, as-reported SEC input**, **black =
  live formula** (gross profit, margins, y/y, 1H = Q1+Q2, totals, ratios),
  **pale-yellow fill = forecast columns** driven by an assumptions/scenario
  block (Bull / Base / Bear) via ``CHOOSE(MATCH(...))``.
"""

from __future__ import annotations

from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .model import CopartModel
from .periods import fiscal_quarter, fiscal_year

# ---- palette (matches the reference model) --------------------------------
SLATE = "2F3E46"   # section header bg
TEAL = "52796F"    # sub / segment header bg
GREEN = "84A98C"   # CAGR header bg
MINT = "CAD2C5"    # subtotal highlight bg
EST = "FFFDE7"     # estimate column bg
YELLOW = "FFFF00"  # scenario toggle bg
BAND = "F3F5F4"    # zebra band
NAVY = "1F3864"
GREY = "595959"
BLUE = "0000FF"    # hard-coded input font
BLACK = "000000"

F_TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY)
F_NOTE = Font(name="Calibri", size=10, color=GREY)
F_NOTE_I = Font(name="Calibri", size=9, italic=True, color=GREY)
F_HDR = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
F_SEC = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
F_SUB = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
F_IN = Font(name="Calibri", size=10, color=BLUE)          # input
F_INB = Font(name="Calibri", size=10, bold=True, color=BLUE)
F_FX = Font(name="Calibri", size=10, color=BLACK)         # formula
F_FXB = Font(name="Calibri", size=10, bold=True, color=BLACK)
F_LBL = Font(name="Calibri", size=10, color=BLACK)
F_LBLB = Font(name="Calibri", size=10, bold=True, color=BLACK)
F_LBLG = Font(name="Calibri", size=10, color="404040")

FILL_SEC = PatternFill("solid", fgColor=SLATE)
FILL_SUB = PatternFill("solid", fgColor=TEAL)
FILL_CAGR = PatternFill("solid", fgColor=GREEN)
FILL_SUBTOT = PatternFill("solid", fgColor=MINT)
FILL_EST = PatternFill("solid", fgColor=EST)
FILL_YEL = PatternFill("solid", fgColor=YELLOW)
FILL_BAND = PatternFill("solid", fgColor=BAND)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right")
LEFTW = Alignment(horizontal="left", vertical="top", wrap_text=True)

NUM = '#,##0;(#,##0);"-"'
NUM1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
EPSF = '0.00;(0.00);"-"'
XF = '0.00x'

LABEL_COL = 2
FIRST_DATA = 3
SCEN_TOGGLE = "Model!$B$2_SCEN"  # replaced at runtime with real ref


def _dm(y: int, m: int, d: int) -> str:
    return f"{y:04d}-{m:02d}-{d:02d}"


class Column:
    __slots__ = ("idx", "letter", "kind", "fy", "q", "end", "is_est", "label")

    def __init__(self, idx, kind, fy, q=None, end=None, is_est=False, label=""):
        self.idx = idx
        self.letter = get_column_letter(idx)
        self.kind = kind  # 'Q','H','FY','EST'
        self.fy = fy
        self.q = q
        self.end = end
        self.is_est = is_est
        self.label = label


class WorkbookBuilder:
    def __init__(self, model: CopartModel):
        self.m = model
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.fys = [fiscal_year(e) for e in model.annual_ends]
        self.hist_fys = self.fys
        self.est_fys = list(range(self.fys[-1] + 1, self.fys[-1] + 6))
        self._plan_columns()
        self.rows: dict[str, int] = {}   # line-key -> row on Model sheet
        self.scen_cell = "$B$3"          # scenario toggle cell (set in _title)

    # ------------------------------------------------------------------ #
    def _plan_columns(self):
        cols: list[Column] = []
        self.fycol: dict[int, Column] = {}
        self.qcol: dict[tuple, Column] = {}
        self.hcol: dict[int, Column] = {}
        self.estcol: dict[int, Column] = {}
        idx = FIRST_DATA
        for fy in self.hist_fys:
            for q in (1, 2):
                end = self._resolve_q_end(fy, q)
                c = Column(idx, "Q", fy, q, end, label=f"Q{q} {str(fy)[2:]}")
                cols.append(c); self.qcol[(fy, q)] = c; idx += 1
            c = Column(idx, "H", fy, None, None, label=f"1H {str(fy)[2:]}")
            cols.append(c); self.hcol[fy] = c; idx += 1
            for q in (3, 4):
                end = self._resolve_q_end(fy, q)
                c = Column(idx, "Q", fy, q, end, label=f"Q{q} {str(fy)[2:]}")
                cols.append(c); self.qcol[(fy, q)] = c; idx += 1
            end = self._resolve_fy_end(fy)
            c = Column(idx, "FY", fy, None, end, label=f"FY{fy}")
            cols.append(c); self.fycol[fy] = c; idx += 1
        for fy in self.est_fys:
            c = Column(idx, "EST", fy, None, None, True, label=f"FY{fy}E")
            cols.append(c); self.estcol[fy] = c; idx += 1
        self.columns = cols
        self.notes_col = idx
        self.cagr5f_col = idx + 1
        self.cagr5h_col = idx + 2
        self.cagr10_col = idx + 3
        self.last_col = idx + 3
        # scenario table columns (well to the right)
        self.scen_c0 = self.last_col + 3  # label col
        self.scen_bull = self.scen_c0 + 1
        self.scen_base = self.scen_c0 + 2
        self.scen_bear = self.scen_c0 + 3

    def _resolve_q_end(self, fy, q):
        for e in self.m.quarter_ends:
            if fiscal_year(e) == fy and fiscal_quarter(e) == q:
                return e
        return None

    def _resolve_fy_end(self, fy):
        for e in self.m.annual_ends:
            if fiscal_year(e) == fy:
                return e
        return None

    # ------------------------------------------------------------------ #
    def build(self) -> Workbook:
        self.ws = self.wb.create_sheet("Model")
        self._title()
        self._header_row()
        self._assumptions_table()
        r = 8
        r = self._segment_section(r)
        r = self._income_statement(r)
        r = self._growth_margins(r)
        r = self._cash_flow(r)
        r = self._balance_sheet(r)
        r = self._ratios(r)
        r = self._valuation(r)
        self._column_setup()
        self._cover()
        self._scenario_summary()
        self._dcf()
        return self.wb

    # ------------------------------------------------------------------ #
    # low-level cell writers
    # ------------------------------------------------------------------ #
    def _c(self, r, cidx):
        return self.ws.cell(row=r, column=cidx)

    def _is_est_col(self, cidx):
        return cidx in (c.idx for c in self.columns if c.is_est)

    def _put(self, r, cidx, value, fmt=NUM, font=F_FX, est_fill=True, border=None,
             align=RIGHT):
        cell = self._c(r, cidx)
        cell.value = value
        cell.number_format = fmt
        cell.font = font
        cell.alignment = align
        if border:
            cell.border = border
        if est_fill and self._col_is_est(cidx):
            cell.fill = FILL_EST
        return cell

    def _col_is_est(self, cidx):
        return any(c.idx == cidx and c.is_est for c in self.columns)

    def _label(self, r, text, font=F_LBL, fill=None, indent=0, border=None):
        cell = self._c(r, LABEL_COL)
        cell.value = ("  " * indent) + text
        cell.font = font
        if fill:
            cell.fill = fill
        if border:
            cell.border = border
        return cell

    def _section(self, r, text):
        for cidx in range(LABEL_COL, self.last_col + 1):
            c = self._c(r, cidx)
            c.fill = FILL_SEC
            if cidx == LABEL_COL:
                c.value = text
                c.font = F_SEC
        return r + 1

    def _subheader(self, r, text):
        for cidx in range(LABEL_COL, self.last_col + 1):
            c = self._c(r, cidx)
            c.fill = FILL_SUB
            if cidx == LABEL_COL:
                c.value = text
                c.font = F_SUB
        return r + 1

    # ------------------------------------------------------------------ #
    def _title(self):
        ws = self.ws
        ws.cell(row=2, column=LABEL_COL, value="COPART, INC. (CPRT) — SEC-Filings 3-Statement Model").font = F_TITLE
        ws.cell(row=3, column=LABEL_COL,
                value="US GAAP as reported · US$ millions · FYE July 31 · Source: SEC EDGAR "
                      "Forms 10-K & 10-Q (data.sec.gov XBRL), CIK 0000900075").font = F_NOTE
        ws.cell(row=4, column=LABEL_COL,
                value="Blue = as-reported input from SEC filings · Black = formula · "
                      "Yellow columns = forecast (driven by Assumptions / scenario toggle).").font = F_NOTE_I
        # scenario toggle
        ws.cell(row=2, column=self.notes_col, value="Scenario:").font = F_LBLB
        tog = ws.cell(row=2, column=self.notes_col + 1, value="Base")
        tog.font = F_INB
        tog.fill = FILL_YEL
        tog.alignment = CENTER
        self.scen_cell = f"${get_column_letter(self.notes_col + 1)}$2"

    def _header_row(self):
        ws = self.ws
        r = 6
        hc = ws.cell(row=r, column=LABEL_COL, value="(US$ in millions)")
        hc.font = F_HDR; hc.fill = FILL_SEC; hc.alignment = Alignment(horizontal="left")
        for c in self.columns:
            cell = ws.cell(row=r, column=c.idx, value=c.label)
            cell.font = F_HDR
            cell.fill = FILL_EST if c.is_est else FILL_SEC
            cell.alignment = CENTER
        for cidx, txt in ((self.notes_col, "Modelling Notes"),
                          (self.cagr5f_col, "5Y CAGR (fwd)"),
                          (self.cagr5h_col, "5Y CAGR (hist)"),
                          (self.cagr10_col, "10Y CAGR")):
            cell = ws.cell(row=r, column=cidx, value=txt)
            cell.font = F_HDR
            cell.fill = FILL_CAGR
            cell.alignment = CENTER
        ws.freeze_panes = ws.cell(row=7, column=FIRST_DATA)

    # ------------------------------------------------------------------ #
    # helpers for value lookup
    # ------------------------------------------------------------------ #
    def _seg_val(self, metric, col: Column, bucket, is_stock=False):
        if col.kind == "FY":
            return self.m.seg_annual(metric, col.end, bucket)
        if col.kind == "Q" and col.end:
            return self.m.seg_quarter(metric, col.end, bucket, is_stock)
        return None

    def _flow(self, concepts, col: Column):
        if col.kind == "FY":
            return self.m.flow_value(concepts, col.end, "FY")
        if col.kind == "Q" and col.end:
            return self.m.quarter_flow(concepts, col.end)
        return None

    def _instant(self, concepts, col: Column):
        end = col.end
        if col.kind == "H":
            c = self.qcol.get((col.fy, 2))
            end = c.end if c else None
        if not end:
            return None
        return self.m.instant_value(concepts, end)

    def _mm(self, v):
        return None if v is None else v / 1e6

    # ------------------------------------------------------------------ #
    # a generic "input row" over history + optional 1H/FY formulas
    # ------------------------------------------------------------------ #
    def _input_row(self, r, key, label, getter, *, indent=1, bold=False,
                   fmt=NUM, sum_1h=True, present=None):
        """Write a hard-coded input row across history; 1H is a Q1+Q2 formula.

        ``getter(col)`` returns the raw (already-scaled) value for a column or
        None.  Records presence of a value per column-idx in ``present`` dict.
        """
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=indent)
        for c in self.columns:
            if c.is_est:
                continue
            if c.kind == "H" and sum_1h:
                q1, q2 = self.qcol.get((c.fy, 1)), self.qcol.get((c.fy, 2))
                if q1 and q2:
                    self._put(r, c.idx, f"={q1.letter}{r}+{q2.letter}{r}",
                              fmt=fmt, font=F_FXB if bold else F_FX)
                continue
            v = getter(c)
            if v is not None:
                self._put(r, c.idx, v, fmt=fmt, font=F_INB if bold else F_IN)
                if present is not None:
                    present[c.idx] = r
        self.rows[key] = r
        return r + 1

    def _formula_row(self, r, key, label, make_formula, *, indent=1, bold=False,
                     fmt=NUM, hist_only=False, present_req=None, est_formula=None):
        """Write a formula row. ``make_formula(col)`` returns a formula string
        (without leading '=') or None to skip.  ``present_req`` is a list of row
        keys whose input cells must exist in that column for the formula to be
        written (avoids GP=rev when costs are blank)."""
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=indent)
        for c in self.columns:
            if c.is_est:
                f = est_formula(c) if est_formula else (make_formula(c) if not hist_only else None)
            else:
                if present_req and not self._present_ok(c, present_req):
                    continue
                f = make_formula(c)
            if f:
                self._put(r, c.idx, "=" + f, fmt=fmt, font=F_FXB if bold else F_FX)
        self.rows[key] = r
        return r + 1

    def _present_ok(self, col, keys):
        for k in keys:
            rr = self.rows.get(k)
            if rr is None:
                return False
            v = self._c(rr, col.idx).value
            if v is None:
                return False
        return True

    def _cagr(self, r, kind="level"):
        """Fill the three CAGR columns for row r."""
        L = get_column_letter
        fy_first = self.fycol[self.hist_fys[0]].letter
        fy_last = self.fycol[self.hist_fys[-1]].letter
        fy_5h = self.fycol[self.hist_fys[-6]].letter if len(self.hist_fys) >= 6 else fy_first
        est_last = self.estcol[self.est_fys[-1]].letter
        # forward 5Y
        self.ws.cell(row=r, column=self.cagr5f_col,
                     value=f'=IFERROR(({est_last}{r}/{fy_last}{r})^(1/5)-1,"n/m")').number_format = PCT
        self.ws.cell(row=r, column=self.cagr5h_col,
                     value=f'=IFERROR(({fy_last}{r}/{fy_5h}{r})^(1/5)-1,"n/m")').number_format = PCT
        self.ws.cell(row=r, column=self.cagr10_col,
                     value=f'=IFERROR(({fy_last}{r}/{fy_first}{r})^(1/{len(self.hist_fys)-1})-1,"n/m")').number_format = PCT
        for cc in (self.cagr5f_col, self.cagr5h_col, self.cagr10_col):
            self.ws.cell(row=r, column=cc).font = F_FX

    def cagr5f_col_at(self, r):  # helper kept for clarity
        return self.cagr5f_col

    # ------------------------------------------------------------------ #
    # SECTION: Segment P&L
    # ------------------------------------------------------------------ #
    def _segment_section(self, r):
        r = self._section(r, "SEGMENT P&L — BY REPORTABLE SEGMENT (US & INTERNATIONAL)")
        buckets = [("US", "United States"), ("International", "International")]
        seg_rev_rows = {}
        seg_oi_rows = {}
        for bkey, bname in buckets:
            r = self._subheader(r, bname)
            rk = f"seg_{bkey}_rev"
            r = self._input_row(r, rk, "Revenue",
                                lambda c, b=bkey: self._mm(self._seg_val("revenue", c, b)),
                                indent=1)
            seg_rev_rows[bkey] = self.rows[rk]
            self._cagr(self.rows[rk])
            oik = f"seg_{bkey}_oi"
            r = self._input_row(r, oik, "Operating income",
                                lambda c, b=bkey: self._mm(self._seg_val("operating_income", c, b)),
                                indent=1, bold=True)
            seg_oi_rows[bkey] = self.rows[oik]
            self._cagr(self.rows[oik])
            # operating margin (formula)
            rk_m = f"seg_{bkey}_om"
            rowrev, rowoi = seg_rev_rows[bkey], seg_oi_rows[bkey]
            r = self._formula_row(r, rk_m, "Operating margin %",
                                  lambda c, rr=rowrev, ro=rowoi: f'IFERROR({c.letter}{ro}/{c.letter}{rr},"")',
                                  indent=1, fmt=PCT)
            # y/y revenue (FY + EST only)
            r = self._yoy_row(r, f"seg_{bkey}_revyoy", "Revenue y/y %", rowrev)
            # D&A, CapEx, Assets, Goodwill
            r = self._input_row(r, f"seg_{bkey}_dna", "Depreciation & amortisation",
                                lambda c, b=bkey: self._mm(self._seg_val("dna", c, b)), indent=1)
            r = self._input_row(r, f"seg_{bkey}_capex", "Capital expenditures",
                                lambda c, b=bkey: self._mm(self._seg_val("capex", c, b)), indent=1)
            r = self._input_row(r, f"seg_{bkey}_assets", "Total assets",
                                lambda c, b=bkey: self._mm(self._seg_val("assets", c, b, True)),
                                indent=1, sum_1h=False)
            r = self._input_row(r, f"seg_{bkey}_gw", "Goodwill",
                                lambda c, b=bkey: self._mm(self._seg_val("goodwill", c, b, True)),
                                indent=1, sum_1h=False)
            r += 1
        # Group total (formulas = US + Intl)
        r = self._subheader(r, "Group total (consolidated segments)")
        us, it = "US", "International"
        r = self._seg_total_row(r, "seg_tot_rev", "Revenue", seg_rev_rows[us], seg_rev_rows[it], bold=True)
        self.rows["group_rev"] = self.rows["seg_tot_rev"]
        self._cagr(self.rows["seg_tot_rev"])
        r = self._seg_total_row(r, "seg_tot_oi", "Operating income", seg_oi_rows[us], seg_oi_rows[it], bold=True)
        self.rows["group_oi"] = self.rows["seg_tot_oi"]
        self._cagr(self.rows["seg_tot_oi"])
        rr, ro = self.rows["seg_tot_rev"], self.rows["seg_tot_oi"]
        r = self._formula_row(r, "seg_tot_om", "Operating margin %",
                              lambda c, a=rr, b=ro: f'IFERROR({c.letter}{b}/{c.letter}{a},"")',
                              indent=1, fmt=PCT)
        # revenue mix
        r = self._subheader(r, "Revenue mix %")
        for bkey, bname in buckets:
            rowrev = seg_rev_rows[bkey]
            tot = self.rows["seg_tot_rev"]
            r = self._formula_row(r, f"mix_{bkey}", bname,
                                  lambda c, rr=rowrev, tt=tot: f'IFERROR({c.letter}{rr}/{c.letter}{tt},"")',
                                  indent=1, fmt=PCT)
        return r + 1

    def _seg_total_row(self, r, key, label, row_us, row_it, bold=False):
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=1,
                    border=Border(top=Side(style="thin", color="808080")))
        for c in self.columns:
            f = f"={c.letter}{row_us}+{c.letter}{row_it}"
            cell = self._put(r, c.idx, f, fmt=NUM, font=F_FXB if bold else F_FX)
            cell.border = Border(top=Side(style="thin", color="808080"))
        self.rows[key] = r
        return r + 1

    def _yoy_row(self, r, key, label, data_row):
        self._label(r, label, font=F_LBLG, indent=1)
        for c in self.columns:
            if c.kind == "FY":
                prev = self.fycol.get(c.fy - 1)
                if prev:
                    self._put(r, c.idx, f"=IFERROR({c.letter}{data_row}/{prev.letter}{data_row}-1,\"\")",
                              fmt=PCT, font=F_FX)
            elif c.is_est:
                prevfy = c.fy - 1
                prev = self.estcol.get(prevfy) or self.fycol.get(prevfy)
                if prev:
                    self._put(r, c.idx, f"=IFERROR({c.letter}{data_row}/{prev.letter}{data_row}-1,\"\")",
                              fmt=PCT, font=F_FX)
        self.rows[key] = r
        return r + 1

    # ------------------------------------------------------------------ #
    # SECTION: Consolidated income statement
    # ------------------------------------------------------------------ #
    def _income_statement(self, r):
        r = self._section(r, "CONSOLIDATED INCOME STATEMENT")
        present = {}
        REV = ["RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "Revenues"]
        # Total revenue — est = group segment revenue
        r = self._is_line(r, "revenue", "Total revenues (service + vehicle sales)",
                          lambda c: self._mm(self._flow(REV, c)), present=present, bold=True,
                          est_formula=lambda c: f"{c.letter}{self.rows['group_rev']}")
        self._cagr(self.rows["revenue"])
        r = self._is_line(r, "yard", "Yard operations expense",
                          lambda c: self._mm(self._flow(["DirectOperatingCosts"], c)), present=present,
                          est_formula=None)
        r = self._is_line(r, "cvs", "Cost of vehicle sales",
                          lambda c: self._mm(self._flow(["CostDirectMaterial", "CostOfGoodsSold"], c)),
                          present=present)
        # Gross profit = rev - yard - cvs
        r = self._formula_row(r, "gross_profit", "Gross profit",
                              lambda c: f"{c.letter}{self.rows['revenue']}-{c.letter}{self.rows['yard']}-{c.letter}{self.rows['cvs']}",
                              indent=0, bold=True, present_req=["revenue", "yard", "cvs"],
                              est_formula=lambda c: None)
        r = self._is_line(r, "gna", "General & administrative",
                          lambda c: self._mm(self._flow(["GeneralAndAdministrativeExpense"], c)), present=present)
        # Operating income (formula) — est comes from segment total
        r = self._formula_row(r, "operating_income", "Operating income",
                              lambda c: f"{c.letter}{self.rows['gross_profit']}-{c.letter}{self.rows['gna']}",
                              indent=0, bold=True, present_req=["gross_profit", "gna"],
                              est_formula=lambda c: f"{c.letter}{self.rows['group_oi']}")
        self._cagr(self.rows["operating_income"])
        # Other income / expense net — input, forced so pretax ties
        r = self._is_line(r, "other", "Interest & other income / (expense), net",
                          self._other_income_getter, present=present,
                          est_formula=lambda c: f"{c.letter}{self.rows['revenue']}*{self.scen('AS_otherPctRev', c)}")
        # Pretax
        r = self._formula_row(r, "pretax", "Income before income taxes",
                              lambda c: f"{c.letter}{self.rows['operating_income']}+{c.letter}{self.rows['other']}",
                              indent=0, bold=True, present_req=["operating_income"],
                              est_formula=lambda c: f"{c.letter}{self.rows['operating_income']}+{c.letter}{self.rows['other']}")
        # order below is pretax(R) → tax(R+1) → etr(R+2); tax est references etr row
        r = self._is_line(r, "tax", "Income tax expense",
                          lambda c: self._mm(self._flow(["IncomeTaxExpenseBenefit"], c)), present=present,
                          est_formula=lambda c: f"{c.letter}{self.rows['pretax']}*{c.letter}{self.rows['pretax']+2}")
        # effective tax rate
        r = self._formula_row(r, "etr", "  Effective tax rate",
                              lambda c: f'IFERROR({c.letter}{self.rows["tax"]}/{c.letter}{self.rows["pretax"]},"")',
                              indent=1, fmt=PCT,
                              est_formula=lambda c: self.scen("AS_taxRate", c))
        r = self._formula_row(r, "net_income", "Net income",
                              lambda c: f"{c.letter}{self.rows['pretax']}-{c.letter}{self.rows['tax']}",
                              indent=0, bold=True, present_req=["pretax", "tax"],
                              est_formula=lambda c: f"{c.letter}{self.rows['pretax']}-{c.letter}{self.rows['tax']}")
        self._cagr(self.rows["net_income"])
        # per share — sh_diluted first (buyback rollforward), sh_basic follows it
        shd_row = r
        self.rows["sh_diluted"] = shd_row
        r = self._is_line(r, "sh_diluted", "Weighted-avg shares — diluted (m)",
                          lambda c: self._mm(self._flow(["WeightedAverageNumberOfDilutedSharesOutstanding"], c)),
                          present=present, sum_1h=False,
                          est_formula=lambda c, rr=shd_row: (
                              f"{self._prev(c).letter}{rr}*(1-{self.scen('AS_buyback', c)})"
                              if self._prev(c) else None))
        r = self._is_line(r, "sh_basic", "Weighted-avg shares — basic (m)",
                          lambda c: self._mm(self._flow(["WeightedAverageNumberOfSharesOutstandingBasic"], c)),
                          present=present, sum_1h=False,
                          est_formula=lambda c, rr=shd_row: f"{c.letter}{rr}")
        r = self._formula_row(r, "eps_basic", "EPS — basic ($)",
                              lambda c: f'IFERROR({c.letter}{self.rows["net_income"]}/{c.letter}{self.rows["sh_basic"]},"")',
                              indent=0, fmt=EPSF, hist_only=False,
                              est_formula=lambda c: f'IFERROR({c.letter}{self.rows["net_income"]}/{c.letter}{self.rows["sh_basic"]},"")')
        r = self._formula_row(r, "eps_diluted", "EPS — diluted ($)",
                              lambda c: f'IFERROR({c.letter}{self.rows["net_income"]}/{c.letter}{self.rows["sh_diluted"]},"")',
                              indent=0, bold=True, fmt=EPSF,
                              est_formula=lambda c: f'IFERROR({c.letter}{self.rows["net_income"]}/{c.letter}{self.rows["sh_diluted"]},"")')
        self._cagr(self.rows["eps_diluted"])
        self._label(r, "Note: EPS and share counts are as-reported each period and are NOT retroactively "
                       "adjusted for Copart's stock splits, so they are not comparable across split dates.",
                    font=F_NOTE_I, indent=1)
        r += 1
        return r + 1

    def _is_line(self, r, key, label, getter, *, present, bold=False, fmt=NUM,
                 sum_1h=True, est_formula=None):
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=0)
        for c in self.columns:
            if c.is_est:
                if est_formula:
                    f = est_formula(c)
                    if f:
                        self._put(r, c.idx, "=" + f, fmt=fmt, font=F_FXB if bold else F_FX)
                continue
            if c.kind == "H" and sum_1h:
                q1, q2 = self.qcol.get((c.fy, 1)), self.qcol.get((c.fy, 2))
                if q1 and q2 and (self._c(r, q1.idx).value is not None or self._c(r, q2.idx).value is not None):
                    self._put(r, c.idx, f"={q1.letter}{r}+{q2.letter}{r}", fmt=fmt,
                              font=F_FXB if bold else F_FX)
                continue
            v = getter(c)
            if v is not None:
                self._put(r, c.idx, v, fmt=fmt, font=F_INB if bold else F_IN)
                present[c.idx] = r
        self.rows[key] = r
        return r + 1

    def _other_income_getter(self, col):
        oi = self._flow(["OperatingIncomeLoss"], col)
        pt = self._flow(["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                         "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"], col)
        if oi is None or pt is None:
            return None
        return self._mm(pt - oi)

    def _shares_est(self, col):
        prevfy = col.fy - 1
        prev = self.estcol.get(prevfy) or self.fycol.get(prevfy)
        if not prev:
            return None
        return f"{prev.letter}{self.rows['sh_diluted']}*(1-{self.scen('AS_buyback', col)})"

    # ------------------------------------------------------------------ #
    def _growth_margins(self, r):
        r = self._section(r, "GROWTH & MARGINS")
        rev, gp, oi, ni = (self.rows["revenue"], self.rows["gross_profit"],
                           self.rows["operating_income"], self.rows["net_income"])
        r = self._yoy_row(r, "gm_revyoy", "Revenue y/y %", rev)
        r = self._yoy_row(r, "gm_oiyoy", "Operating income y/y %", oi)
        r = self._yoy_row(r, "gm_epsyoy", "EPS (diluted) y/y %", self.rows["eps_diluted"])
        r = self._margin_row(r, "gm_gpm", "Gross margin %", gp, rev)
        r = self._margin_row(r, "gm_opm", "Operating margin %", oi, rev)
        r = self._margin_row(r, "gm_npm", "Net margin %", ni, rev)
        return r + 1

    def _margin_row(self, r, key, label, num, den):
        self._label(r, label, font=F_LBLG, indent=1)
        for c in self.columns:
            self._put(r, c.idx, f'=IFERROR({c.letter}{num}/{c.letter}{den},"")', fmt=PCT, font=F_FX)
        self.rows[key] = r
        # CAGR cols = average of period margins
        self._avg_cagr(r)
        return r + 1

    def _avg_cagr(self, r):
        fyletters = [self.fycol[fy].letter for fy in self.hist_fys]
        estletters = [self.estcol[fy].letter for fy in self.est_fys]
        rng_h = ",".join(f"{L}{r}" for L in fyletters[-5:])
        rng_f = ",".join(f"{L}{r}" for L in estletters)
        rng_10 = ",".join(f"{L}{r}" for L in fyletters)
        self.ws.cell(row=r, column=self.cagr5f_col, value=f'=IFERROR(AVERAGE({rng_f}),"n/m")').number_format = PCT
        self.ws.cell(row=r, column=self.cagr5h_col, value=f'=IFERROR(AVERAGE({rng_h}),"n/m")').number_format = PCT
        self.ws.cell(row=r, column=self.cagr10_col, value=f'=IFERROR(AVERAGE({rng_10}),"n/m")').number_format = PCT
        for cc in (self.cagr5f_col, self.cagr5h_col, self.cagr10_col):
            self.ws.cell(row=r, column=cc).font = F_FX

    # ------------------------------------------------------------------ #
    def _cash_flow(self, r):
        r = self._section(r, "CONSOLIDATED CASH FLOW  (fiscal-year basis)")
        note = self._label(r, "Interim cash-flow statements are filed year-to-date; only fiscal-year figures are shown below.",
                           font=F_NOTE_I, indent=1)
        r += 1
        # CFO(R) is followed by D&A(R+1), SBC(R+2), ΔNWC(R+3); CFO est references those rows
        cfo_row = r
        r = self._fy_input_row(r, "cfo", "Cash from operations",
                               ["NetCashProvidedByUsedInOperatingActivities"], bold=True,
                               est_formula=lambda c, R=cfo_row: f"{c.letter}{self.rows['net_income']}+{c.letter}{R+1}+{c.letter}{R+2}-{c.letter}{R+3}")
        r = self._fy_input_row(r, "cf_dna", "  Depreciation & amortisation",
                               ["DepreciationDepletionAndAmortization"],
                               est_formula=lambda c: f"{c.letter}{self.rows['revenue']}*{self.scen('AS_daPctRev', c)}")
        r = self._fy_input_row(r, "cf_sbc", "  Stock-based compensation",
                               ["ShareBasedCompensation"],
                               est_formula=lambda c: f"{c.letter}{self.rows['revenue']}*{self.scen('AS_sbcPctRev', c)}")
        # change in working capital (est driver only; hist blank)
        r = self._label_only_row(r, "dwc", "  Change in net working capital (est.)",
                                 est_formula=lambda c: f"({c.letter}{self.rows['revenue']}-{self._prev(c).letter}{self.rows['revenue']})*{self.scen('AS_nwcPctRev', c)}")
        r = self._fy_input_row(r, "capex", "Capital expenditures",
                               ["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"],
                               est_formula=lambda c: f"-{c.letter}{self.rows['revenue']}*{self.scen('AS_capexPctRev', c)}")
        r = self._fy_input_row(r, "cfi", "Cash from investing", ["NetCashProvidedByUsedInInvestingActivities"], bold=True)
        r = self._fy_input_row(r, "cff", "Cash from financing", ["NetCashProvidedByUsedInFinancingActivities"], bold=True)
        # FCF
        r = self._formula_row(r, "fcf", "Free cash flow (CFO − CapEx)",
                              lambda c: f"{c.letter}{self.rows['cfo']}+{c.letter}{self.rows['capex']}" if c.is_est
                              else (f"{c.letter}{self.rows['cfo']}-{c.letter}{self.rows['capex']}" if self._present_ok(c, ['cfo','capex']) else None),
                              indent=0, bold=True,
                              est_formula=lambda c: f"{c.letter}{self.rows['cfo']}+{c.letter}{self.rows['capex']}")
        self._cagr(self.rows["fcf"])
        r = self._margin_row(r, "fcf_margin", "  FCF margin %", self.rows["fcf"], self.rows["revenue"])
        r = self._formula_row(r, "capex_pct", "  CapEx % of revenue",
                              lambda c: f'IFERROR(ABS({c.letter}{self.rows["capex"]})/{c.letter}{self.rows["revenue"]},"")',
                              indent=1, fmt=PCT,
                              est_formula=lambda c: f'IFERROR(ABS({c.letter}{self.rows["capex"]})/{c.letter}{self.rows["revenue"]},"")')
        return r + 1

    def _prev(self, col):
        prevfy = col.fy - 1
        return self.estcol.get(prevfy) or self.fycol.get(prevfy)

    def _fy_input_row(self, r, key, label, concepts, *, bold=False, est_formula=None, fmt=NUM):
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=0 if bold else 1)
        for c in self.columns:
            if c.is_est:
                if est_formula:
                    f = est_formula(c)
                    if f:
                        self._put(r, c.idx, "=" + f, fmt=fmt, font=F_FXB if bold else F_FX)
                continue
            if c.kind != "FY":
                continue
            v = self._mm(self.m.flow_value(concepts, c.end, "FY"))
            if v is not None:
                self._put(r, c.idx, v, fmt=fmt, font=F_INB if bold else F_IN)
        self.rows[key] = r
        return r + 1

    def _label_only_row(self, r, key, label, *, est_formula, fmt=NUM):
        self._label(r, label, font=F_LBLG, indent=1)
        for c in self.columns:
            if c.is_est and est_formula:
                f = est_formula(c)
                if f:
                    self._put(r, c.idx, "=" + f, fmt=fmt, font=F_FX)
        self.rows[key] = r
        return r + 1

    # ------------------------------------------------------------------ #
    def _balance_sheet(self, r):
        r = self._section(r, "CONSOLIDATED BALANCE SHEET  (period end)")
        defs = [
            ("bs_cash", "Cash & cash equivalents",
             ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"], False),
            ("bs_ca", "Total current assets", ["AssetsCurrent"], False),
            ("bs_ppe", "Property & equipment, net", ["PropertyPlantAndEquipmentNet"], False),
            ("bs_gw", "Goodwill", ["Goodwill"], False),
            ("bs_ta", "Total assets", ["Assets"], True),
            ("bs_cl", "Total current liabilities", ["LiabilitiesCurrent"], False),
            ("bs_debt", "Long-term debt", ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebt"], False),
            ("bs_tl", "Total liabilities", ["Liabilities"], True),
            ("bs_eq", "Total stockholders' equity",
             ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], True),
        ]
        for key, label, concepts, bold in defs:
            r = self._bs_row(r, key, label, concepts, bold=bold)
        # equity roll-forward for estimates: prior equity + NI − dividends − buybacks
        self._bs_equity_est()
        # current ratio
        r = self._formula_row(r, "bs_curr", "  Current ratio (x)",
                              lambda c: f'IFERROR({c.letter}{self.rows["bs_ca"]}/{c.letter}{self.rows["bs_cl"]},"")',
                              indent=1, fmt=XF,
                              est_formula=lambda c: None)
        return r + 1

    def _bs_row(self, r, key, label, concepts, bold=False):
        self._label(r, label, font=F_LBLB if bold else F_LBL, indent=0 if bold else 1)
        for c in self.columns:
            if c.is_est:
                continue  # est filled selectively later (equity)
            end = c.end
            if c.kind == "H":
                q2 = self.qcol.get((c.fy, 2))
                end = q2.end if q2 else None
            if not end:
                continue
            v = self._mm(self.m.instant_value(concepts, end))
            if v is not None:
                self._put(r, c.idx, v, fmt=NUM, font=F_INB if bold else F_IN)
        self.rows[key] = r
        return r + 1

    def _bs_equity_est(self):
        r = self.rows["bs_eq"]
        for c in self.columns:
            if not c.is_est:
                continue
            prev = self._prev(c)
            if not prev:
                continue
            # equity + net income − buybacks (approx via financing not modelled)
            f = f"={prev.letter}{r}+{c.letter}{self.rows['net_income']}"
            self._put(r, c.idx, f, fmt=NUM, font=F_FXB)

    # ------------------------------------------------------------------ #
    def _ratios(self, r):
        r = self._section(r, "RATIO ANALYSIS")
        ni, eq, ta = self.rows["net_income"], self.rows["bs_eq"], self.rows["bs_ta"]
        oi, dna = self.rows["operating_income"], self.rows["cf_dna"]
        debt, cash = self.rows["bs_debt"], self.rows["bs_cash"]
        etr = self.rows["etr"]
        # EBITDA
        r = self._formula_row(r, "ebitda", "EBITDA (Operating income + D&A)",
                              lambda c: f'IFERROR({c.letter}{oi}+{c.letter}{dna},"")',
                              indent=0, bold=True,
                              est_formula=lambda c: f'{c.letter}{oi}+{c.letter}{dna}')
        r = self._formula_row(r, "roa", "Return on assets (ROA)",
                              lambda c: f'IFERROR({c.letter}{ni}/{c.letter}{ta},"")', indent=1, fmt=PCT,
                              est_formula=lambda c: None)
        r = self._formula_row(r, "roe", "Return on equity (ROE)",
                              lambda c: f'IFERROR({c.letter}{ni}/{c.letter}{eq},"")', indent=1, fmt=PCT,
                              est_formula=lambda c: f'IFERROR({c.letter}{ni}/{c.letter}{eq},"")')
        r = self._formula_row(r, "nopat", "NOPAT = EBIT × (1 − tax)",
                              lambda c: f'IFERROR({c.letter}{oi}*(1-{c.letter}{etr}),"")', indent=1,
                              est_formula=lambda c: f'{c.letter}{oi}*(1-{c.letter}{etr})')
        r = self._formula_row(r, "roic", "ROIC = NOPAT / (Equity + Debt − Cash)",
                              lambda c: f'IFERROR({c.letter}{self.rows["nopat"]}/({c.letter}{eq}+{c.letter}{debt}-{c.letter}{cash}),"")',
                              indent=1, fmt=PCT, est_formula=lambda c: None)
        r = self._formula_row(r, "ndebt", "Net debt (Debt − Cash)",
                              lambda c: f'IFERROR({c.letter}{debt}-{c.letter}{cash},"")', indent=1,
                              est_formula=lambda c: None)
        r = self._formula_row(r, "nde", "Net debt / EBITDA (x)",
                              lambda c: f'IFERROR({c.letter}{self.rows["ndebt"]}/{c.letter}{self.rows["ebitda"]},"")',
                              indent=1, fmt=XF, est_formula=lambda c: None)
        return r + 1

    # ------------------------------------------------------------------ #
    def _valuation(self, r):
        r = self._section(r, "VALUATION  (share price is a manual input — not from SEC filings)")
        # price input row (blue, manual) on FY + EST columns
        self._label(r, "Avg. share price ($) — manual input", font=F_LBL, indent=0)
        for c in self.columns:
            if c.kind in ("FY", "EST"):
                cell = self._put(r, c.idx, None, fmt=EPSF, font=F_IN)
        self.rows["px"] = r
        r += 1
        px, sh, ni = self.rows["px"], self.rows["sh_diluted"], self.rows["net_income"]
        r = self._formula_row(r, "mktcap", "Market capitalisation",
                              lambda c: (f'IFERROR({c.letter}{px}*{c.letter}{sh},"")' if c.kind in ("FY",) else None),
                              indent=1, est_formula=lambda c: f'IFERROR({c.letter}{px}*{c.letter}{sh},"")')
        r = self._formula_row(r, "ev", "Enterprise value (Mkt cap + Net debt)",
                              lambda c: (f'IFERROR({c.letter}{self.rows["mktcap"]}+{c.letter}{self.rows["ndebt"]},"")' if c.kind=="FY" else None),
                              indent=1, est_formula=lambda c: None)
        r = self._formula_row(r, "ev_ebitda", "  EV / EBITDA (x)",
                              lambda c: (f'IFERROR({c.letter}{self.rows["ev"]}/{c.letter}{self.rows["ebitda"]},"")' if c.kind=="FY" else None),
                              indent=1, fmt=XF, est_formula=lambda c: None)
        r = self._formula_row(r, "pe", "  P / E (x)",
                              lambda c: (f'IFERROR({c.letter}{px}/{c.letter}{self.rows["eps_diluted"]},"")' if c.kind in ("FY",) else None),
                              indent=1, fmt=XF, est_formula=lambda c: f'IFERROR({c.letter}{px}/{c.letter}{self.rows["eps_diluted"]},"")')
        r = self._formula_row(r, "fcfy", "  FCF yield %",
                              lambda c: (f'IFERROR({c.letter}{self.rows["fcf"]}/{c.letter}{self.rows["mktcap"]},"")' if c.kind=="FY" else None),
                              indent=1, fmt=PCT, est_formula=lambda c: None)
        return r + 1

    # ------------------------------------------------------------------ #
    # Assumptions / scenario table (Bull / Base / Bear)
    # ------------------------------------------------------------------ #
    ASSUMPTIONS = [
        ("AS_revGrowth_US", "Revenue growth — US", PCT, {"Bull": 0.14, "Base": 0.10, "Bear": 0.04}),
        ("AS_revGrowth_Intl", "Revenue growth — International", PCT, {"Bull": 0.16, "Base": 0.11, "Bear": 0.04}),
        ("AS_opMargin_US", "Operating margin — US", PCT, {"Bull": 0.40, "Base": 0.385, "Bear": 0.35}),
        ("AS_opMargin_Intl", "Operating margin — International", PCT, {"Bull": 0.30, "Base": 0.27, "Bear": 0.22}),
        ("AS_otherPctRev", "Other income % of revenue", PCT, {"Bull": 0.02, "Base": 0.015, "Bear": 0.01}),
        ("AS_taxRate", "Effective tax rate", PCT, {"Bull": 0.22, "Base": 0.23, "Bear": 0.25}),
        ("AS_daPctRev", "D&A % of revenue", PCT, {"Bull": 0.045, "Base": 0.05, "Bear": 0.055}),
        ("AS_sbcPctRev", "Stock-based comp % of revenue", PCT, {"Bull": 0.006, "Base": 0.007, "Bear": 0.008}),
        ("AS_nwcPctRev", "ΔNWC % of Δrevenue", PCT, {"Bull": 0.05, "Base": 0.08, "Bear": 0.10}),
        ("AS_capexPctRev", "CapEx % of revenue", PCT, {"Bull": 0.10, "Base": 0.12, "Bear": 0.14}),
        ("AS_buyback", "Buyback (% shares retired / yr)", PCT, {"Bull": 0.010, "Base": 0.005, "Bear": 0.000}),
    ]

    def _assumptions_table(self):
        ws = self.ws
        c0 = self.scen_c0
        r0 = 6
        ws.cell(row=r0 - 1, column=c0, value="SCENARIO / ASSUMPTIONS TABLE").font = F_SEC
        for cc in range(c0, self.scen_bear + 1):
            ws.cell(row=r0 - 1, column=cc).fill = FILL_SEC
        for i, (name, label, _) in enumerate([("Driver", "Driver", None)]):
            pass
        heads = [(c0, "Driver"), (self.scen_bull, "Bull"), (self.scen_base, "Base"), (self.scen_bear, "Bear")]
        for cc, txt in heads:
            cell = ws.cell(row=r0, column=cc, value=txt)
            cell.font = F_SUB; cell.fill = FILL_SUB; cell.alignment = CENTER
        self.scen_rows: dict[str, int] = {}
        r = r0 + 1
        for name, label, fmt, vals in self.ASSUMPTIONS:
            ws.cell(row=r, column=c0, value=label).font = F_LBL
            for cc, case in ((self.scen_bull, "Bull"), (self.scen_base, "Base"), (self.scen_bear, "Bear")):
                cell = ws.cell(row=r, column=cc, value=vals[case])
                cell.number_format = fmt
                cell.font = F_IN
            self.scen_rows[name] = r
            r += 1
        # widths
        ws.column_dimensions[get_column_letter(c0)].width = 30
        for cc in (self.scen_bull, self.scen_base, self.scen_bear):
            ws.column_dimensions[get_column_letter(cc)].width = 8

    def scen(self, name, col):
        """Return a formula fragment selecting the driver value for the active
        scenario, e.g. CHOOSE(MATCH($scen,{"Bull","Base","Bear"},0),Bull,Base,Bear)."""
        r = self.scen_rows[name]
        bull = f"${get_column_letter(self.scen_bull)}${r}"
        base = f"${get_column_letter(self.scen_base)}${r}"
        bear = f"${get_column_letter(self.scen_bear)}${r}"
        return f'CHOOSE(MATCH({self.scen_cell},{{"Bull","Base","Bear"}},0),{bull},{base},{bear})'

    # ------------------------------------------------------------------ #
    def _column_setup(self):
        ws = self.ws
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["A"].width = 2
        ws.column_dimensions[get_column_letter(LABEL_COL)].width = 40
        for c in self.columns:
            ws.column_dimensions[c.letter].width = 9.5 if not c.is_est else 10
        ws.column_dimensions[get_column_letter(self.notes_col)].width = 26
        for cc in (self.cagr5f_col, self.cagr5h_col, self.cagr10_col):
            ws.column_dimensions[get_column_letter(cc)].width = 12
        # now wire the segment revenue / OI estimate drivers (needed rows exist)
        self._wire_segment_estimates()

    def _wire_segment_estimates(self):
        """Fill FY26E–30E for segment revenue & operating income using drivers."""
        for bkey, gkey in (("US", "AS_revGrowth_US"), ("International", "AS_revGrowth_Intl")):
            rrow = self.rows[f"seg_{bkey}_rev"]
            orow = self.rows[f"seg_{bkey}_oi"]
            mkey = {"US": "AS_opMargin_US", "International": "AS_opMargin_Intl"}[bkey]
            for c in self.columns:
                if not c.is_est:
                    continue
                prev = self._prev(c)
                self._put(rrow, c.idx, f"={prev.letter}{rrow}*(1+{self.scen(gkey, c)})", fmt=NUM, font=F_FX)
                self._put(orow, c.idx, f"={c.letter}{rrow}*{self.scen(mkey, c)}", fmt=NUM, font=F_FXB)

    # ================================================================== #
    # COVER
    # ================================================================== #
    def _cover(self):
        ws = self.wb.create_sheet("Cover")
        self.wb.move_sheet("Cover", -(len(self.wb.sheetnames) - 1))
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["A"].width = 3
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 66
        ws.cell(row=2, column=2, value="COPART, INC.").font = Font(name="Calibri", size=22, bold=True, color=NAVY)
        ws.cell(row=3, column=2, value="SEC-Filings 3-Statement Financial Model — 15-Year History + 5-Year Forecast").font = Font(size=12, color=GREY)
        meta = [
            ("Ticker / Exchange", "CPRT · Nasdaq"),
            ("SEC CIK", "0000900075"),
            ("Fiscal year end", "July 31"),
            ("Currency / units", "US$ millions (except per-share and share counts)"),
            ("Data source", "SEC EDGAR — Forms 10-K & 10-Q, XBRL (data.sec.gov). No non-SEC inputs except the manual valuation share price."),
            ("Reported segments", "United States · International"),
            ("Historical coverage", f"FY{self.hist_fys[0]}–FY{self.hist_fys[-1]} (annual + Q1/Q2/1H/Q3/Q4)"),
            ("Forecast", f"FY{self.est_fys[0]}E–FY{self.est_fys[-1]}E (driver-based, scenario toggle)"),
        ]
        r = 5
        for k, v in meta:
            kc = ws.cell(row=r, column=2, value=k); kc.font = F_LBLB; kc.fill = PatternFill("solid", fgColor="D9E1F2")
            vc = ws.cell(row=r, column=3, value=v); vc.font = F_LBL; vc.alignment = LEFTW
            r += 1
        r += 1
        ws.cell(row=r, column=2, value="Worksheets").font = F_SEC
        for cc in (2, 3):
            ws.cell(row=r, column=cc).fill = FILL_SEC
        ws.cell(row=r, column=3).font = F_SEC
        r += 1
        for name, desc in [
            ("Model", "Full model — segment P&L, income statement, cash flow, balance sheet, ratios, valuation; historicals (formulas) + FY26E–30E estimates."),
            ("Bull / Base / Bear", "Scenario P&L summary linked to the Model scenario toggle."),
            ("DCF", "Unlevered DCF built off the model's forecast free cash flow."),
        ]:
            ws.cell(row=r, column=2, value=name).font = F_LBLB
            ws.cell(row=r, column=3, value=desc).font = F_LBL
            ws.cell(row=r, column=3).alignment = LEFTW
            r += 1
        r += 1
        disc = ("Colour key: blue = as-reported figure taken directly from Copart's SEC filings; "
                "black = live Excel formula; pale-yellow columns = forecast years driven by the "
                "Assumptions / scenario table on the Model tab. Segment operating income is reported "
                "by Copart from ~FY2016 (two reportable segments); earlier years reflect geographic "
                "revenue disclosure as filed. For research/education only — not investment advice.")
        dc = ws.cell(row=r, column=2, value=disc); dc.font = F_NOTE_I; dc.alignment = LEFTW
        ws.merge_cells(start_row=r, start_column=2, end_row=r + 4, end_column=3)

    # ================================================================== #
    def _scenario_summary(self):
        ws = self.wb.create_sheet("Bull-Base-Bear")
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["B"].width = 34
        ws.cell(row=2, column=2, value="COPART — Bull / Base / Bear P&L Summary").font = F_TITLE
        ws.cell(row=3, column=2, value="Linked to Model — toggle scenario via the Model tab.").font = F_NOTE_I
        last_hist = self.fycol[self.hist_fys[-1]].letter
        est_letters = [self.estcol[fy].letter for fy in self.est_fys]
        heads = [f"FY{self.hist_fys[-1]}A"] + [f"FY{fy}E" for fy in self.est_fys]
        cols = [last_hist] + est_letters
        for i, h in enumerate(heads):
            cell = ws.cell(row=5, column=3 + i, value=h)
            cell.font = F_SUB; cell.fill = FILL_SUB; cell.alignment = CENTER
        lines = [("Revenue", "revenue", NUM), ("Operating income", "operating_income", NUM),
                 ("Net income", "net_income", NUM), ("EPS — diluted ($)", "eps_diluted", EPSF),
                 ("Free cash flow", "fcf", NUM)]
        r = 6
        for label, key, fmt in lines:
            ws.cell(row=r, column=2, value=label).font = F_LBL
            mrow = self.rows[key]
            for i, cl in enumerate(cols):
                cell = ws.cell(row=r, column=3 + i, value=f"=Model!{cl}{mrow}")
                cell.number_format = fmt; cell.font = F_FX
            r += 1
        ws.cell(row=r + 1, column=2, value="Active scenario:").font = F_LBLB
        ws.cell(row=r + 1, column=3, value=f"=Model!{self.scen_cell}").font = F_INB

    # ================================================================== #
    def _dcf(self):
        ws = self.wb.create_sheet("DCF")
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["B"].width = 36
        for cc in range(3, 9):
            ws.column_dimensions[get_column_letter(cc)].width = 12
        ws.cell(row=2, column=2, value="COPART — Unlevered DCF (off model forecast FCF)").font = F_TITLE
        ws.cell(row=3, column=2, value="Free cash flow linked from the Model forecast columns. Assumptions in blue are editable.").font = F_NOTE_I
        # assumptions
        ass = [("WACC", 0.09, PCT), ("Terminal growth (g)", 0.03, PCT)]
        r = 5
        self._dcf_ass = {}
        for label, val, fmt in ass:
            ws.cell(row=r, column=2, value=label).font = F_LBLB
            cell = ws.cell(row=r, column=3, value=val); cell.number_format = fmt; cell.font = F_IN
            self._dcf_ass[label] = r
            r += 1
        r += 1
        # year headers
        est_letters = [self.estcol[fy].letter for fy in self.est_fys]
        for i, fy in enumerate(self.est_fys):
            cell = ws.cell(row=r, column=3 + i, value=f"FY{fy}E")
            cell.font = F_SUB; cell.fill = FILL_SUB; cell.alignment = CENTER
        fcf_row = r + 1
        ws.cell(row=fcf_row, column=2, value="Free cash flow (US$m)").font = F_LBL
        for i, cl in enumerate(est_letters):
            c = ws.cell(row=fcf_row, column=3 + i, value=f"=Model!{cl}{self.rows['fcf']}")
            c.number_format = NUM; c.font = F_FX
        # discount factor
        wacc = f"$C${self._dcf_ass['WACC']}"
        df_row = fcf_row + 1
        ws.cell(row=df_row, column=2, value="Discount factor").font = F_LBL
        for i in range(len(est_letters)):
            col = get_column_letter(3 + i)
            c = ws.cell(row=df_row, column=3 + i, value=f"=1/(1+{wacc})^{i+1}")
            c.number_format = "0.000"; c.font = F_FX
        pv_row = df_row + 1
        ws.cell(row=pv_row, column=2, value="PV of FCF").font = F_LBL
        for i in range(len(est_letters)):
            col = get_column_letter(3 + i)
            c = ws.cell(row=pv_row, column=3 + i, value=f"={col}{fcf_row}*{col}{df_row}")
            c.number_format = NUM; c.font = F_FX
        # terminal value
        g = f"$C${self._dcf_ass['Terminal growth (g)']}"
        last = get_column_letter(3 + len(est_letters) - 1)
        rr = pv_row + 2
        ws.cell(row=rr, column=2, value="Terminal value (Gordon)").font = F_LBLB
        tv = ws.cell(row=rr, column=3, value=f"={last}{fcf_row}*(1+{g})/({wacc}-{g})")
        tv.number_format = NUM; tv.font = F_FX
        ws.cell(row=rr + 1, column=2, value="PV of terminal value").font = F_LBL
        ws.cell(row=rr + 1, column=3, value=f"=C{rr}*{last}{df_row}").number_format = NUM
        ws.cell(row=rr + 1, column=3).font = F_FX
        ws.cell(row=rr + 2, column=2, value="Enterprise value").font = F_LBLB
        ws.cell(row=rr + 2, column=3, value=f"=SUM({get_column_letter(3)}{pv_row}:{last}{pv_row})+C{rr+1}").number_format = NUM
        ws.cell(row=rr + 2, column=3).font = F_FXB
        ws.cell(row=rr + 3, column=2, value="− Net debt (FY latest, Model)").font = F_LBL
        ws.cell(row=rr + 3, column=3, value=f"=Model!{self.fycol[self.hist_fys[-1]].letter}{self.rows['ndebt']}").number_format = NUM
        ws.cell(row=rr + 3, column=3).font = F_FX
        ws.cell(row=rr + 4, column=2, value="Equity value").font = F_LBLB
        ws.cell(row=rr + 4, column=3, value=f"=C{rr+2}-C{rr+3}").number_format = NUM
        ws.cell(row=rr + 4, column=3).font = F_FXB
        ws.cell(row=rr + 5, column=2, value="÷ Diluted shares (m, FY latest)").font = F_LBL
        ws.cell(row=rr + 5, column=3, value=f"=Model!{self.fycol[self.hist_fys[-1]].letter}{self.rows['sh_diluted']}").number_format = NUM
        ws.cell(row=rr + 5, column=3).font = F_FX
        ws.cell(row=rr + 6, column=2, value="Implied value per share ($)").font = F_LBLB
        ws.cell(row=rr + 6, column=3, value=f"=C{rr+4}/C{rr+5}").number_format = EPSF
        ws.cell(row=rr + 6, column=3).font = F_FXB
