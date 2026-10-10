"""Bull-Base-Bear, DCF and Charts tabs (layouts mirror the MLM model)."""
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.drawing.text import CharacterProperties, Font as DFont, ParagraphProperties
from openpyxl.styles import Alignment
from openpyxl.utils import column_index_from_string, get_column_letter

from .framework import (BLACK, BLUE, CREAM, DARK, FMT_EPS, FMT_NUM, FMT_PCT, FMT_PCT0, FMT_SHR, FMT_X, GREEN, LIGHT,
                        MID, WHITE, YELLOW, fill, font, put_comment)

GREYF = "595959"

# ------------------------------------------------------------------------------------------------
# Bull / Base / Bear
# ------------------------------------------------------------------------------------------------
BBB_ROWS = [
    (9, "Revenue", "revenue", FMT_NUM, "main"),
    (10, "   Revenue y/y %", None, FMT_PCT0, "yoy:9"),
    (11, "   Revenue y/y % at constant exchange rates", "gr_cc", FMT_PCT, "nocagr"),
    (12, "Recurring Operating Income", "roi", FMT_NUM, "main"),
    (13, "   Recurring operating margin %", None, FMT_PCT, "margin:12:9:mg_roi"),
    (15, "Operating Income (IFRS)", "op_inc", FMT_NUM, "main"),
    (16, "   Operating income y/y %", None, FMT_PCT0, "yoy:15"),
    (17, "   Operating margin (IFRS) %", None, FMT_PCT, "margin:15:9:mg_oi"),
    (19, "Recurring Net Income (attributable; excl. non-recurring & French exceptional contribution)", "b2_rni",
     FMT_NUM, "main"),
    (21, "FDSO (m)", "sh_dil", FMT_SHR, "main"),
    (23, "Recurring EPS — Diluted (€)", "b2_eps", FMT_EPS, "main"),
    (24, "   EPS y/y %", None, FMT_PCT0, "yoy:23"),
    (31, "Adjusted Free Cash Flow", "afcf", FMT_NUM, "main"),
    (32, "   FCF %", None, FMT_PCT, "margin:31:9:afcf_m"),
    (33, "   FCF / share (€)", None, FMT_EPS, "div:31:21"),
    (35, "EBITDA (IFRS 16)", "ebitda", FMT_NUM, "main"),
    (36, "   EBITDA margin %", None, FMT_PCT, "margin:35:9:mg_ebitda"),
    (38, "Net Debt (negative = net cash)", "l_nd", FMT_NUM, "nocagr"),
    (39, "   Net Debt / EBITDA (x)", None, FMT_X, "div:38:35"),
    (41, "ROIC", "roic", FMT_PCT, "ratio"),
    (42, "RONTA", "ronta", FMT_PCT, "ratio"),
]
PE = {"B": 34.0, "N": 42.0, "Z": 27.0}   # Base / Bull / Bear P/E on recurring EPS


def write_bbb(wb, cols, rowmap):
    ws = wb.create_sheet("Bull-Base-Bear")
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 60
    widths = {"A": 2.14, "B": 63.86, "I": 13.29, "M": 3.86, "N": 63.86, "U": 13.29, "Y": 3.86, "Z": 63.86,
              "AG": 13.29}
    for L, w in widths.items():
        ws.column_dimensions[L].width = w
    for a, b in (("C", "H"), ("O", "T"), ("AA", "AF")):
        for i in range(column_index_from_string(a), column_index_from_string(b) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 11.86
    for a, b in (("J", "L"), ("V", "X"), ("AH", "AJ")):
        for i in range(column_index_from_string(a), column_index_from_string(b) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 12.57
    ws["B2"] = "Hermès International (RMS) — Bull / Base / Bear Case P&L Summary"
    ws["B2"].font = font(16, True, color=DARK)
    ws["B3"] = ("Adjusted figures (Hermès APMs: recurring operating income, adjusted free cash flow, restated net cash; "
                "recurring net income / EPS and EBITDA = model bridges) · EUR millions · Live panel linked to Model — "
                "toggle scenario via Model!" + cols.NOTES + "2. Bull and Bear panels are value snapshots generated from "
                "the Model with the switch set to each case.")
    ws["B3"].font = font(10, color=GREYF)
    ws["J2"], ws["J3"] = "Share price (€):", "As of:"
    for a in ("J2", "J3"):
        ws[a].font = font(12, True, color=WHITE)
        ws[a].fill = fill(DARK)
    ws["K2"] = f"=Model!${cols.annual(2026).L}${rowmap['px']}"
    ws["K2"].font, ws["K2"].fill, ws["K2"].number_format = font(12, True, color=GREEN), fill(CREAM), "#,##0.00"
    ws["K3"] = "=TODAY()"
    ws["K3"].number_format = "dd-mmm-yy"
    years = [2025, 2026, 2027, 2028, 2029, 2030]
    hist_annual = [c for c in cols.list if c.kind in ("A", "Y")]
    panels = [("B", "Scenario:", f"=Model!${cols.NOTES}$2", None), ("N", "Scenario:", "Bull", "Bull"),
              ("Z", "Scenario:", "Bear", "Bear")]
    for (start, lab, scn, snap) in panels:
        s = column_index_from_string(start)
        C = lambda i: get_column_letter(s + i)     # noqa: E731
        ws[f"{C(0)}5"] = lab
        ws[f"{C(1)}5"] = scn
        if snap is None:
            ws[f"{C(0)}5"].font, ws[f"{C(0)}5"].fill = font(12, True, color=WHITE), fill(DARK)
            ws[f"{C(1)}5"].font, ws[f"{C(1)}5"].fill = font(12, True, color=DARK), fill(LIGHT)
        else:
            ws[f"{C(0)}5"].font = font(12, True)
            ws[f"{C(1)}5"].font, ws[f"{C(1)}5"].fill = font(12, True, color=GREEN), fill(YELLOW)
            ws[f"{C(2)}5"] = f"Snapshot (values) — Model run with switch = {snap}"
            ws[f"{C(2)}5"].font = font(10, color=GREYF)
        ws[f"{C(0)}7"] = "(EURm, except EPS and shares)"
        ws[f"{C(0)}7"].font, ws[f"{C(0)}7"].fill = font(9, True, color=WHITE), fill(DARK)
        heads = ["2025A"] + [f"{y}E" for y in years[1:]] + ["25-'30 CAGR", "LT Hist Avg", "LT Hist Min", "LT Hist Max"]
        for i, h in enumerate(heads):
            cell = ws[f"{C(1 + i)}7"]
            cell.value = h
            cell.font = font(11, True, color=WHITE)
            cell.fill = fill(MID if i >= 7 else DARK)
            cell.alignment = Alignment(horizontal="center")
        for (r, lab, key, fmt, kind) in BBB_ROWS:
            lc = ws[f"{C(0)}{r}"]
            lc.value = lab
            main = kind in ("main", "nocagr", "ratio")
            lc.font = font(12, main, color=DARK if main else GREYF)
            for i, y in enumerate(years):
                cell = ws[f"{C(1 + i)}{r}"]
                mc = cols.annual(y)
                f = None
                if key:
                    f = f"=Model!{mc.L}{rowmap[key]}"
                elif kind.startswith("yoy"):
                    base = int(kind.split(":")[1])
                    f = None if i == 0 else f'=IFERROR({C(1 + i)}{base}/{C(i)}{base}-1,"")'
                elif kind.startswith(("margin", "div")):
                    parts = kind.split(":")
                    f = f'=IFERROR({C(1 + i)}{parts[1]}/{C(1 + i)}{parts[2]},"")'
                if f:
                    cell.value = f
                cell.number_format = fmt
                cell.font = font(12, main, color=GREEN if key else GREYF)
                if snap is None:
                    cell.fill = fill("F5F5F5" if i == 0 else CREAM)
            if kind == "main":
                cg = ws[f"{C(7)}{r}"]
                cg.value = f'=IFERROR(({C(6)}{r}/{C(1)}{r})^(1/5)-1,"n/m")'
                cg.number_format = FMT_PCT0
                cg.font = font(12, True)
                cg.fill = fill("E8EDE9")
            if kind.startswith("margin") or kind == "ratio":
                mk = kind.split(":")[3] if kind.startswith("margin") else key
                refs = ",".join(f"Model!{c.L}{rowmap[mk]}" for c in hist_annual)
                for j, fn in enumerate(("AVERAGE", "MIN", "MAX")):
                    cc = ws[f"{C(8 + j)}{r}"]
                    cc.value = f'=IFERROR({fn}({refs}),"")'
                    cc.number_format = fmt
                    cc.font = font(12, color=GREYF)
                    cc.fill = fill("F0F2F0")
        for r, t in ((26, "P / E (x) — assumed (recurring EPS)"), (27, "Price Target (€)"),
                     (28, "   Upside / (Downside) vs current"), (29, "IRR (to Dec-Y-1)"), (34, "   FCF Yield (on PT)"),
                     (44, "Implied Market Cap (EURm)"), (45, "(+) Net Debt & NCI"),
                     (46, "Implied Enterprise Value (EURm)"), (47, "Implied EV / EBITDA (x)")):
            ws[f"{C(0)}{r}"] = t
            ws[f"{C(0)}{r}"].font = font(12, color=GREYF)
        ws[f"{C(0)}27"].font, ws[f"{C(0)}27"].fill = font(12, True, color=WHITE), fill(DARK)
        ws[f"{C(0)}29"].font, ws[f"{C(0)}29"].fill = font(12, True, color=DARK), fill(LIGHT)
        for i in range(3, 6):
            col, prev, y = C(1 + i), C(i), years[i]
            mc = cols.annual(y)
            pe_cell = ws[f"{col}26"]
            pe_cell.value = PE[start] if i == 3 else f"={prev}26"
            pe_cell.font, pe_cell.fill, pe_cell.number_format = font(12, True, color=BLUE), fill("FFF8DC"), "0.0\\x"
            ws[f"{col}27"] = f"={col}26*{col}23"
            ws[f"{col}27"].number_format = FMT_NUM
            ws[f"{col}27"].font, ws[f"{col}27"].fill = font(12, True, color=WHITE), fill(DARK)
            ws[f"{col}28"] = f'=IFERROR({col}27/$K$2-1,"")'
            ws[f"{col}28"].number_format = FMT_PCT0
            ws[f"{col}29"] = f'=IFERROR(({col}27/$K$2)^(1/((DATE({y}-1,12,31)-$K$3)/365.25))-1,"")'
            ws[f"{col}29"].number_format = FMT_PCT0
            ws[f"{col}29"].font, ws[f"{col}29"].fill = font(12, True, color=DARK), fill(LIGHT)
            ws[f"{col}34"] = f'=IFERROR({col}33/{col}$27,"")'
            ws[f"{col}34"].number_format = FMT_PCT
            ws[f"{col}44"] = f"={col}27*{col}21"
            ws[f"{col}45"] = f"={col}38+Model!{mc.L}{rowmap['v_nci']}"
            ws[f"{col}46"] = f"={col}44+{col}45"
            ws[f"{col}47"] = f'=IFERROR({col}46/{col}35,"")'
            for r in (44, 45, 46):
                ws[f"{col}{r}"].number_format = FMT_NUM
            ws[f"{col}47"].number_format = FMT_X
            for r in (28, 34, 44, 45, 46, 47):
                ws[f"{col}{r}"].font = font(12, color=GREYF)
    put_comment(ws["N26"], "Assumed exit P/E on recurring diluted EPS. Hermès traded at ~45–55x forward earnings in "
                           "2021–25; €1,299.50 (2-Oct-26) ≈ 28x 2026E recurring EPS (Base).")
    return ws


# ------------------------------------------------------------------------------------------------
# DCF
# ------------------------------------------------------------------------------------------------
def write_dcf(wb, cols, rowmap):
    ws = wb.create_sheet("DCF")
    ws.sheet_view.zoomScale = 60
    ws.column_dimensions["A"].width = 10.57
    ws.column_dimensions["B"].width = 50
    for L in "CDEFGHIJKLMNO":
        ws.column_dimensions[L].width = 12.57
    ws.column_dimensions["P"].width = 13.29

    def M(key, y):
        return f"Model!{cols.annual(y).L}{rowmap[key]}"

    def hdr(cell, text, color=MID, sz=12):
        ws[cell] = text
        ws[cell].font = font(sz, True, color=WHITE)
        ws[cell].fill = fill(color)

    def note(cell, text):
        ws[cell] = text
        ws[cell].font = font(10, color=GREYF)

    hdr("B2", "DCF VALUATION — HERMÈS INTERNATIONAL (RMS)", DARK, 14)
    hdr("B4", "1. WACC BUILD")
    inputs = [(5, "Risk-free rate (EUR 10Y govt)", 0.030, "0.00%",
               "Assumption (~blend of 10Y Bund / OAT yields); update to market"),
              (6, "Equity risk premium", 0.055, "0.00%", "Euro-area implied ERP ~5–6% (Damodaran)"),
              (7, "Levered beta", 0.90, "0.00", "Luxury peers (LVMH, Kering, Richemont, Prada) ~0.9–1.2; Hermès' "
                                              "pricing power and family-controlled shareholder base dampen cyclicality"),
              (8, "Cost of equity", "=C5+C7*C6", "0.00%", None),
              (9, "Pre-tax cost of debt", 0.035, "0.00%", "No financial debt (net cash €12.9bn at 30-Jun-26); "
                                                       "notional IG euro cost"),
              (10, "Tax rate", 0.285, "0.00%", "Model 2027E+ effective tax rate (excl. the French exceptional "
                                               "contribution)"),
              (11, "After-tax cost of debt", "=C9*(1-C10)", "0.00%", None),
              (12, "Target D/V", 0.0, "0.00%", "Net cash balance sheet; lease liabilities (~€2.3bn) treated as "
                                              "operating (ROU depreciation kept in EBIT)"),
              (13, "WACC", "=C8*(1-C12)+C11*C12", "0.00%", None)]
    for r, lab, v, fmt, nt in inputs:
        ws[f"B{r}"] = lab
        ws[f"C{r}"] = v
        ws[f"C{r}"].number_format = fmt
        ws[f"B{r}"].font = font(12, r == 13)
        if isinstance(v, str):
            ws[f"C{r}"].font = font(12, r == 13)
            if r == 13:
                ws[f"C{r}"].fill = fill(LIGHT)
        else:
            ws[f"C{r}"].font, ws[f"C{r}"].fill = font(12, color=BLUE), fill(CREAM)
        if nt:
            note(f"D{r}", nt)
    ws["B15"], ws["C15"] = "Valuation date (live)", "=TODAY()"
    ws["C15"].number_format = "dd-mmm-yy"
    note("D15", "Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end")
    hdr("B16", "2. UNLEVERED FREE CASH FLOW BUILD (EURm)")
    yrs = list(range(2026, 2036))
    colL = list("DEFGHIJKLM")
    for L, y in zip(colL, yrs):
        hdr(f"{L}17", f"{y}E", DARK)
    hdr("N17", "Terminal", DARK)
    labels = {18: "Recurring operating income = adjusted EBIT (Model)", 19: "   y/y %",
              20: "(+) Non-recurring items (Model; nil in forecast)", 21: "× (1 − tax rate)",
              22: "NOPAT  =  (Adjusted EBIT + non-recurring) × (1 − t)",
              23: "plus D&A of PP&E and intangibles (ROU depreciation kept in EBIT as lease-cost proxy)",
              24: "− Operating investments and acquisitions", 25: "− Δ Working capital (CF statement)",
              26: "Unlevered FCF", 27: "   y/y %", 28: "Terminal Value (Gordon Growth)",
              29: "   memo: operating investments only (fade years carry no acquisitions)"}
    for r, t in labels.items():
        ws[f"B{r}"] = t
    ws["B29"].font = font(10, color=GREYF)
    for i, (L, y) in enumerate(zip(colL, yrs)):
        if y <= 2030:
            ws[f"{L}18"] = f"={M('roi', y)}"
            ws[f"{L}20"] = f"={M('nonrec', y)}"
            ws[f"{L}23"] = f"={M('da_fixed', y)}"
            ws[f"{L}29"] = f"={M('cf_capex', y)}"
            ws[f"{L}24"] = f"={L}29+{M('cf_acq', y)}"
            ws[f"{L}25"] = f"={M('cf_wc', y)}"
            for r in (18, 20, 23, 24, 25, 29):
                ws[f"{L}{r}"].font = font(12, color=GREEN)
        else:
            p = colL[i - 1]
            for r in (18, 20, 23, 25, 29):
                ws[f"{L}{r}"] = f"={p}{r}*(1+{L}$31)"
            ws[f"{L}24"] = f"={L}29"
        ws[f"{L}21"] = "=1-$C$10"
        ws[f"{L}21"].number_format = "0.0%"
        ws[f"{L}22"] = f"=({L}18+{L}20)*{L}21"
        ws[f"{L}26"] = f"={L}22+{L}23+{L}24+{L}25"
        if i > 0:
            ws[f"{L}19"] = f'=IFERROR({L}18/{colL[i - 1]}18-1,"")'
            ws[f"{L}27"] = f'=IFERROR({L}26/{colL[i - 1]}26-1,"")'
            ws[f"{L}19"].number_format = ws[f"{L}27"].number_format = "0.0%"
        for r in (18, 20, 22, 23, 24, 25, 26, 29):
            ws[f"{L}{r}"].number_format = FMT_NUM
        ws[f"{L}26"].font, ws[f"{L}26"].fill = font(12, True), fill(LIGHT)
    ws["B26"].font, ws["B26"].fill = font(12, True), fill(LIGHT)
    ws["N26"] = "=M26*(1+$C$32)"
    ws["N28"] = "=N26/($C$13-$C$32)"
    for a in ("N26", "N28"):
        ws[a].number_format = FMT_NUM
        ws[a].font, ws[a].fill = font(12, True), fill(LIGHT)
    ws["B31"], ws["B32"] = "Fade-period growth (2031E–35E)", "Terminal growth rate"
    ws["I31"], ws["M31"] = 0.07, 0.045
    for L in "JKL":
        ws[f"{L}31"] = "=" + f"{chr(ord(L) - 1)}31+($M$31-$I$31)/(COLUMNS($I$31:$M$31)-1)"
    for L in "IJKLM":
        ws[f"{L}31"].number_format = "0.0%"
        ws[f"{L}31"].font = font(12, color=BLUE if L in "IM" else BLACK)
        if L in "IM":
            ws[f"{L}31"].fill = fill(CREAM)
    ws["C32"] = 0.030
    ws["C32"].number_format = "0.0%"
    ws["C32"].font, ws["C32"].fill = font(12, True, color=BLUE), fill(YELLOW)
    ws["B34"], ws["B35"], ws["B36"] = "Discount period (years)", "Discount factor", "PV of UFCF"
    for L, y in zip(colL, yrs):
        ws[f"{L}34"] = f"=(DATE({y},12,31)-$C$15)/365.25"
        ws[f"{L}35"] = f"=1/(1+$C$13)^{L}34"
        ws[f"{L}36"] = f"={L}26*{L}35"
        ws[f"{L}34"].number_format, ws[f"{L}35"].number_format, ws[f"{L}36"].number_format = "0.00", "0.000", FMT_NUM
    ws["N34"], ws["N35"], ws["N36"] = "=M34", "=1/(1+$C$13)^N34", "=N28*N35"
    ws["N34"].number_format, ws["N35"].number_format, ws["N36"].number_format = "0.00", "0.000", FMT_NUM
    note("D37", "Recurring operating income expenses free-share plans and right-of-use depreciation (a proxy for lease "
                "payments, so lease liabilities are not deducted as debt below). 2026E UFCF is the full calendar year "
                "(H1/26 actual + H2/26E); the 2026E column is discounted to 31-Dec-26.")
    # implied ROIC
    hdr("B39", "Implied ROIC & incremental ROIC (EURm)")
    for L in colL:
        ws[f"{L}39"] = f"={L}17"
        ws[f"{L}39"].font = font(12, True)
    rows = {40: "NOPAT (row 22)", 41: "Net investment  =  NOPAT − UFCF", 42: "Opening invested capital",
            43: "Closing invested capital", 44: "Implied ROIC  =  NOPAT / opening IC",
            45: "Reinvestment rate  =  net inv. / NOPAT", 46: "Incremental ROIC  =  Δ NOPAT / prior-yr net inv.",
            47: "Cumulative incremental ROIC 2026E–35E"}
    for r, t in rows.items():
        ws[f"B{r}"] = t
    for i, L in enumerate(colL):
        ws[f"{L}40"] = f"={L}22"
        ws[f"{L}41"] = f"={L}40-{L}26"
        ws[f"{L}42"] = f"={M('r_ic', 2025)}" if i == 0 else f"={colL[i - 1]}43"
        ws[f"{L}43"] = f"={L}42+{L}41"
        ws[f"{L}44"] = f'=IFERROR({L}40/{L}42,"")'
        ws[f"{L}45"] = f'=IFERROR({L}41/{L}40,"")'
        if i > 0:
            p = colL[i - 1]
            ws[f"{L}46"] = f'=IFERROR(({L}40-{p}40)/{p}41,"")'
        for r in (40, 41, 42, 43):
            ws[f"{L}{r}"].number_format = FMT_NUM
        for r in (44, 45, 46):
            ws[f"{L}{r}"].number_format = "0.0%"
    ws["C47"] = '=IFERROR((M40-D40)/SUM(D41:L41),"")'
    ws["C47"].number_format = "0.0%"
    note("D48", "Opening IC = Model 2025A invested capital (equity + lease liabilities − restated net cash), rolled "
                "forward with net investment. Hermès' book IC is small relative to NOPAT (ROIC > 60%).")
    hdr("B49", "3. VALUATION SUMMARY")
    summ = [(50, "Sum of PV (explicit + fade)", "=SUM(D36:M36)", FMT_NUM),
            (51, "PV of Terminal Value", "=N36", FMT_NUM),
            (52, "Enterprise Value", "=C50+C51", FMT_NUM),
            (53, "Less: net debt (Model 2026E YE; negative = net cash)", f"={M('l_nd', 2026)}", FMT_NUM),
            (54, "Less: non-controlling interests (Model 2026E)", f"={M('v_nci', 2026)}", FMT_NUM),
            (55, "Equity Value", "=C52-C53-C54", FMT_NUM),
            (56, "Diluted shares (m, Model 2026E)", f"={M('sh_dil', 2026)}", FMT_SHR),
            (57, "Implied share price (€)", "=C55/C56", "#,##0.00"),
            (58, "Current share price (€)", f"={M('px', 2026)}", "#,##0.00"),
            (59, "Implied upside / (downside)", "=C57/C58-1", FMT_PCT)]
    for r, lab, f, fmt in summ:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = fmt
        ws[f"B{r}"].font = font(12, r in (52, 55, 57))
        if r == 57:
            ws[f"C{r}"].font, ws[f"C{r}"].fill = font(12, True, color=WHITE), fill(DARK)
        elif r in (52, 55):
            ws[f"C{r}"].font, ws[f"C{r}"].fill = font(12, True), fill(LIGHT)
    ws["B60"] = ("Required discount to DCF value for target IRR (discount closes over horizon; value compounds at "
                 "WACC)")
    ws["C60"] = "=1-((1+C13)/(1+F60))^F61"
    ws["C60"].number_format = FMT_PCT
    ws["E60"], ws["F60"] = "Target IRR", 0.12
    ws["B61"] = "Max entry price for target IRR (€) — % vs. current share price shown right"
    ws["C61"], ws["D61"] = "=C57*(1-C60)", "=C61/C58-1"
    ws["C61"].number_format, ws["D61"].number_format = "#,##0.00", FMT_PCT
    ws["E61"], ws["F61"] = "Years for discount to close", 3
    ws["F60"].number_format = FMT_PCT
    for a in ("F60", "F61"):
        ws[a].font, ws[a].fill = font(12, color=BLUE), fill(CREAM)
    hdr("B64", "4. SENSITIVITY: IMPLIED PRICE (€) — WACC × Terminal Growth")
    ws["B65"], ws["C65"] = "WACC step (across)", 0.005
    ws["B66"], ws["C66"] = "Terminal growth step (down)", 0.005
    for a in ("C65", "C66"):
        ws[a].number_format = "0.00%"
        ws[a].font = font(12, color=BLUE)
    ws["B67"] = "g (down) / WACC"
    ws["F67"] = "=$C$13"
    ws["E67"], ws["D67"] = "=F67-$C$65", "=E67-$C$65"
    ws["G67"], ws["H67"] = "=F67+$C$65", "=G67+$C$65"
    for L in "DEFGH":
        ws[f"{L}67"].number_format = "0.00%"
        ws[f"{L}67"].font = font(12, True)
    ws["B70"] = "=$C$32"
    ws["B69"], ws["B68"] = "=B70-$C$66", "=B69-$C$66"
    ws["B71"], ws["B72"] = "=B70+$C$66", "=B71+$C$66"
    for r in range(68, 73):
        ws[f"B{r}"].number_format = "0.00%"
        ws[f"B{r}"].font = font(12, True)
        for L in "DEFGH":
            ws[f"{L}{r}"] = (f'=IFERROR((SUMPRODUCT($D$26:$M$26/(1+{L}$67)^$D$34:$M$34)+($M$26*(1+$B{r})/({L}$67'
                             f'-$B{r}))/(1+{L}$67)^$M$34-$C$53-$C$54)/$C$56,"")')
            ws[f"{L}{r}"].number_format = "#,##0"
    ws["F70"].fill = fill(LIGHT)
    hdr("B75", "5. REVERSE DCF")
    note("B76", "To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C57 (implied price) to "
                "the current price (C58) by changing C32 (terminal growth) or the Model scenario levers (métier "
                "constant-currency growth, recurring operating margin).")
    hdr("B78", "6. MAUBOUSSIN EV / NOPAT — TWO-STAGE FRAMEWORK")
    note("B79", "EV/NOPAT  =  1/r  +  [g × (1 − r/ROIIC) / (r × (r − g))] × [1 − ((1+g)/(1+r))^N]")
    note("B80", 'Formula source: Mauboussin & Rappaport, "Expectations Investing" (2021); Counterpoint Global, "What '
                'Does a Price-Earnings Multiple Mean?" (2020).')
    hdr("B82", "Input")
    hdr("C82", "Value")
    hdr("D82", "Rationale (Hermès characteristics)")
    mi = [(83, "r  (Cost of capital / WACC)", "=$C$13", "Linked from Section 1 WACC build"),
          (84, "g  (NOPAT growth, Stage 1)", 0.08, "Model recurring operating income CAGR 2025–30E: high-single-digit "
                                                 "constant-currency growth, stable ~41% margin"),
          (85, "ROIIC  (Return on incremental invested capital)", 0.40,
           "Capacity growth (leather workshops, stores) earns very high returns: ROIC > 60% on book IC; incremental "
           "capex ~7% of sales"),
          (86, "N  (Years of value creation / CAP)", 20,
           "Scarcity-driven brand (waitlists, controlled capacity), 190-year heritage, family control (H51 ~66%), "
           "vertical integration in craftsmanship")]
    for r, lab, v, nt in mi:
        ws[f"B{r}"], ws[f"C{r}"] = lab, v
        note(f"D{r}", nt)
        ws[f"C{r}"].number_format = "0" if r == 86 else "0.00%"
        ws[f"C{r}"].font = font(12, color=BLACK if isinstance(v, str) else BLUE)
        if not isinstance(v, str):
            ws[f"C{r}"].fill = fill(CREAM)
    hdr("B88", "Calculation")
    hdr("C88", "Value")
    calc = [(89, "Steady-state component:  1 / r", "=1/C83"), (90, "Value-creation factor: 1 − r / ROIIC", "=1-C83/C85"),
            (91, "Growth multiplier: g × (1 − r/ROIIC) / (r × (r − g))", "=C84*C90/(C83*(C83-C84))"),
            (92, "Time decay: 1 − ((1+g)/(1+r))^N", "=1-((1+C84)/(1+C83))^C86"),
            (93, "PVGO component (growth value)", "=C91*C92"), (94, "Mauboussin EV / NOPAT (steady-state + PVGO)",
                                                               "=C89+C93")]
    for r, lab, f in calc:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = "0.00"
    ws["B94"].font, ws["C94"].font = font(12, True, color=WHITE), font(12, True, color=WHITE)
    ws["B94"].fill = ws["C94"].fill = fill(DARK)
    ws["C94"].number_format = "0.0\\x"
    hdr("B96", "VALUATION  —  Applied to 2028E NOPAT")
    hdr("C96", "EURm")
    val = [(97, "2028E recurring operating income (Model)", f"={M('roi', 2028)}"),
           (98, "(+) 2028E non-recurring items", f"={M('nonrec', 2028)}"),
           (99, "Tax rate (from WACC build)", "=$C$10"),
           (100, "2028E NOPAT  =  (ROI + non-recurring) × (1 − t)", "=(C97+C98)*(1-C99)"),
           (101, "× Mauboussin EV/NOPAT multiple", "=C94"), (102, "Implied Enterprise Value (2028E basis)", "=C100*C101"),
           (103, "Less: YE2027 net debt + NCI (Model)", f"={M('l_nd', 2027)}+{M('v_nci', 2027)}"),
           (104, "Implied Equity Value", "=C102-C103"), (105, "Diluted shares 2028E (m, Model)", f"={M('sh_dil', 2028)}"),
           (106, "Implied share price 2028 (€)", "=C104/C105"), (108, "Current share price (€)", "=C58"),
           (109, "Implied upside / (downside)", "=C106/C108-1")]
    for r, lab, f in val:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = (FMT_PCT if r in (99, 109) else ("0.0\\x" if r == 101 else
                                     ("#,##0.00" if r in (106, 108) else FMT_NUM)))
    hdr("B111", "MARKET-IMPLIED EV/NOPAT TODAY")
    hdr("C111", "EURm")
    mkt = [(112, "Current market cap (spot × diluted shares)", "=C58*C56"),
           (113, "Plus: YE2026 net debt & NCI", "=C53+C54"),
           (114, "Implied Enterprise Value (today)", "=C112+C113"),
           (115, "Hermès' market-implied EV/NOPAT (on 2028E NOPAT)", "=C114/C100"),
           (117, "Multiple gap (Mauboussin − Market)", "=C94-C115"), (118, "Implied re-rating headroom", "=C94/C115-1")]
    for r, lab, f in mkt:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = FMT_PCT if r == 118 else ("0.0\\x" if r in (115, 117) else FMT_NUM)
    return ws


# ------------------------------------------------------------------------------------------------
# Charts
# ------------------------------------------------------------------------------------------------
def _title(chart, text):
    chart.title = text
    cp = CharacterProperties(sz=1400, b=True, solidFill="000000", latin=DFont(typeface="Calibri"))
    chart.title.tx.rich.p[0].pPr = ParagraphProperties(defRPr=cp)
    for r in chart.title.tx.rich.p[0].r:
        r.rPr = cp


def write_charts(wb, cols, rowmap):
    ws = wb.create_sheet("Charts")
    ws.sheet_view.zoomScale = 70
    ws.column_dimensions["B"].width = 30
    ws["B2"] = "Hermès International — Historical Operating Performance (2009–2025)"
    ws["B2"].font = font(14, True)
    ws["B3"] = ("All historicals · EURm · Linked to Model. Growth decomposition = revenue growth at constant exchange "
                "rates (company-reported) and the currency / scope effect (reported − constant). EBITDA = recurring "
                "operating income + all D&A (IFRS 16 from 2019). Charts start in 2009, the first year with full financial statements (2006–08: key figures only).")
    ws["B3"].font = font(10, color=GREYF)
    yrs = list(range(2009, 2026))
    CL = [get_column_letter(3 + i) for i in range(len(yrs))]

    def yrow(r):
        for L, y in zip(CL, yrs):
            ws[f"{L}{r}"] = y if r == 7 else f"={L}7"
            ws[f"{L}{r}"].font, ws[f"{L}{r}"].fill = font(12, True, color=WHITE), fill(DARK)

    yrow(7)

    def line(r, lab, key, fmt, na=False, zero=False):
        ws[f"B{r}"] = lab
        for L, y in zip(CL, yrs):
            ref = f"Model!{cols.annual(y).L}{rowmap[key]}"
            ws[f"{L}{r}"] = (f"=IFERROR({ref}+0,0)" if zero else (f"=IFERROR({ref}+0,NA())" if na else f"={ref}"))
            ws[f"{L}{r}"].number_format = fmt
            ws[f"{L}{r}"].font = font(12, color=GREEN)

    line(8, "Constant-currency growth %", "cc_grp", FMT_PCT, zero=True)
    line(9, "Currency / scope effect %", "fx_grp", FMT_PCT, zero=True)
    yrow(11)
    line(12, "EBITDA", "ebitda", FMT_NUM, zero=True)
    line(13, "Recurring Operating Income", "roi", FMT_NUM)
    line(14, "EBITDA Margin %", "mg_ebitda", FMT_PCT, na=True)
    line(15, "Recurring Op. Margin %", "mg_roi", FMT_PCT)
    yrow(17)
    line(18, "ROIC", "roic", FMT_PCT, na=True)
    line(19, "RONTA", "ronta", FMT_PCT, na=True)
    line(20, "Recurring op. margin %", "mg_roi", FMT_PCT, na=True)
    line(21, "Adjusted FCF margin %", "afcf_m", FMT_PCT, na=True)

    n = len(yrs)
    cats = Reference(ws, min_col=3, max_col=2 + n, min_row=7)
    c1 = BarChart()
    c1.type, c1.grouping, c1.overlap = "col", "stacked", 100
    _title(c1, "Revenue Growth Decomposition: Constant-Currency Growth vs. Currency Effect, y/y %")
    for r, color in ((8, "2F3E46"), (9, "84A98C")):
        c1.add_data(Reference(ws, min_col=2, max_col=2 + n, min_row=r), titles_from_data=True, from_rows=True)
        c1.series[-1].graphicalProperties.solidFill = color
    c1.set_categories(cats)
    c1.y_axis.number_format = "0%"
    c1.width, c1.height = 15, 7.5
    ws.add_chart(c1, "B23")

    c2 = BarChart()
    c2.type, c2.grouping = "col", "clustered"
    _title(c2, "EBITDA & Recurring Operating Income (EURm)")
    for r, color in ((12, "A8C5D6"), (13, "1F4E79")):
        c2.add_data(Reference(ws, min_col=2, max_col=2 + n, min_row=r), titles_from_data=True, from_rows=True)
        c2.series[-1].graphicalProperties.solidFill = color
    c2.set_categories(cats)
    c2.y_axis.number_format = "#,##0"
    l2 = LineChart()
    for r, color in ((14, "2F3E46"), (15, "C8553D")):
        l2.add_data(Reference(ws, min_col=2, max_col=2 + n, min_row=r), titles_from_data=True, from_rows=True)
        l2.series[-1].graphicalProperties.line.solidFill = color
    l2.y_axis.axId = 200
    l2.y_axis.number_format = "0%"
    l2.y_axis.crosses = "max"
    c2 += l2
    c2.width, c2.height = 15, 7.5
    ws.add_chart(c2, "B44")

    c3 = LineChart()
    _title(c3, "Returns Profile: ROIC, RONTA, Recurring Operating Margin & Adjusted FCF Margin")
    for r, color in ((18, "2F3E46"), (19, "84A98C"), (20, "1F4E79"), (21, "C8553D")):
        c3.add_data(Reference(ws, min_col=2, max_col=2 + n, min_row=r), titles_from_data=True, from_rows=True)
        c3.series[-1].graphicalProperties.line.solidFill = color
    c3.set_categories(cats)
    c3.y_axis.number_format = "0%"
    c3.width, c3.height = 15, 7.5
    ws.add_chart(c3, "B65")
    return ws
