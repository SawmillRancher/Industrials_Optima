"""Bull-Base-Bear, DCF and Charts tabs (layouts mirror the RBA / HII models)."""
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties, Font as DFont
from openpyxl.styles import Alignment

from .framework import (BLACK, BLUE, CREAM, DARK, FMT_EPS, FMT_NUM, FMT_PCT, FMT_PCT0, FMT_SHR, FMT_X, GREEN, LIGHT,
                        MID, WHITE, YELLOW, fill, font, put_comment)

GREYF = "595959"

# ------------------------------------------------------------------------------------------------
# Bull / Base / Bear
# ------------------------------------------------------------------------------------------------
BBB_ROWS = [
    # (row, label, model row key, fmt, kind)  kind: val | sub | cagr-able
    (9, "Net Sales", "net_sales", FMT_NUM, "main"),
    (10, "   Net sales y/y %", None, FMT_PCT0, "yoy:9"),
    (11, "   Organic growth %", "g_org", FMT_PCT, "nocagr"),
    (12, "Non-GAAP Operating Income", "o_cur", FMT_NUM, "main"),
    (13, "   Non-GAAP operating margin %", None, FMT_PCT, "margin:12:9:o_cur_m"),
    (15, "Operating Income (GAAP)", "op_income", FMT_NUM, "main"),
    (16, "   Operating income y/y %", None, FMT_PCT0, "yoy:15"),
    (17, "   Operating margin (GAAP) %", None, FMT_PCT, "margin:15:9:m_oi"),
    (19, "Non-GAAP Net Income (attributable to Teledyne)", "c_ni", FMT_NUM, "main"),
    (21, "FDSO (m)", "sh_dil", FMT_SHR, "main"),
    (23, "Non-GAAP EPS — Diluted ($)", "c_eps", FMT_EPS, "main"),
    (24, "   EPS y/y %", None, FMT_PCT0, "yoy:23"),
    (31, "Free Cash Flow", "fcf", FMT_NUM, "main"),
    (32, "   FCF %", None, FMT_PCT, "margin:31:9:fcf_m"),
    (33, "   FCF / share ($)", None, FMT_EPS, "div:31:21"),
    (35, "Adjusted EBITDA (model)", "adj_ebitda", FMT_NUM, "main"),
    (36, "   Adjusted EBITDA margin %", None, FMT_PCT, "margin:35:9:m_ebitda"),
    (38, "Net Debt", "l_nd", FMT_NUM, "nocagr"),
    (39, "   Net Debt / Adjusted EBITDA (x)", None, FMT_X, "div:38:35"),
    (41, "ROIC", "roic", FMT_PCT, "ratio"),
    (42, "RONTA", "ronta", FMT_PCT, "ratio"),
]


def write_bbb(wb, cols, rowmap, pe=(28.0, 25.0, 21.0)):
    ws = wb.create_sheet("Bull-Base-Bear")
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 50
    for L, w in {"A": 2, "B": 40, "C": 13, "I": 13.6, "J": 12.6, "N": 41.4, "O": 11.5, "Z": 41.4, "AA": 11.75}.items():
        ws.column_dimensions[L].width = w
    ws["B2"] = "Teledyne Technologies (TDY) — Bull / Base / Bear Case P&L Summary"
    ws["B2"].font = font(16, True, color=DARK)
    ws["B3"] = ("Non-GAAP figures (company current definition) · USD millions · Live panel linked to Model — toggle scenario via "
                "Model!" + cols.NOTES + "2. Bull and Bear panels are value snapshots generated from the Model with the "
                "switch set to each case.")
    ws["B3"].font = font(10, color=GREYF)
    ws["J2"], ws["J3"] = "Share price ($):", "As of:"
    for a in ("J2", "J3"):
        ws[a].font = font(12, True, color=WHITE)
        ws[a].fill = fill(DARK)
    px = f"Model!${cols.annual(2026).L}${rowmap['px']}"
    ws["K2"] = f"={px}"
    ws["K2"].font, ws["K2"].fill, ws["K2"].number_format = font(12, True, color=GREEN), fill(CREAM), "#,##0.00"
    ws["K3"] = "=TODAY()"
    ws["K3"].number_format = "dd-mmm-yy"
    years = [2025, 2026, 2027, 2028, 2029, 2030]
    hist_annual = [c for c in cols.list if c.kind in ("A", "Y")]
    panels = [("B", "Scenario:", f"=Model!{cols.NOTES}2", None), ("N", "Scenario:", "Bull", "Bull"),
              ("Z", "Scenario:", "Bear", "Bear")]
    from openpyxl.utils import column_index_from_string, get_column_letter
    snap_targets = {}
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
        ws[f"{C(0)}7"] = "(USDm, except EPS and shares)"
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
            lc.font = font(12, kind in ("main", "nocagr", "ratio"), color=DARK if kind in ("main", "nocagr", "ratio")
                           else GREYF)
            for i, y in enumerate(years):
                cell = ws[f"{C(1 + i)}{r}"]
                mc = cols.annual(y)
                if key:
                    f = f"=Model!{mc.L}{rowmap[key]}"
                elif kind.startswith("yoy"):
                    base = int(kind.split(":")[1])
                    f = None if i == 0 else f'=IFERROR({C(1 + i)}{base}/{C(i)}{base}-1,"")'
                elif kind.startswith("margin"):
                    _, a, b, _k = kind.split(":")
                    f = f'=IFERROR({C(1 + i)}{a}/{C(1 + i)}{b},"")'
                elif kind.startswith("div"):
                    _, a, b = kind.split(":")
                    f = f'=IFERROR({C(1 + i)}{a}/{C(1 + i)}{b},"")'
                if f:
                    cell.value = f
                    snap_targets[(start, r, i)] = f
                cell.number_format = fmt
                is_link = key is not None
                cell.font = font(12, kind in ("main", "nocagr", "ratio"), color=GREEN if is_link else GREYF)
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
        # valuation rows
        pe_col_val = {"B": pe[1], "N": pe[0], "Z": pe[2]}[start]
        ws[f"{C(0)}26"] = "P / E (x) — assumed (non-GAAP EPS)"
        ws[f"{C(0)}27"] = "Price Target ($)"
        ws[f"{C(0)}28"] = "   Upside / (Downside) vs current"
        ws[f"{C(0)}29"] = "IRR (to Dec-Y-1)"
        ws[f"{C(0)}34"] = "   FCF Yield (on PT)"
        ws[f"{C(0)}44"] = "Implied Market Cap (USDm)"
        ws[f"{C(0)}45"] = "(+) Net Debt & NCI"
        ws[f"{C(0)}46"] = "Implied Enterprise Value (USDm)"
        ws[f"{C(0)}47"] = "Implied EV / Adjusted EBITDA (x)"
        for r in (26, 34, 44, 45, 46, 47):
            ws[f"{C(0)}{r}"].font = font(12, color=GREYF)
        for r in (27,):
            ws[f"{C(0)}{r}"].font, ws[f"{C(0)}{r}"].fill = font(12, True, color=WHITE), fill(DARK)
        ws[f"{C(0)}29"].font, ws[f"{C(0)}29"].fill = font(12, True, color=DARK), fill(LIGHT)
        for i in range(2, 6):
            col = C(1 + i)
            prev = C(i)
            y = years[i]
            mc = cols.annual(y)
            pe_cell = ws[f"{col}26"]
            pe_cell.value = pe_col_val if i == 2 else f"={prev}26"
            pe_cell.font, pe_cell.fill, pe_cell.number_format = font(12, True, color=BLUE), fill("FFF8DC"), "0.0\\x"
            ws[f"{col}27"] = f"={col}26*{col}23"
            ws[f"{col}27"].number_format = FMT_NUM
            ws[f"{col}27"].font, ws[f"{col}27"].fill = font(12, True, color=WHITE), fill(DARK)
            ws[f"{col}28"] = f'=IFERROR({col}27/$K$2-1,"")'
            ws[f"{col}28"].number_format = FMT_PCT0
            if i >= 3:
                ws[f"{col}29"] = (f'=IFERROR(({col}27/$K$2)^(1/((DATE({y}-1,12,31)-$K$3)/365.25))-1,"")')
                ws[f"{col}29"].number_format = FMT_PCT0
                ws[f"{col}29"].font, ws[f"{col}29"].fill = font(12, True, color=DARK), fill(LIGHT)
            ws[f"{col}34"] = f'=IFERROR({col}33/{col}$27,"")'
            ws[f"{col}34"].number_format = FMT_PCT
            ws[f"{col}44"] = f"={col}27*{col}21"
            ws[f"{col}45"] = (f"={col}38+Model!{mc.L}{rowmap['v_nci']}" if snap is None
                              else f"={col}38+{('Model!' + mc.L + str(rowmap['v_nci']))}")
            ws[f"{col}46"] = f"={col}44+{col}45"
            ws[f"{col}47"] = f'=IFERROR({col}46/{col}35,"")'
            for r in (44, 45, 46):
                ws[f"{col}{r}"].number_format = FMT_NUM
            ws[f"{col}47"].number_format = FMT_X
            for r in (28, 34, 44, 45, 46, 47):
                ws[f"{col}{r}"].font = font(12, color=GREYF)
    put_comment(ws["N26"], "Bull P/E on non-GAAP EPS (company definition). Teledyne traded ~20–30x NTM non-GAAP EPS "
                "2022–26 (≈25x at $615 on the FY26 outlook mid-point).")
    return ws


# ------------------------------------------------------------------------------------------------
# DCF
# ------------------------------------------------------------------------------------------------
def write_dcf(wb, cols, rowmap):
    ws = wb.create_sheet("DCF")
    ws.sheet_view.zoomScale = 70
    ws.column_dimensions["A"].width = 10.6
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 12.6
    for L in "DEFGHIJKLMN":
        ws.column_dimensions[L].width = 12.6

    def M(key, y):
        return f"Model!{cols.annual(y).L}{rowmap[key]}"

    def hdr(cell, text, color=MID, sz=12):
        ws[cell] = text
        ws[cell].font = font(sz, True, color=WHITE)
        ws[cell].fill = fill(color)

    hdr("B2", "DCF VALUATION — TELEDYNE TECHNOLOGIES (TDY)", DARK, 14)
    hdr("B4", "1. WACC BUILD")
    inputs = [(5, "Risk-free rate (US 10Y govt)", 0.0425, "0.00%", "Assumption (~US 10Y Treasury yield); update to market"),
              (6, "Equity risk premium", 0.050, "0.00%", "US implied ERP ~4.5–5.5% (Damodaran)"),
              (7, "Levered beta", 1.00, "0.00", "Diversified instrumentation / A&D electronics peers (AME, KEYS, LHX) ~0.9–1.1; "
                                               "~25% US Government sales dampen cyclicality"),
              (8, "Cost of equity", "=C5+C7*C6", "0.00%", None),
              (9, "Pre-tax cost of debt", 0.0475, "0.00%", "BBB-rated (investment grade); FLIR-acquisition notes 1.6%–2.75% "
                                                         "fixed coupons; marginal cost ~4.5–5.0%"),
              (10, "Tax rate", 0.215, "0.00%", "Model 2027E+ effective tax rate (FY26 outlook rate in the scenario table)"),
              (11, "After-tax cost of debt", "=C9*(1-C10)", "0.00%", None),
              (12, "Target D/V", 0.10, "0.00%", "Net debt ~$1.7bn vs ~$29bn market cap; leverage 1.1x at 30-Jun-26"),
              (13, "WACC", "=C8*(1-C12)+C11*C12", "0.00%", None)]
    for r, lab, v, fmt, note in inputs:
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
        if note:
            ws[f"D{r}"] = note
            ws[f"D{r}"].font = font(10, color=GREYF)
    ws["B15"], ws["C15"] = "Valuation date (live)", "=TODAY()"
    ws["C15"].number_format = "dd-mmm-yy"
    ws["D15"] = "Periods = (Dec-31-Year − today) / 365.25; cash flows assumed at year-end"
    ws["D15"].font = font(10, color=GREYF)
    hdr("B16", "2. UNLEVERED FREE CASH FLOW BUILD (USDm)")
    yrs = list(range(2026, 2036))
    colL = list("DEFGHIJKLM")
    for L, y in zip(colL, yrs):
        hdr(f"{L}17", f"{y}E", DARK)
    hdr("N17", "Terminal", DARK)
    lines = [(18, "Non-GAAP operating income (Model, current definition)", "o_cur"),
             (19, "(−) Transaction & integration costs (cash, excluded from non-GAAP)", "corp_it"),
             (22, "plus depreciation (D&A ex acquired-intangible amortization)", "adj_da")]
    for r, lab, key in lines:
        ws[f"B{r}"] = lab
        for i, (L, y) in enumerate(zip(colL, yrs)):
            if y <= 2030:
                f = f"={M(key, y)}" if r != 19 else f"=-{M(key, y)}"
                ws[f"{L}{r}"] = f
                ws[f"{L}{r}"].font = font(12, color=GREEN)
            else:
                ws[f"{L}{r}"] = f"={colL[i - 1]}{r}*(1+{L}$29)"
            ws[f"{L}{r}"].number_format = FMT_NUM
    ws["B20"] = "× (1 − tax rate)"
    ws["B21"] = "NOPAT  =  (Non-GAAP OI − transaction costs) × (1 − t)"
    ws["B23"] = "− Capex (PP&E) and acquisitions (M&A lever, 2027E+)"
    ws["B24"] = "− Δ Working capital (CF statement)"
    ws["B25"] = "Unlevered FCF"
    ws["B26"] = "Terminal Value (Gordon Growth)"
    ws["B27"] = "   memo: PP&E capex only (fade years carry no new acquisitions)"
    ws["B27"].font = font(10, color=GREYF)
    ws["B29"] = "Fade-period growth (2031E–35E)"
    ws["B30"] = "Terminal growth rate"
    for i, (L, y) in enumerate(zip(colL, yrs)):
        ws[f"{L}20"] = "=1-$C$10"
        ws[f"{L}20"].number_format = "0.0%"
        ws[f"{L}21"] = f"=({L}18+{L}19)*{L}20"
        if y <= 2030:
            ws[f"{L}27"] = f"={M('cf_capex', y)}"
            ws[f"{L}23"] = f"={L}27" + (f"+{M('cf_acq', y)}" if y >= 2027 else "")
            ws[f"{L}24"] = f"={M('cf_wc', y)}"
            ws[f"{L}23"].font = ws[f"{L}24"].font = ws[f"{L}27"].font = font(12, color=GREEN)
        else:
            ws[f"{L}27"] = f"={colL[i - 1]}27*(1+{L}$29)"
            ws[f"{L}23"] = f"={L}27"
            ws[f"{L}24"] = f"={colL[i - 1]}24*(1+{L}$29)"
        ws[f"{L}25"] = f"={L}21+{L}22+{L}23+{L}24"
        for r in (21, 23, 24, 25, 27):
            ws[f"{L}{r}"].number_format = FMT_NUM
        ws[f"{L}25"].font, ws[f"{L}25"].fill = font(12, True), fill(LIGHT)
    ws["B25"].font, ws["B25"].fill = font(12, True), fill(LIGHT)
    ws["N25"] = "=M25*(1+$C$30)"
    ws["N26"] = "=N25/($C$13-$C$30)"
    for a in ("N25", "N26"):
        ws[a].number_format = FMT_NUM
        ws[a].font, ws[a].fill = font(12, True), fill(LIGHT)
    for L, g in zip("IJKLM", (0.06, 0.055, 0.05, 0.045, 0.04)):
        ws[f"{L}29"] = g
        ws[f"{L}29"].number_format = "0.0%"
        ws[f"{L}29"].font, ws[f"{L}29"].fill = font(12, color=BLUE), fill(CREAM)
    ws["C30"] = 0.03
    ws["C30"].number_format = "0.0%"
    ws["C30"].font, ws["C30"].fill = font(12, True, color=BLUE), fill(YELLOW)
    ws["B32"], ws["B33"], ws["B34"] = "Discount period (years)", "Discount factor", "PV of UFCF"
    for L, y in zip(colL, yrs):
        ws[f"{L}32"] = f"=(DATE({y},12,31)-$C$15)/365.25"
        ws[f"{L}33"] = f"=1/(1+$C$13)^{L}32"
        ws[f"{L}34"] = f"={L}25*{L}33"
        ws[f"{L}32"].number_format = "0.00"
        ws[f"{L}33"].number_format = "0.000"
        ws[f"{L}34"].number_format = FMT_NUM
    ws["N32"], ws["N33"], ws["N34"] = "=M32", "=1/(1+$C$13)^N32", "=N26*N33"
    ws["N32"].number_format, ws["N33"].number_format, ws["N34"].number_format = "0.00", "0.000", FMT_NUM
    ws["D35"] = ("Teledyne's non-GAAP operating income already expenses stock-based compensation (only acquired-"
                 "intangible amortization and acquisition items are excluded). Acquisition spend from the M&A lever is "
                 "deducted in 2027E–30E so that acquired sales / profit in the Model are paid for; the fade period and terminal "
                 "value assume no new acquisitions. Operating-lease costs sit inside "
                 "operating income (lease liabilities not deducted as debt).")
    ws["D35"].font = font(10, color=GREYF)
    hdr("B37", "3. VALUATION SUMMARY")
    summ = [(38, "Sum of PV (explicit + fade)", "=SUM(D34:M34)", FMT_NUM),
            (39, "PV of Terminal Value", "=N34", FMT_NUM),
            (40, "Enterprise Value", "=C38+C39", FMT_NUM),
            (41, "Less: net debt (Model 2026E YE)", f"={M('l_nd', 2026)}", FMT_NUM),
            (42, "Less: non-controlling interests (Model 2026E)", f"={M('v_nci', 2026)}", FMT_NUM),
            (43, "Equity Value", "=C40-C41-C42", FMT_NUM),
            (44, "Diluted shares (m, Model 2026E)", f"={M('sh_dil', 2026)}", FMT_SHR),
            (45, "Implied share price ($)", "=C43/C44", "#,##0.00"),
            (46, "Current share price ($)", f"={M('px', 2026)}", "#,##0.00"),
            (47, "Implied upside / (downside)", "=C45/C46-1", FMT_PCT)]
    for r, lab, f, fmt in summ:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = fmt
        ws[f"B{r}"].font = font(12, r in (40, 43, 45))
        if r == 45:
            ws[f"C{r}"].font, ws[f"C{r}"].fill = font(12, True, color=WHITE), fill(DARK)
        elif r in (40, 43):
            ws[f"C{r}"].font, ws[f"C{r}"].fill = font(12, True), fill(LIGHT)
    hdr("B50", "4. SENSITIVITY: IMPLIED PRICE ($) — WACC × Terminal Growth")
    ws["B52"] = "WACC (across):"
    ws["B53"] = "g (down) / WACC"
    for L, w in zip("DEFGH", (0.07, 0.075, 0.08, 0.085, 0.09)):
        ws[f"{L}53"] = w
        ws[f"{L}53"].number_format = "0.00%"
        ws[f"{L}53"].font = font(12, True, color=BLUE)
    for r, g in zip(range(54, 59), (0.02, 0.025, 0.03, 0.035, 0.04)):
        ws[f"B{r}"] = g
        ws[f"B{r}"].number_format = "0.00%"
        ws[f"B{r}"].font = font(12, True, color=BLUE)
        for L in "DEFGH":
            ws[f"{L}{r}"] = (f'=IFERROR((SUMPRODUCT($D$25:$M$25/(1+{L}$53)^$D$32:$M$32)+($M$25*(1+$B{r})/({L}$53-$B{r}))'
                             f'/(1+{L}$53)^$M$32-$C$41-$C$42)/$C$44,"")')
            ws[f"{L}{r}"].number_format = "#,##0"
    hdr("B61", "5. REVERSE DCF")
    ws["B62"] = ("To solve for the market-implied path: Data ▸ What-If Analysis ▸ Goal Seek — set C45 to the current price "
                 "(C46) by changing C30 (terminal growth) or the Model scenario levers (segment organic growth, non-GAAP "
                 "margins, M&A spend).")
    ws["B62"].font = font(10, color=GREYF)
    hdr("B64", "6. MAUBOUSSIN EV / NOPAT — TWO-STAGE FRAMEWORK")
    ws["B65"] = "EV/NOPAT  =  1/r  +  [g × (1 − r/ROIIC) / (r × (r − g))] × [1 − ((1+g)/(1+r))^N]"
    ws["B66"] = ('Formula source: Mauboussin & Rappaport, "Expectations Investing" (2021); Counterpoint Global, "What Does '
                 'a Price-Earnings Multiple Mean?" (2020).')
    for a in ("B65", "B66"):
        ws[a].font = font(10, color=GREYF)
    hdr("B68", "Input")
    hdr("C68", "Value")
    hdr("D68", "Rationale (Teledyne characteristics)")
    mi = [(69, "r  (Cost of capital / WACC)", "=$C$13", "Linked from Section 1 WACC build"),
          (70, "g  (NOPAT growth, Stage 1)", 0.08, "Model non-GAAP OI CAGR 2025–30E: mid-single-digit organic growth "
                                                 "+ margin expansion + bolt-on M&A"),
          (71, "ROIIC  (Return on incremental invested capital)", 0.15, "Organic growth is capital-light (capex ~2% "
                                                                     "of sales); acquired growth earns ~8–10% after-tax "
                                                                     "on purchase price (FLIR goodwill-heavy base: ROIC "
                                                                     "~7–9%)"),
          (72, "N  (Years of value creation / CAP)", 15, "Niche leadership in IR imaging, marine instruments and "
                                                         "space-qualified sensors; decentralised serial-acquirer model "
                                                         "with disciplined capital allocation")]
    for r, lab, v, note in mi:
        ws[f"B{r}"], ws[f"C{r}"], ws[f"D{r}"] = lab, v, note
        ws[f"C{r}"].number_format = "0" if r == 72 else "0.00%"
        ws[f"C{r}"].font = font(12, color=BLACK if isinstance(v, str) else BLUE)
        if not isinstance(v, str):
            ws[f"C{r}"].fill = fill(CREAM)
        ws[f"D{r}"].font = font(10, color=GREYF)
    hdr("B74", "Calculation")
    hdr("C74", "Value")
    calc = [(75, "Steady-state component:  1 / r", "=1/C69"), (76, "Value-creation factor: 1 − r / ROIIC", "=1-C69/C71"),
            (77, "Growth multiplier: g × (1 − r/ROIIC) / (r × (r − g))", "=C70*C76/(C69*(C69-C70))"),
            (78, "Time decay: 1 − ((1+g)/(1+r))^N", "=1-((1+C70)/(1+C69))^C72"),
            (79, "PVGO component (growth value)", "=C77*C78"), (80, "Mauboussin EV / NOPAT (steady-state + PVGO)", "=C75+C79")]
    for r, lab, f in calc:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = "0.00"
    ws["B80"].font, ws["C80"].font, ws["C80"].fill = font(12, True, color=WHITE), font(12, True, color=WHITE), fill(DARK)
    ws["B80"].fill = fill(DARK)
    ws["C80"].number_format = "0.0\\x"
    hdr("B82", "VALUATION  —  Applied to 2028E NOPAT")
    hdr("C82", "USDm")
    val = [(83, "2028E Non-GAAP operating income (Model)", f"={M('o_cur', 2028)}"),
           (84, "(−) 2028E transaction & integration costs", f"=-{M('corp_it', 2028)}"),
           (85, "Tax rate (from WACC build)", "=$C$10"),
           (86, "2028E NOPAT  =  (OI − transaction costs) × (1 − t)", "=(C83+C84)*(1-C85)"),
           (87, "× Mauboussin EV/NOPAT multiple", "=C80"), (88, "Implied Enterprise Value (2028E basis)", "=C86*C87"),
           (89, "Less: YE2027 net debt + NCI (Model)", f"={M('l_nd', 2027)}+{M('v_nci', 2027)}"),
           (90, "Implied Equity Value", "=C88-C89"), (91, "Diluted shares 2028E (m, Model)", f"={M('sh_dil', 2028)}"),
           (92, "Implied share price 2028 ($)", "=C90/C91"), (94, "Current share price ($)", "=C46"),
           (95, "Implied upside / (downside)", "=C92/C94-1")]
    for r, lab, f in val:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = FMT_PCT if r in (85, 95) else ("0.0\\x" if r == 87 else
                                                                  ("#,##0.00" if r in (92, 94) else FMT_NUM))
    hdr("B97", "MARKET-IMPLIED EV/NOPAT TODAY")
    hdr("C97", "USDm")
    mkt = [(98, "Current market cap (spot × diluted shares)", "=C46*C44"),
           (99, "Plus: YE2026 net debt & NCI", "=C41+C42"),
           (100, "Implied Enterprise Value (today)", "=C98+C99"),
           (101, "TDY's market-implied EV/NOPAT (on 2028E NOPAT)", "=C100/C86"),
           (103, "Multiple gap (Mauboussin − Market)", "=C80-C101"), (104, "Implied re-rating headroom", "=C80/C101-1")]
    for r, lab, f in mkt:
        ws[f"B{r}"], ws[f"C{r}"] = lab, f
        ws[f"C{r}"].number_format = FMT_PCT if r == 104 else ("0.0\\x" if r in (101, 103) else FMT_NUM)
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
    ws["B2"] = "Teledyne Technologies — Historical Operating Performance (2006–2025)"
    ws["B2"].font = font(14, True)
    ws["B3"] = ("All historicals · USDm · Linked to Model. M&A % = disclosed incremental sales from acquisitions (e.g. "
                "DALSA 2011, e2v 2017, FLIR 2021, Excelitas A&D 2025). Non-GAAP OI on the current definition (model "
                "memo series) for all years.")
    ws["B3"].font = font(10, color=GREYF)
    yrs = list(range(2006, 2026))
    from openpyxl.utils import get_column_letter
    CL = [get_column_letter(3 + i) for i in range(len(yrs))]
    last = CL[-1]

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

    line(8, "Organic %", "g_org", FMT_PCT, zero=True)
    line(9, "M&A %", "g_acq", FMT_PCT, zero=True)
    yrow(11)
    line(12, "Non-GAAP Operating Income", "o_cur", FMT_NUM)
    line(13, "Operating Income (GAAP)", "op_income", FMT_NUM)
    line(14, "Non-GAAP Op. Margin %", "m_adjoi", FMT_PCT)
    line(15, "GAAP Op. Margin %", "m_oi", FMT_PCT)
    yrow(17)
    line(18, "ROIC", "roic", FMT_PCT, na=True)
    line(19, "RONTA", "ronta", FMT_PCT, na=True)
    line(20, "Non-GAAP op. margin %", "m_adjoi", FMT_PCT, na=True)
    line(21, "FCF margin %", "fcf_m", FMT_PCT, na=True)

    cats = Reference(ws, min_col=3, max_col=2 + len(yrs), min_row=7)
    c1 = BarChart()
    c1.type, c1.grouping, c1.overlap = "col", "stacked", 100
    _title(c1, "Net Sales Growth Decomposition: Organic vs M&A")
    for r, color in ((8, "2F3E46"), (9, "84A98C")):
        c1.add_data(Reference(ws, min_col=2, max_col=2 + len(yrs), min_row=r), titles_from_data=True, from_rows=True)
        c1.series[-1].graphicalProperties.solidFill = color
    c1.set_categories(cats)
    c1.y_axis.number_format = "0%"
    c1.width, c1.height = 30, 7.5
    ws.add_chart(c1, "B24")

    c2 = BarChart()
    c2.type, c2.grouping = "col", "clustered"
    _title(c2, "Non-GAAP & GAAP Operating Income (USDm) with Margins (%)")
    for r, color in ((12, "A8C5D6"), (13, "1F4E79")):
        c2.add_data(Reference(ws, min_col=2, max_col=2 + len(yrs), min_row=r), titles_from_data=True, from_rows=True)
        c2.series[-1].graphicalProperties.solidFill = color
    c2.set_categories(cats)
    c2.y_axis.number_format = "#,##0"
    l2 = LineChart()
    for r, color in ((14, "2F3E46"), (15, "C8553D")):
        l2.add_data(Reference(ws, min_col=2, max_col=2 + len(yrs), min_row=r), titles_from_data=True, from_rows=True)
        l2.series[-1].graphicalProperties.line.solidFill = color
    l2.y_axis.axId = 200
    l2.y_axis.number_format = "0%"
    l2.y_axis.crosses = "max"
    c2 += l2
    c2.width, c2.height = 30, 7.5
    ws.add_chart(c2, "B45")

    c3 = LineChart()
    _title(c3, "Returns Profile: ROIC, RONTA, Non-GAAP Operating Margin & FCF Margin")
    for r, color in ((18, "2F3E46"), (19, "84A98C"), (20, "1F4E79"), (21, "C8553D")):
        c3.add_data(Reference(ws, min_col=2, max_col=2 + len(yrs), min_row=r), titles_from_data=True, from_rows=True)
        c3.series[-1].graphicalProperties.line.solidFill = color
    c3.set_categories(cats)
    c3.y_axis.number_format = "0%"
    c3.width, c3.height = 30, 7.5
    ws.add_chart(c3, "B66")
    return ws
