# MCO model build kit

`models/MCO_Model.xlsx` is the Moody's Corporation (NYSE: MCO) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows. The template's Base and Bull panels had P/E rows for 2029E–30E only, so their 2028E implied-EV cells read zero; the 2028E P/E rows were added.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E UFCF is shown but excluded from the sum, because net debt is taken at YE2026E.
  - Charts: segment contribution to revenue growth, Adjusted Operating Income vs operating income, and a returns panel. Book ROIC is replaced by FCF conversion, because invested capital is near zero or negative after debt-funded buybacks.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal year)
The layout is the template's own, so no column shift is needed (template column − 0):
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BX Q1/26–Q2/26:** quarterly actuals, grouped and collapsed like the template.
- **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast, calibrated to the FY26 outlook (Q2-26 release, 22-Jul-2026).
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast:** CF notes, CH–CK CAGRs (5Y forward '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** as originally reported, from each period's own release / 10-Q. Annual columns use the 10-K where it differs from the Q4 release.
- **Recasts:**
  - **2006–07:** Moody's reported "Moody's Investors Service" (including research) and "Moody's KMV" until the Jan-2008 reorganisation into MIS and MA. Revenue lines for 2006–07 use the 2008-basis comparatives from the FY2007 and FY2008 documents (commented); the P&L is as reported.
  - **MA lines on the current structure:** Decision Solutions / Research & Insights / Data & Information arrived in 2022, and the Banking / Insurance / KYC split in the 2023 10-Q notes and 2024 releases. For the year before each re-presentation, the lines come from the following year's restated comparatives ("latest filing presenting the period"). This is done only where the restated lines sum to the originally reported MA revenue, i.e. the change is inside MA.
  - **Legacy MA structures** are memo rows: Subscriptions / Software / Consulting (2006–08); RD&A / Risk Management Software / PS (2009–11); RD&A / ERS / PS (2012–21).
  - **Q4-14 realignment:** KIS non-ratings revenue moved from MA to the new "MIS Other" line. Q1–Q3/14 stay as reported, so Σ quarters ≠ FY2014 by ±$10.1m (documented exception).
  - **Restatements not applied** (originally reported values kept): 2018 REIT revenue moved from SFG to CFG; 2016–17 adjusted EPS recast for amortization; ASU 2016-09 CFO restatement; 2Q23 DS → R&I move for 2022.
- **Adjusted Operating Income** (OI excluding D&A, restructuring and other items) has been published since Q3-12.
  - For 2006–11 the model applies the same definition: operating income + D&A + restructuring + IS-face other operating items, such as the 2006 99 Church Street building gain.
  - The company's earlier "non-GAAP operating income" (before D&A) is kept in cell comments.
- **Per-share data:** no stock splits since 2005; no share classes.
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M).
  - The 2019 "reclassification of cash to assets held for sale" (MAKS) sits in the FX & other line.
  - Published free cash flow is year-to-date in the releases; discrete quarters are derived.

## Model structure (Model tab)
- **Operating build:**
  - MIS revenue by line of business: Corporate Finance, Structured Finance, Financial Institutions, PPIF and MIS Other.
  - MA revenue by line: Banking, Insurance, KYC, Research & Insights and Data & Information.
  - A "not split on the current lines" row carries history before each structure; Σ lines is checked against reported segment revenue.
  - Intersegment revenue is held at % of external revenue: the MIS royalty charged to MA, and MA's sales to MIS.
  - Segment Adjusted Operating Income = total segment revenue (external + intersegment) × Adjusted Operating Margin (the company basis), checked against the published figure.
  - Σ segments = consolidated Adjusted Operating Income: Moody's allocates all corporate costs to the segments.
  - Memo rows: recurring revenue, MA ARR, organic constant-currency growth.
- **Acquisitions and divestitures:**
  - PPAs (final allocations, net of cash acquired) in the closing-quarter columns: BvD Q3-17, Reis Q4-18, RDC Q1-20, Q4-20 aggregate, Cortera Q1-21, RMS Q3-21, PassFort Q4-21.
  - The Regulatory Solutions sale (Q2-26) carries up to $119m of contingent consideration, modelled as a Q4/26E gain consistent with the FY26 EPS bridge (gain ~$(1.25) vs Q2 $(0.72)).
- **Future M&A lever:** MA bolt-ons, $200m p.a. Base at 7.0x EV / sales, 25% adjusted margin, 40% intangibles / 15-year life (assumptions).
- **FY26 outlook calibration (Q3/Q4-26E):**
  - **MIS:** one uniform Δ on the 1H26 y/y growth of every line, solved so FY26 revenue = FY25 × (1 + guided growth). "High-single-digit" is read as 9 / 8 / 7% (Bull / Base / Bear).
  - **MA:** the same, with "mid-single-digit" read as 6 / 5 / 4%. These readings of qualitative ranges are model interpretations.
  - **Margins:** one uniform Δ on both segment margins (prior-year quarter + 1H26 drift), solved so FY26 adjusted diluted EPS = $17.00 / $16.75 / $16.50.
    - Required 2H Adjusted Operating Income = (adjusted NI target − 1H actual − helper) ÷ (1 − t).
    - The helper is (−D&A + acquired-intangible amortization + net interest + other non-operating) × (1 − t) − NCI. It is closed form, with no circularity.
  - **Information rows (not forced):** MCO revenue growth, adjusted operating margin (52–53%), MIS margin (~65%), MA margin (34–35%), diluted EPS ($16.00–16.50), FCF ($2.7–2.9bn).
  - **Point estimates** from the guidance reconciliation:
    - interest $220–240m;
    - non-operating $70–90m incl. gains;
    - D&A ~6%, restructuring ~1.5% and reserve ~0.5% of revenue;
    - capex ~$450m;
    - ETR 23–25%.
  - **Base result:** revenue $8,227m (+6.6%), MIS margin 65.3%, MA margin 34.1%, adjusted operating margin 52.5%, diluted EPS $16.22, FCF $2,934m (above the guided range).
  - The HSD MIS guide implies roughly flat 2H MIS revenue after +16% in 1H26, so the MIS Δ is large (−16.6 pp).
- **GAAP P&L from the build:** operating income = Adjusted Operating Income − D&A − restructuring − other excluded items.
  - Operating expense is % of revenue, and SG&A is the balancing line.
  - Interest is on opening balances; the tax rate is applied to items as well.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating income → Adjusted Operating Income** (company definition; definition flags by column).
  2. **Net income → EBITDA → Adjusted EBITDA → Adjusted EBITA** (model definitions):
     - Adjusted EBITDA = the company's Adjusted Operating Income.
     - Adjusted EBITA = Adjusted Operating Income − depreciation (before acquired-intangible amortization), the NOPAT basis.
  3. **Net income → adjusted net income → adjusted diluted EPS:**
     - Items: amortization (from Q3-17), restructuring, other operating items, non-operating items, and the tax effect derived as published adjusted NI − NI − pre-tax items.
     - Where only per-share bridges were published (2013–15), item $ = per-share × diluted shares and adjusted NI = adjusted EPS × diluted shares (commented).
     - Periods with no published measure show adjusted = GAAP (flagged).
- **Other schedules:**
  - Cash flow (company FCF definition checked) and buybacks.
  - Balance sheet: ties every column; deferred revenue as % of revenue.
  - Working capital (year-end levels).
  - Debt: 14 senior notes repaid at maturity and refinanced, plus ~$500m p.a. incremental notes. Commercial paper is drawn to a $1.5bn minimum cash balance, with a headroom memo vs the $1.25bn backstop facility.
  - Leverage-target buybacks for 2027E+: net debt / Adjusted Operating Income of 1.50 / 1.25 / 1.00x (assumption).
  - Ratios: book ROIC shows n/m where IC < 25% of revenue.
  - Valuation.
- **DCF basis:**
  - NOPAT = (Adjusted EBITA − restructuring − other excluded cash items) × (1 − 24%), with a depreciation-only add-back.
  - Capex and bolt-on M&A are deducted; leases are operating.
  - Opening IC = 2025A book IC.
  - Market inputs are labelled assumptions, because Treasury / FRED data are not reachable: risk-free 4.25%, ERP 5%, beta 1.10, cost of debt 5.0%, D/V 8%; WACC 9.3%, g 4%.
  - Base implied price ~$381; Mauboussin (2028E NOPAT) ~$440.

## Key forecast assumptions (Base)
- **Revenue growth 2027E–30E** (scenario table, citing 1H26 trends and ARR growth):
  - MIS: CFG 7% → 5%, SFG 5% → 4%, FIG 6% → 5%, PPIF 6% → 5%, MIS Other 6% → 5%.
  - MA: Banking 7% → 6%, Insurance 9% → 7%, KYC 12% → 9%, R&I 5%, D&I 8% → 7%.
- **Margins:** MIS 65.5% → 67.0%; MA 35.5% → 38.5% (FY26 guidance 34–35%; restructuring savings $300–350m p.a.).
- **Restructuring:** $60m in 2027E (programme $300–350m, $212m charged to 30-Jun-2026). Other excluded items: $20m in 2027E (duplicate rent).
- **Cost and capital inputs:**
  - Operating expense 23.5% and SBC 3.0% of revenue; depreciation 3.6% → 3.8% of revenue (FY2025 3.4%).
  - Amortization per the FY2025 10-K schedule ($195m 2027E).
  - Capex 5.0–5.2% of revenue; ETR 24%; DPS +9% p.a.
- **2H26 buybacks:** $835m / $685m / $535m (FY26 guidance "up to $3.0bn"; 1H26 $2,165m).
- **Share price $470.00:** user-provided (12-Oct-2026); input at `Model!CA` in the valuation block. Cross-check: the latest SEC-filed price is the June-2026 average repurchase price of $450.64 (Q2-26 10-Q Part II Item 2). Update to market.

## Data corrections
- None. Known data exceptions (documented, not corrected):
  - FY2014 Σ quarters ≠ FY for MIS / MA revenue and segment AOI (Q4-14 realignment; ±$10.1m revenue, ±$1.9m AOI).
  - FY2016 restructuring and SG&A: the Q4-16 release kept $3.6m of restructuring inside SG&A, while the 10-K shows FY $12.0m. Adjusted OI Σ quarters ≠ FY by $3.6m, and segment AOI by $2.6m / $1.0m.
  - Q4-16 diluted EPS (2.22) as printed in the release; the 10-K shows (2.25).

## Sources
SEC EDGAR only (CIK 1059556):
- Forms 10-K / 10-Q FY2006–Q2 FY2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4 2006 – Q2 2026. The 2007–08 releases are plain-text exhibits, fetched by `fetch_txt.py`.
- Other 8-Ks: management and board changes 2026 (reviewed, not material).
- XBRL company facts: acquired-intangible amortization, plus cross-checks of revenue, operating income, net income, EPS, CFO and total assets.

The investor-relations site (ir.moodys.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs, and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds:
  - FY26 guidance (current and history, with the reconciliation rows) and the assumptions table;
  - the debt instruments, commercial paper and revolver;
  - the amortization schedule, buyback authorization and monthly repurchases, dividends;
  - deals and divestitures, the restructuring programme, shares outstanding, PPAs and pension.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export MCO_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 fetch_txt.py && python3 period_index.py`.
   3. Extract each new period into `data/<period>.json` following `EXTRACTION_SCHEMA.md`. This build extracted the periods with parallel agents on that schema; there is no `extract.py`.
   4. `python3 check_data.py` runs 1,394 checks: statement arithmetic, revenue-line and segment sums, Adjusted Operating Income / adjusted EPS bridges, GAAP EPS, cash and balance-sheet tie-outs, XBRL cross-checks and quarter sums. The known exceptions are the 9 listed under Data corrections.
3. Build: `python3 build.py --snap --recalc` writes `../MCO_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py <recalculated file>` → 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../MCO_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../MCO_Model.xlsx --allow 'Model!CF2' --extra WWD Woodward 382.17` → 0 hits. `Model!CF2` is MCO's own scenario switch.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs, compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `h2t.py`, `make_index.py`, `fetch.py`, `fetch_txt.py`, `period_index.py`: EDGAR HTML → text, filings index, downloads (including the 2007–08 plain-text exhibits), and the period → document map.
- `xbrl.py`: XBRL company-facts helper (calendar year; `dump_subset()` writes `data/_xbrl.json`).
- `normalize.py`: basis rules, revenue-line label maps, MA recast fill, flat model keys, discrete quarterly cash flow, FCF year-to-date handling.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
