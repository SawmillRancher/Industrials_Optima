# Cintas (CTAS) — 3-Statement Model

`CTAS_Model.xlsx` is built on the MLM model template, keeping the same sheets, layout, colour conventions, scenario switch and GAAP → Adjusted bridges. It has been adapted to how Cintas reports.

| Sheet | Contents |
|---|---|
| **Model** | Segment build (UR&FS, First Aid & Safety, All Other). UniFirst block (toggle). Future M&A lever. Group total with FY27 guidance calibration. Income statement. EBITDA → Adjusted EBITDA bridge. GAAP EPS → adjusted EPS bridge. Growth & margins. Cash flow, FCF, buybacks, balance sheet, working capital. UniFirst purchase-price allocation, D&A split, debt & leverage schedules. Ratios and valuation. Scenario input table in columns CS–CW; switch in CK2. |
| **Bull-Base-Bear** | Live panel (current switch) plus value snapshots of the Bull and Bear runs. |
| **DCF** | WACC, unlevered FCF FY2027E–36E, terminal value, WACC × g sensitivity, Mauboussin EV/NOPAT. |
| **Charts** | FY2006–FY2026 history: organic vs. inorganic growth; Adj. EBITDA & operating income; returns. |

The template's `DCF_old` sheet was an MLM-specific legacy version and is not carried over.

## Periods and basis
- **Periods:** fiscal years end 31-May. Annual FY2006–FY2012, then quarterly from Q1 FY13 to Q1 FY27 (actual). Q2–Q4 FY27E, then FY2027E–FY2031E. Quarter columns are grouped and collapsed, as in the template.
- **Restatements:** quarters are shown as originally reported. Per-share data and share counts are restated for the 4-for-1 split (Sep-2024).
- **Segments:** the legacy four-segment structure runs to FY2015 as memo rows. The current structure starts in FY2016 (FY2015 recast).

## Sources
All from SEC EDGAR (CIK 0000723254). The Cintas IR releases are the same documents as the 8-K Ex. 99 filings.
- **Earnings releases:** 86 releases (FY2005–Q1 FY27), giving the income statement, balance sheet, cash flow, segments, organic growth, FCF and adjusted EPS reconciliations.
- **Cintas 10-K / 10-Q:** segment organic growth, dividends and debt.
- **UniFirst deal:** the deal 8-K, S-4/424B3 (pro forma and purchase-price allocation) and the 2026 credit agreement 8-K.
- **UniFirst standalone:** UniFirst 10-K / 8-K / 10-Q (CIK 0000717954).
- **Citations:** see `source_kit/unf/UNF_SOURCES.txt` for the UniFirst numbers.

## GAAP → Adjusted bridges
- **Adjusted EBITDA (model definition):** income from continuing ops + taxes + interest expense − interest income + D&A = EBITDA. Add back the items the company excluded from adjusted EPS:
  - G&K and UniFirst transaction & integration costs;
  - restructuring, impairment, legal and Shred-it charges;
  - the FY09 inventory charge;
  - S&A items (FY18 employee payment, FY21–22 gains);
  - non-operating gains and equity-method results.
- **EBITDA check:** ties to company-published EBITDA for FY2012–14 (Debt/EBITDA tables).
- **Adjusted EPS:** reconciled to every company-published adjusted EPS figure (FY09–11, FY14–15, FY17–22, FY26–Q1 FY27). A "other company-defined items & rounding" row covers the ASU 2016-09 benefit, the two-class method and rounding.
- **Free cash flow and organic growth:** Cintas's own non-GAAP measures, tied to the published figures.

## Key forecast assumptions (Base)
- **Legacy FY27E:** calibrated to the midpoint of guidance ($12.21bn revenue; $5.495 adjusted EPS, which excludes UniFirst).
- **UniFirst:**
  - closing assumed 31-Dec-2026; $155 cash + 0.772 CTAS shares (14.07m shares);
  - $2.8bn acquisition debt at 5% (424B3);
  - purchase-price allocation per the 424B3: goodwill $2.85bn; intangibles $1.29bn amortised at $98m a year;
  - $375m synergies phased 25%, 55%, 85% and 100% over FY28–31E;
  - $350m integration costs (assumption — not disclosed).
- **FY28E+:**
  - organic growth: UR&FS 7.0–6.0%, FA&S 12–9%, All Other 9–7%;
  - modest margin expansion;
  - $300–450m a year of bolt-on M&A;
  - buybacks plugged to 1.25x net debt / Adjusted EBITDA.
- **Share price:** $198.95, the latest observable on EDGAR (Form 4, 15-Sep-2026). Overwrite it with a live quote.

## Rebuild
`source_kit/` holds the extraction and build scripts, the extracted dataset (`edgar/hist.json`), the curated non-GAAP data (`scripts/curated.py`) and the template.

Run `python3 source_kit/scripts/build_model.py out.xlsx`. It needs openpyxl, and LibreOffice for the Bull/Bear snapshot runs. Then recalculate (open in Excel, or `soffice --headless --convert-to xlsx`).

To re-extract history from EDGAR:
1. `dl.py` (download)
2. `convall.py` (convert to text)
3. `parseall.py`
4. `extract.py`
5. `canon.py`
6. `segparse.py`
7. `hist.py`

Raw filings are not committed (~200 MB).
