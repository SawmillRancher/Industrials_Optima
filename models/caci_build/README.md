# CACI model build kit

`models/CACI_Model.xlsx` is the CACI International Inc (NYSE: CACI) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kits:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CK2`, scenario table in `Model!CS:CW`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to 30-June fiscal year ends. Net debt is taken at 30-Jun-2027E, so the FY2027E cash flow is excluded (inclusion flag, DCF row 28).
  - Charts: organic vs acquired growth, EBITDA / income from operations, returns (FY2007–FY2026).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 June; 2027 = Jul-2026 – Jun-2027)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–CA Q1/13–Q4/26 with FY subtotals; CB Q1/27:** grouped and collapsed like the template.
- **CC–CE Q2/27E–Q4/27E, CF 2027E:** forecast, calibrated to the FY27 guidance (Q1 FY27 release, 21-Oct-2026).
- **CG–CJ 2028E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 5): CK notes, CM–CP CAGRs (5Y fwd '26–'31, 5Y, 10Y, 20Y), CS–CW scenario table.

## Basis
- **Policy:** as originally reported — each period from its own earnings release (three-month column; fiscal years from the Q4 release twelve-month column).
- **Documented exceptions (latest filing that first presents the period; cell comments):**
  - Customer types: Department of War / Intelligence Community / Federal civilian were introduced in the Q1 FY26 release. FY2025 quarters and FY2025 use the FY2026 comparatives; all earlier periods are on the legacy basis (Department of Defense incl. intelligence agencies / Federal civilian), kept in memo rows with a Σ check. The main rows carry a "not split on the current basis" line to FY2024.
  - Measures first published with comparatives: adjusted net income on the current definition (Q3 FY20–Q2 FY21, FY2020), free cash flow and MARPA (FY2019–Q2 FY21), Technology / Expertise revenue (FY2020), contract awards (FY2018).
- **Segments:** Domestic Operations and International Operations throughout (memo block; segment measure = net income to FY2025, income from operations from the FY2025 10-K). Q4 = fiscal year − Q1–Q3; not derived for Q4 FY16 (ASU 2016-09 adoption) and Q4 FY25 (measure change).
- **Per-share data:** no stock splits; no share classes. Shares outstanding = shares issued − treasury shares (XBRL, from FY2010).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Lines are grouped into the model's buckets by `normalize.py`.

## Model structure (Model tab)
- **Operating build:** revenue = prior-year revenue × (1 + organic growth) + acquired revenue (company definition: acquired until the first anniversary of closing). Acquired revenue is published FY2006–13 and derived from the stated organic growth from FY2020 (cell comments quote the release). Customer types are a mix-driven output (Department of War balances). Memo blocks: contract type, prime / subcontractor, Technology / Expertise, direct-cost mix, backlog roll-forward with derived adjustments, awards and book-to-bill, employees, segments.
- **Acquisition block:** ARKA Group (closed 9-Mar-2026, $2,642.7m net of cash): preliminary PPA from the FY2026 10-K in the Q3/26 column with a zero check; remaining inorganic revenue in Q2–Q3/27E = Q1/27 acquired revenue × share of the quarter before the anniversary. ARKA's standalone revenue was not disclosed (the seller was private).
- **Future M&A lever:** spend ÷ EV/sales (2.5x), 16% EBITDA margin, PP&E 5% / intangibles 43% / goodwill split, 15-year amortization.
- **FY27 guidance calibration (Q2–Q4/27E):**
  - Revenue: one Δ on organic growth (vs Q1/27 +2.1%), solved so FY27 revenue = $10.9 / 10.8 / 10.7bn.
  - Margin: one Δ on the EBITDA margin (prior-year quarter + Q1 drift), solved in closed form so FY27 adjusted net income = $760 / 750 / 740m.
  - Information rows, not forced: adjusted EPS ($33.18–34.08 on 22.3m shares), GAAP net income ($579–599m), free cash flow (at least $900m).
- **GAAP P&L from the build:** income from operations = EBITDA − D&A − depreciation within direct costs. Direct costs are implied. Interest on opening balances; tax 25%.
- **GAAP → non-GAAP bridges** (checks vs published in every reported period):
  1. **Net income → EBITDA (company definition in force) → adjusted EBITA (model):** definition row flags pro forma / adjusted EBITDA periods; an explicit basis-difference line covers the company's net-interest and NCI basis.
  2. **Net income → adjusted net income → adjusted diluted EPS:** definition in force per period (FY2009–Q2 FY18 old definition; none Q3 FY18–Q2 FY20; current definition from Q3 FY20), plus a current-definition memo series for every period with published intangible amortization.
  3. **Free cash flow:** CFO excluding MARPA − capex (company definition), checked vs published.
- **Other schedules:** cash flow; buybacks; balance sheet; working capital; ARKA PPA; debt (scheduled term-loan amortization, revolver to a $200m minimum cash, headroom memo); leverage-target buybacks from 2028E (2.5x / 2.0x / 1.5x); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBITA (before intangible amortization; stock-based compensation expensed), depreciation-only add-back; leases operating; opening IC = FY2026 book IC (includes ARKA). Market inputs (risk-free 4.25%, ERP 5%, beta 0.85) are assumptions.

## Key forecast assumptions (Base)
- Organic growth 6.5% / 6.5% / 6.0% / 6.0% (2028E–31E); EBITDA margin 13.2% → 13.8%; M&A $300m p.a. — assumptions citing FY2024–26 history and the FY27 guidance.
- Indirect costs 22.2% → 21.9% of revenue; depreciation 1.05%; capex 1.1%; amortization per the 10-K schedule; tax 25%; no dividend.
- Q2–Q4/27E buybacks $150m / $50m / $0 (assumption; $187.3m authorization remaining).
- **Share price $625.00:** provided by the user on 20-Nov-2026 (not an SEC-filed price); update it at `Model!CF` in the valuation block.
- **Guidance:** only the FY27 guidance filed on EDGAR (8-K Ex. 99.1, 21-Oct-2026) is used. Nothing from outside EDGAR (calls, IR decks) is in the model.

## Data corrections
- None. Known data exceptions (documented, not corrected; `check_data.py` prints them):
  - FY2014: Σ quarterly adjusted net income as first published exceeds the FY figure by $2.5m (Six3 transaction-cost presentation).
  - FY2016: Σ quarters of net income is $1.0m below the year (ASU 2016-09 adopted in the Q4 release for the full year).
  - FY2025: Σ quarterly contract awards is $22.5m below the year.
  - Q2 FY22 release: borrowing and FX cash-flow lines were printed without amounts; derived from the financing subtotal and the net change in cash.

## Sources
SEC EDGAR only (CIK 0000016058):
- Forms 10-K / 10-Q FY2006–Q1 FY2027.
- Form 8-K Item 2.02 earnings releases (Ex. 99 / 99.1), Q4 FY2006 – Q1 FY2027 (81 releases).
- Deal / financing 8-Ks: ARKA (22-Dec-2025, 9-Mar-2026), Term Loan B-2 and 2033 Notes-2 (Mar-2026).
- XBRL company facts for intangible amortization, goodwill, shares issued / treasury shares, and the annual cross-check.

The investor-relations site (investor.caci.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. `filings.csv` indexes the filings, each `data/<period>.json` lists its source URLs, and `data/_releases.json` indexes the releases. `manual_items.json` holds the FY27 guidance, amortization, debt facts, the ARKA PPA, the buyback authorization and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export CACI_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 -I fetch.py && python3 -I extract.py && python3 -I supp.py`.
   3. `python3 check_data.py` runs ~1,800 checks (statement arithmetic, revenue tables, segments, bridges, cash, balance sheet, quarters vs years) and 100 XBRL cross-checks. Known exceptions: the four listed above.
3. Build: `python3 build.py --snap --recalc` writes `../CACI_Model.xlsx`, reruns with the switch on Bull and Bear to fill the snapshot panels, and stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../CACI_Model.xlsx` → 0 error cells, 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../CACI_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../CACI_Model.xlsx --extra WWD Woodward 382.17 STE STERIS` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `parse_release.py`, `extract.py`, `supp.py`: EDGAR HTML → text (inline-XBRL safe), filings index, downloads, release parser, per-period extraction, 10-K / 10-Q / XBRL supplements.
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow.
- `check_data.py`: data consistency checks and XBRL cross-check.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
