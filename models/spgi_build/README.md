# SPGI model build kit

`models/SPGI_Model.xlsx` is the S&P Global Inc. (NYSE: SPGI) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CC2`, scenario table in `Model!CK:CO`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). FY2026E (Q4 under way at the valuation date) is the base year; net debt and NCI are taken at 31-Dec-2026E and the explicit years are 2027E–2031E.
  - Charts: division contribution to revenue growth, adjusted EBITDA / operating profit, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
- **C–E FY2010–FY2012:** annual. FY2010–11 are continuing operations as recast after the McGraw-Hill Education sale (FY2012 10-K; Q4-2012 release comparative); FY2012 as reported. FY2010–11 have no balance sheet or cash flow on this basis.
- **F–BR Q1/13–Q4/25 with FY subtotals; BS–BT Q1/26–Q2/26:** grouped and collapsed like the template.
- **BU–BV Q3/26E–Q4/26E, BW 2026E:** forecast, calibrated to the FY26 outlook (Q2-26 release, 28-Jul-2026).
- **BX–CB 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 3): CC notes, CE–CH CAGRs (5Y fwd '26–'31, 5Y, 10Y, 15Y), CK–CO scenario table.

## Basis
- **Policy:** hybrid recast.
  - FY2010–11: continuing operations (McGraw-Hill Education / Broadcasting in discontinued operations).
  - FY2012–FY2024 and Q1/13–Q4/24: as originally reported in each period's own release (Mobility, Engineering Solutions and the other divested businesses included while owned).
  - 2025 quarters, FY2025 and Q1–Q2/26: Regulation S-X Article 11 pro forma continuing operations excluding Mobility (spun off as Mobility Global, NYSE: MBGL, on 1-Jul-2026), from the 8-K/A of 6-Jul-2026 (Ex. 99.1 quarterly recast and pro forma statements; Ex. 99.2 FY2023–25 and Q1-26 pro forma statements) and the Q2-26 release (Exhibits 5–7). This is the base the FY26 guidance is measured against. The pro forma includes the Transition Services Agreement income ($9m a quarter in 2025, $6m in 2026). Reported net income attributable − pro forma continuing net income is shown as discontinued operations, so net income and EPS tie to the reported figures.
  - Balance sheet and cash flow stay as reported (including Mobility to 30-Jun-2026). FY2023–24 pro forma figures (annual only) are memo rows.
- **Recasts not applied** (cell comments; known `check_data` exceptions): McGraw Hill Construction moved to discontinued operations in Q3-14, so Q1–Q2/14 include it and Σ quarters ≠ FY2014; the 2014 cost-allocation change and the Q1-18 pension reclassification (ASU 2017-07) recast prior-year comparatives that the model keeps as first reported; FY2019 opex reclassification (~$8m).
- **Divisions by lineage:**
  - Ratings: S&P Ratings → S&P Global Ratings.
  - Indices: S&P DJ Indices (73% / 27% JV with CME Group from Jul-2012).
  - Energy: Commodities & Commercial 2010–15 (incl. J.D. Power to Sep-2016, Aviation Week, McGraw Hill Construction to 2014) → Platts → Commodity Insights (2022) → Energy (recast 2025+ with 451 Research and Maritime & Trade).
  - Market Intelligence: S&P Capital IQ → Market Intelligence (SNL from Sep-2015; IHS Markit financial services from Mar-2022; recast 2025+).
  - The combined Market & Commodities Intelligence segment (Q4/16–2017) is a legacy row; its revenue is split into MI / Platts from the company's organic-revenue table. Mobility (Mar-2022 to Jun-2026) and Engineering Solutions (to May-2023) are legacy rows.
- **Revenue by type** (release revenue-information exhibit): Ratings transaction / non-transaction; Indices asset-linked fees / exchange-traded derivatives / subscriptions; Energy and MI subscription / non-subscription / royalties or recurring variable. Earlier labels are mapped to the current lines, and a "not split" row closes any period without a type table.
- **Per-share data:** no stock splits since May-2005; no share classes.
- **Cash flow:** XBRL year to date (2013–15 10-Qs tag continuing and discontinued cash flows separately; they are summed); quarters derived (Q4 = FY − 9M). Distributions to NCI come from the releases where the 10-Q tag is missing (2018–21).

## Model structure (Model tab)
- **Division build:** revenue by type × division adjusted operating margin = division adjusted OP (company non-GAAP: OP + non-GAAP adjustments + deal-related amortization) − adjusted corporate unallocated + adjusted equity income (OSTTRA, sold Q4-2025) = adjusted operating profit, checked against the published figure. A company rounding residual row closes the build in the published periods.
- **Future M&A lever:** spend ÷ EV/revenue (8x), 30% adjusted margin, 35% intangibles amortized over 15 years (deal-related, adjusted out), goodwill for the rest.
- **FY26 outlook calibration:**
  - Revenue: one uniform Δ on the 1H-26 y/y growth of every revenue line, solved so that FY26 revenue = FY2025 pro forma $13,589m × (1 + 7.9% / 6.9% / 5.9%). Base Δ is −7.6pp: guidance implies ~3% 2H growth after +10.8% in 1H.
  - Margins: one uniform Δ on the division margins (prior-year quarter + 1H drift), solved in closed form so that FY26 adjusted EPS = $17.75 / $17.625 / $17.50. The solve runs through tax, adjusted interest, other income and NCI as a ratio to Indices adjusted OP.
  - Point estimates from the outlook: adjusted corporate $190m, deal amortization $785m, GAAP interest $375m, tax 22.5%, capex $200m.
  - Information rows, not forced: GAAP EPS $16.35–16.60 (model −$0.04 vs mid), adjusted margin +35–60 bp (model +48 bp), organic cc +6–8%.
- **GAAP P&L from the build:** OP = adjusted OP − deal amortization − non-GAAP adjustments (Q4/26E includes an assumed ~$250m gain on the geoscience sale to SLB, implied by the GAAP-vs-adjusted margin guidance and the −$1.20 EPS-bridge item). Selling and general expenses are implied. Interest is calculated on opening balances. NCI = ratio × Indices adjusted OP.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **OP → adjusted OP:** company items grouped as severance / restructuring, acquisition and merger, disposition and separation, gains, legal, impairments and other, plus deal-related amortization (added back from 2016; FY2011–15 adjusted OP included amortization, flagged). The company's per-period item wording is in cell comments.
  2. **Net income → EBITDA → adjusted EBITDA:** a model definition (adjusted OP + depreciation); S&P Global publishes no EBITDA.
  3. **Net income → adjusted net income → adjusted EPS:** the tax effect is derived from published adjusted net income. Q4-14 uses the company's 276.2m adjusted share count (GAAP loss quarter). Q1-22 and FY2022 adjusted measures were published only pro forma for IHS Markit, so the model rebuilds the actual scope (from published after-tax totals; FY = Σ quarters) and the check reads n/p.
- **Mobility spin-off (Q3/26E):** the 31-Mar-2026 pro forma Mobility balances are removed (assets $12,995m, liabilities $1,178m), along with the $1,981m Mobility notes. The equity reduction ($9,836m) is the balancing figure. The $1,974m net distribution was already in cash at 30-Jun-2026; Mobility's own cash ($121m) leaves through a financing line. Replace with the Q3-26 10-Q balances when filed.
- **Other schedules:**
  - Cash flow, buybacks, balance sheet and working capital: year-end ratios excluding Mobility, with unearned revenue at 29% of revenue.
  - IHS Markit PPA (Q1-22, preliminary).
  - Debt: notes refinanced at maturity; prior year-end CP above $500m is termed out; CP to a $1.5bn minimum cash within the $2.0bn facility.
  - Leverage-target buybacks for 2027E+: net debt / adjusted EBITDA of 1.75x / 1.5x / 1.25x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT = (adjusted EBITA, i.e. adjusted OP before deal amortization and after SBC, − severance / acquisition / disposition / legal cash costs) × (1 − 22.5%), with a depreciation-only add-back.
  - UFCF after capex and bolt-on M&A.
  - EV bridge deducts net debt plus redeemable NCI (CME's 27% of S&P DJI, carrying value) and other NCI.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.0) are assumptions, because rate sources are not reachable from the build environment.

## Key forecast assumptions (Base)
- **2H-26 buybacks:** $5.75bn (Bull $6.0bn, Bear $5.5bn), from the company's ">$7bn in 2026" with $1.5bn done in 1H.
- **Revenue growth 2027E–31E:**
  - Ratings transaction 3% → 5%; non-transaction 7% → 6%.
  - Indices asset-linked fees 10% → 8%; ETD 5%; subscriptions 8% → 7%.
  - Energy 6%; Market Intelligence 6–6.5%.
- **Adjusted margins:** Ratings 66.5–67%, Indices 71.5–72.5%, Energy 47.5–49%, MI 35–37%. Adjusted corporate 1.3% of revenue.
- **Other drivers:**
  - Deal amortization: 10-K schedule less Mobility $303m (assumption).
  - Severance $40m p.a.; M&A $500m p.a. (assumption).
  - Capex 1.4% of revenue; DPS +5% p.a.; tax 22.5%.
  - Notes coupon 3.35% → 3.8% as maturities refinance at ~5%.
- **Share price $415.00** (user-provided, 12-Oct-2026; the Q2-26 average repurchase price was $414.85). Update it at `Model!BW` in the valuation block.

## Data corrections
- None. Known data exceptions (documented, not corrected; `check_data.py` lists them): FY2014 Σ quarters ≠ year (McGraw Hill Construction to discontinued operations in Q3-14); FY2019 opex reclassification; the 2025 pro forma quarterization of adjusted OP sums to $6,971m vs $6,974m for the year. Published FCF is compared only where the release CFO equals the 10-Q / 10-K CFO (Q1-13, Q1-15, Q1-16 differ).

## Sources
SEC EDGAR only (CIK 64040):
- Forms 10-K FY2012–FY2025 and 10-Q Q1-13 – Q2-26.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4-12 – Q2-26 (the Q4-16 release was filed under Items 2.01 / 7.01).
- 8-K of 2-Jul-2026 (Mobility separation completed), 8-K/A of 6-Jul-2026 (pro forma and recast financial information), 8-K of 6-Jul-2026 (Market Intelligence operating model).
- XBRL company facts for the face statements (as first filed), SBC, deferred tax, dividends per share and shares.

The investor-relations site is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings and `data/_releases.json` maps each release to its quarter.
- Each `data/<period>.json` lists its source URLs. These were transcribed from the release text by parallel agents on one schema (`EXTRACTION_SCHEMA.md`) and self-checked with `check_rec.py`.
- `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the 2025–1H26 pro forma recast, the Mobility spin balances, the FY26 guidance, the debt at 30-Jun-2026, the amortization schedule, buybacks, divestitures, the IHS Markit PPA and the share price, each with its source.

No guidance from outside EDGAR is used (none is marked unverified).

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export SPGI_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 releases.py`.
   3. Transcribe any new release to `data/<period>.json` per `EXTRACTION_SCHEMA.md` and check it with `python3 check_rec.py data/<period>.json`.
   4. Refresh the XBRL subset with `python3 -c "import xbrl; xbrl.dump_subset()"`.
   5. `python3 check_data.py` runs 980 checks: statement arithmetic, division sums, adjusted bridges vs published, EPS, cash and balance-sheet tie-outs, quarters vs years, and XBRL cross-checks. It should report 0 unexplained failures and 8 known exceptions.
3. Build: `python3 build.py --snap --recalc` writes `../SPGI_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 inspect_model.py ../SPGI_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 cyc.py ../SPGI_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../SPGI_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`, `releases.py`: EDGAR filings index, downloads, HTML → text, release-to-quarter map.
- `xbrl.py`: XBRL company-facts helper (calendar year; earliest-filed values).
- `normalize.py`: basis rules, division lineage mapping, revenue-type mapping, pro forma recast overlay, XBRL statements, discrete quarterly cash flow.
- `check_rec.py`, `check_data.py`: per-record and whole-dataset consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
