# Karman Holdings (NYSE: KRMN) — 3-statement model

`KRMN_Model.xlsx` is built on the TDY model template (`../templates/TDY_Model.xlsx`). It keeps TDY's layout, cell styles,
colour conventions (blue = input, black = formula, green = cross-sheet link), check rows and scenario mechanics, adapted to
Karman's reporting.

## Sheets
| Sheet | Contents |
|---|---|
| Model | End-market revenue build → M&A lever → group Adj. EBITDA → IS → three GAAP→adjusted bridges → growth & margins → CF → buybacks → BS → working capital → BS schedules (debt, leases, amortization) → ratios → valuation. Scenario switch in `AA2`; scenario input table in `AG:AK`. |
| Bull-Base-Bear | Live panel linked to the Model, plus value snapshots of the Model run with the switch on Bull and on Bear. |
| DCF | WACC, UFCF on Adjusted EBITA, fade period and terminal value, WACC × g sensitivity, Mauboussin EV/NOPAT. |
| Charts | Organic vs M&A growth, Adj. EBITDA and GAAP operating income with margins, returns profile (2022A–2030E). |

## Period coverage
- Annual columns for FY2022–FY2023, the earliest years Karman reported (IPO prospectus / 10-K).
- Quarterly columns from Q1/24, the first quarters reported (as comparatives in the 2025 10-Qs), through Q2/26.
- Q3/26E–Q4/26E are calibrated to the FY26 outlook (Q2-26 release, 6-Aug-2026) less 1H/26 actuals. 2026E–2030E are annual.

## Karman-specific adaptations vs TDY
- **Segment build**: Karman reports one segment, so the build uses its four end markets (Hypersonics & Strategic Missile Defense,
  Space & Launch, Tactical Missiles & IDS, Maritime Defense Systems). Margins are modelled at group level.
- **Anchor KPI**: Adjusted EBITDA, Karman's guidance metric, replaces TDY's non-GAAP EPS calibration.
- **Bridges**:
  1. GAAP operating income → Adjusted EBITA (model) → company-published Adjusted EBITDA.
  2. GAAP net income → EBITDA → Adjusted EBITDA, line items exactly as published.
  3. GAAP net income → Adjusted net income → Adjusted EPS (company definition: adjustments are not tax-effected).
     A memo line adds a tax-effected EPS that also excludes amortization.

  Each bridge has a "model vs published (should be 0)" check against every reported period.
- **Debt**: Citi Term Loan B, revolver and finance leases (finance leases are treated as debt in net debt and EV).

## Sources
SEC EDGAR, CIK 0002040127:
- XBRL company facts (`sources/companyfacts_CIK0002040127.json`).
- Forms 10-K and 10-Q.
- IPO prospectus (424B4, 13-Feb-2025).
- Form 8-K earnings releases (Ex. 99.1), which are the same documents as on investors.karman-sd.com.
- 8-Ks on acquisitions and credit agreements, and the 16-Sep-2026 investor update.

Source notes are attached as cell comments on the row labels. The share price ($34.14, close 2-Oct-2026) is a user-updatable
input at `Model!V` in the Valuation block.

## Rebuild
```
cd builder
python3 driver.py ../KRMN_Model.xlsx   # builds Bull/Bear snapshots, then the Base file, and recalculates
```
Requires `openpyxl` and LibreOffice Calc (used for recalculation via the xlsx skill's `recalc.py`; set `RECALC_PY` to override).
