# GE model build kit

`models/GE_Model.xlsx` is the three-statement model for General Electric Company, operating as GE Aerospace (NYSE: GE). It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`. The scripts were adapted from the WWD kit.

- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped and collapsed.
- **Scenarios:** Bull / Base / Bear switch in `Model!AC2`; scenario table in `Model!AK:AO`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows. The implied-valuation rows are blank in years without an assumed P/E.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). FY2026E is the base year (net debt at 31-Dec-2026E); the explicit years are FY2027E–31E.
  - Charts: FY2023–2031E, the years with a GE Aerospace balance sheet.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (calendar fiscal years)
- **C FY2022:** annual. This is the first year presented on the GE Aerospace basis (statements, segments and cash flow; no balance sheet, no non-GAAP).
- **D–R Q1/23–Q4/25 with FY subtotals:** grouped and collapsed like the template.
- **S–T Q1/26–Q2/26:** actual.
- **U–V Q3/26E–Q4/26E and W 2026E:** forecast, calibrated to the FY26 guidance in the Q2-26 release (16-Jul-2026).
- **X–AB 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 55):
  - AC: modelling notes.
  - AE–AH: 5-year forward CAGR, 3-year and 2-year historical CAGR, and the 2026E-vs-2025 change / level.
  - AK–AO: scenario table.

## Basis
- **Policy:** each period is taken from the first filing that presents it on the GE Aerospace continuing-operations basis. GE HealthCare (spun 3-Jan-2023) and GE Vernova (spun 2-Apr-2024) are both in discontinued operations.
  - **FY2022–23 and the 2023 quarters:** recast comparatives in the 2024 Forms 10-Q / 10-K and the 2024 releases. Q1-23 = H1-23 − Q2-23; Q4-23 = FY2023 − 9M-23. The preliminary $bn recast in the 11-Apr-2024 8-K is used only for the Q1-23 per-share figures and shares.
  - **Q1-24:** from the Q1-25 10-Q and release comparatives. The Q1-24 10-Q still consolidated GE Vernova.
  - **Q2-24 onward:** as originally reported. Q4 statement and segment data = FY − 9M; Q4 non-GAAP and orders come from the Q4 release.
- **Balance sheet** from 31-Dec-2023 (31-Mar-2024 is not on the GE Aerospace basis). **Cash flow** from Q3-23: only H1-23 was re-presented, so Q1-23 and Q2-23 are blank. Q3-23 = 9M − H1, and so on.
- **Segments as reported in each period:**
  - Commercial Engines & Services (CES: equipment, services).
  - Defense & Propulsion Technologies (DPT: Defense & Systems, Propulsion & Additive Technologies).
  - The **Jan-2026 recast** (Aeroderivative CES → DPT; T&O site revenue and cost from Corporate & Other to the segments) applies from Q1-26. The recast figures are memo rows:
    - Q1–Q2/25 from the 2026 10-Qs;
    - FY2025 revised ($bn estimates: CES services $24.2B, equipment $7.7B, DPT $12.2B, Corporate $(1.0)B) from the Q4-25 release guidance table.

    2026 growth rates are computed against the recast basis.
- **Run-off insurance and U.S. tax equity** sit outside adjusted revenue, operating profit and adjusted EPS (company definitions), each in its own block.
- **Per-share data:** no splits in the window. The 1-for-8 reverse split was in Aug-2021. Q4 weighted shares = 4 × FY − (Q1 + Q2 + Q3).

## Model structure (Model tab)
- **Segment build:**
  - CES services and CES equipment revenue, and DPT revenue.
  - Eliminations as a % of segment revenue.
  - Segment operating profit = revenue × margin.
  - Plus adjusted Corporate & Other operating costs = operating profit (company non-GAAP), checked against the operating-profit bridge.
  - KPI memos: commercial and LEAP engine deliveries, implied equipment revenue per engine, internal shop-visit growth, defense engines, orders, book-to-bill, RPO.
- **Pending CPP acquisition** (8-K 8-Sep-2026: $11.75bn cash; $7bn cash + new debt; ~$2.0bn 2027E revenue; ~26x / 18x EBITDA without / with ~$200m net synergies):
  - toggle; closing assumed 30-Sep-2027 (one quarter in 2027E);
  - 25% of CPP revenue assumed sold to GE and eliminated (the margin stays in the group);
  - synergies phased 0 / 25 / 60 / 100 / 120% × a scenario realisation multiplier;
  - assumed PPA (PP&E 15%, intangibles 35% over 15 years, NWC 5%, goodwill the residual), in the PPA table with a 0-check;
  - $4.75bn acquisition debt at ~5%; $150m of integration costs in 2028E restructuring.

  All undisclosed terms are flagged as assumptions.
- **Future M&A lever:** bolt-ons beyond CPP (Base $0 in 2027–28E, then $0.5bn a year), at 4.0x EV / sales.
- **FY26 guidance calibration (2H-26E):**
  - **Revenue:** each line's FY26E target = FY2025 revised base × (1 + guided segment growth + one uniform Δ). Δ is solved so FY26 adjusted revenue = FY2025 $42,322m × (1 + high-teens: 19 / 18 / 17%). The 2H is split into Q3 / Q4 by the 2025 Q3:Q4 pattern. Base Δ = −0.4pp.
  - **Operating profit:** the CES and DPT guides plus the Corporate guide give the pre-calibration total. One uniform margin Δ on 2H CES + DPT revenue closes it to the total guide ($10.55 / 10.65 / 10.75B). Base Δ = −0.2pp.
  - **FCF:** the 2H change in customer advances (progress collections + contract liabilities) is solved so FY26 FCF = $8.9 / 9.05 / 9.2B. The ratio is then held.
  - **Information rows (not forced):** CES / DPT operating profit vs their guides (Base −$37m / −$13m); adjusted EPS vs $7.65–7.85 (Base $7.84, +$0.09 vs the mid-point).
  - **Mapping:** the numeric mapping of the qualitative guides (high-teens, ~20%, low 20s, LDD) is an assumption, labelled in the scenario table.
- **GAAP P&L from the build:**
  - Profit before tax = operating profit + insurance profit + tax equity − interest + non-operating benefit income − restructuring − separation (+ gains, nil).
  - Cost of services sold is the implied line.
  - Adjusted net income = (operating profit − interest) × (1 − adjusted ETR). GAAP net income = adjusted − after-tax items; tax is the residual.
  - Interest is calculated on opening balances.
- **Bridges** (checks vs published in every reported period):
  1. **Profit (GAAP) → operating profit (company):** − insurance profit, − U.S. tax equity, + interest, + non-operating benefit cost, + restructuring, + separation, + goodwill impairment, − gains, − NCI (±3 company rounding).
  2. **Net income → EBITDA → adjusted EBITDA:** a model definition, since GE publishes no EBITDA. Adjusted EBITDA = operating profit + D&A, with a pro forma memo for the CPP closing year.
  3. **Continuing net income to common → adjusted net income → adjusted EPS:** company items net of tax, a basis-difference row vs the company's starting figure, and a definition row (±4 / ±0.01).
  4. **CFOA → FCF:** − PP&E additions (+ PP&E dispositions from the Q3-25 definition), + separation and restructuring cash.
- **Other schedules:**
  - Cash flow, with discontinued operations and a cash-of-discontinued-operations bridge to continuing cash.
  - Buybacks; balance sheet with a restricted-cash memo (CF continuing cash − BS cash).
  - Working capital (DSO / DIO / DPO, contract assets, advances, SD&A, other current liabilities).
  - CPP / M&A PPA.
  - Debt: 10-K maturities refinanced; CPP debt; revolver / CP / incremental notes to an $8bn minimum cash, with a headroom memo vs the $3bn revolver.
  - Leverage-target buybacks; ratios (NOPAT on operating profit, insurance excluded from RONTA); valuation.
- **DCF basis:**
  - NOPAT = (operating profit − restructuring and separation) × (1 − 17%), with a total D&A add-back. Operating profit is full-cost: after amortization and stock-based compensation.
  - Insurance, tax equity and pension income are excluded.
  - CPP consideration is in FY2027E row 22.
  - Run-off insurance is not deducted in the EV bridge (assumed self-funding).

## Key forecast assumptions (Base)
- **Growth:**
  - CES services: FY26 guided low 20s (22%), then 14 / 11 / 9 / 8 / 7% for 2027–31E.
  - CES equipment: ~20% (FY26), then 12 / 10 / 8 / 6 / 5%.
  - DPT: LDD (11%), then 8 / 7 / 6 / 6 / 5%.
- **Margins:** CES 26.8% → 28.2%; DPT 13.0% → 15.0%. Adjusted Corporate & Other costs −2.5% of adjusted revenue; eliminations −4.2% of segment revenue.
- **Insurance:** revenue −3% a year at a 22% margin. **U.S. tax equity:** −$280m pre-tax / +$320m tax credits a year. **Non-operating benefit income:** $680m in 2027E, falling to $600m.
- **Costs and capital spending:** adjusted ETR 16.5% (2H-26E), then 17%; capex 2.8–3.2% of adjusted revenue; D&A on PP&E 1.9%; 10-K amortization schedule + CPP PPA.
- **Shareholder returns:** DPS $0.47 a quarter in 2026, then +15% a year. 2H-26 buybacks $5.0 / 4.0 / 3.0B (Bull / Base / Bear). 2027E+ buybacks plug to net debt / adjusted EBITDA of 1.5 / 1.0 / 0.5x.
- **Results:** FY2026E adjusted revenue $49.9bn, operating profit $10.65bn, adjusted EPS $7.84, FCF $9.05bn. 2027E adjusted EPS $9.13; 2031E $15.00.
- **Share price $308.00:** provided by the user (12-Oct-2026). It is the input at `Model!W` in the valuation block; update it to market. For reference, the Q2-26 10-Q average repurchase price was $292.17.
- **Guidance source:** all guidance used is from EDGAR (8-K Ex. 99.1 releases); no guidance from outside EDGAR (call transcripts, decks not filed) was used. Numeric mappings of qualitative guides are labelled assumptions.

## Data corrections
None. Known differences are documented rather than corrected:
- **Rounding:** company rounding of $1–3m in the non-GAAP bridges (GE computes totals from unrounded numbers; check tolerances are stated in each label).
- **FY2025 FCF quarters:** they don't sum to the FY figure, because the Q3-25 release added PP&E dispositions to the definition and re-presented prior periods (FY2024 $6,203m vs $6,089m first published).
- **Q1-24 NCI:** the Q1-25 10-Q comparative shows total NCI including GE Vernova ($27m), so continuing NCI ($3m) comes from the EPS note.

## Sources
SEC EDGAR only (CIK 0000040545):
- **Forms 10-Q** for Q2-24 to Q2-26 (Q1-24 was checked and not used because it consolidated GE Vernova); **Forms 10-K** for FY2024 and FY2025.
- **Form 8-K Item 2.02 earnings releases (Ex. 99.1)** for Q2-24 to Q2-26. The Q1-24 release reported GE consolidated and is not used.
- **Other 8-Ks:**
  - 11-Apr-2024 (Item 7.01, supplemental GE Aerospace financial information for 2023);
  - 8-Sep-2026 (CPP acquisition: Ex. 99.1 presentation, Ex. 99.2 release).
- **XBRL company facts:** used for the cross-check and dividends per share.

The investor-relations site is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_cf_ytd.json` holds the year-to-date cash-flow statements and `data/_xbrl.json` the XBRL subset.
- `manual_items.json` holds the FY26 guidance and its history, the FY2025 revised segment base, CPP terms and assumptions, debt maturities, the amortization schedule, buyback authorization, dividends, tax rates and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export GE_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 630 checks: statement arithmetic, segment sums, bridges vs published, EPS, cash and balance-sheet tie-outs, and quarters vs years. The only known exception is the FY2025 FCF quarter sum (definition change).
   4. `python3 xbrl.py` cross-checks against XBRL company facts (88 facts).
3. Build: `python3 build.py --snap --recalc` writes `../GE_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../GE_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../GE_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../GE_Model.xlsx --extra WWD 382.17 Woodward` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML (ranges cut to FY2023–2031E).
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `tables.py`: row reader for the text files (signs, V% layouts, statement anchors).
- `extract.py`: per-period extraction (statements, EPS notes, MD&A segment / Corporate tables, release non-GAAP tables, cash flow YTD, balance sheets, Jan-2026 recast comparatives).
- `normalize.py`: basis rules, flat model keys, discrete quarterly cash flow, Q4 shares, manual items.
- `check_data.py`: data consistency checks. `xbrl.py`: XBRL cross-check.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
