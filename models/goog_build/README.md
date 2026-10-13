# GOOG model build kit

`models/GOOG_Model.xlsx` is the Alphabet Inc. (NASDAQ: GOOG) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CF2`, scenario table in `Model!CN:CR`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Net debt is taken at YE2026E, so the 2026E UFCF is excluded from the PV sum. Fade-period capex converges to D&A + NOPAT × g ÷ terminal RONIC (input, 20%).
  - Charts: Google Services / Google Cloud contribution to revenue growth, adjusted EBITDA and operating income, returns (2011–2030E).
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BX Q1/26–Q2/26:** grouped and collapsed like the template.
- **BY–BZ Q3/26E–Q4/26E, CA 2026E:** forecast (no company guidance; 1H26 run-rate with scenario shifts).
- **CB–CE 2027E–2030E:** scenario forecast.
- **Right of the forecast** (same columns as the template): CF notes, CH–CK CAGRs (5Y fwd '25–'30, 5Y, 10Y, 19Y), CN–CR scenario table.

## Basis
- **Policy:** consolidated statements as originally reported in each period's own 10-K / 10-Q. Revenue types and segment revenue / operating income come from the latest filing that presents the period (recast basis), with the earlier structures as first reported kept as memo rows.
- **Registrants:** Google Inc. (CIK 1288776) to Q3-2015; Alphabet Inc. (CIK 1652044, holding-company reorganization of 2-Oct-2015) from the FY2015 10-K.
- **Recasts and discontinued operations** (cell comments on the affected cells):
  - Motorola Home (2012–13) and Motorola Mobile (2014) in discontinued operations as reported.
  - Q2-15 10-Q revised income tax for 2008–Q1-15: Q1-15 kept as first reported, so Σ 2015 quarters exceeds FY2015 net income by $71m.
  - 2019: performance fees moved from operating expenses to OI&E; 2017–18 segments recast. An explicit "segment recast / basis difference" row carries the $1,203m 2018 difference.
  - Google Cloud split out of Google Services from Q4-20 (recast to 2018); Google DeepMind moved to Alphabet-level activities in 2023.
- **Revenue types:** Search & other, YouTube ads, Network, subscriptions / platforms / devices ("Google other" to Q4-23), Cloud: annual from FY2017, quarterly from Q1-19. Earlier periods sit in a derived "not split" row. The legacy split as first reported (Google websites / properties, Network members, other, Motorola Mobile, Other Bets; 2006–2019) is a memo block.
- **Segments:** Google Services / Google Cloud / Other Bets / Alphabet-level activities: annual from FY2018, quarterly from Q1-20. Google / Other Bets (2015–20) and Google / Motorola Mobile (2012–13) are memo rows.
- **Per-share data:** split-adjusted by the filing date of each source document. The 2-for-1 Class C dividend of 2-Apr-2014 gives ×40 before 3-Apr-2014; the 20-for-1 split of 15-Jul-2022 gives ×20 before that date. Shares = Class A + B + C. Diluted shares = Class A diluted (assumes conversion of Class B) + Class C diluted. EPS as reported = Class A, which equals Class C except Q2-15 / FY2015, when the $522m Class C adjustment payment raised Class C EPS; the payment is an allocation row. Q4 weighted shares = 4 × FY − Σ Q1–Q3. Q4 EPS comes from the Q4 release.
- **Cash flow:** quarters derived from year-to-date statements (Q4 = FY − 9M). Cash includes restricted cash from 2018; a memo row reconciles to balance-sheet cash. In Q1–Q3/14 the cash-flow statement cash included $160m of Motorola Mobile cash held for sale.

## Model structure (Model tab)
- **Revenue build:** Search & other, YouTube ads, Network and subscriptions / platforms / devices make up Google Services; plus Google Cloud, Other Bets and hedging.
  - Q3–Q4/26E: prior-year quarter × (1 + 1H26 y/y growth + scenario shift).
  - Optional FY26 revenue target (blank by default): if entered, the 2H shift is solved closed-form with a sensitivity helper row.
  - 2027E–2030E: scenario levers per revenue type.
  - KPIs: TAC (release), revenue backlog / RPO (XBRL; Cloud $513.9bn at 30-Jun-2026), employees.
- **Segment operating income:** segment revenue × margin, with Other Bets as a $ lever and Alphabet-level costs as % of revenues.
  - Q3–Q4/26E Services margin = Q2-26 margin + last year's sequential change; Cloud margin = Q2-26 held; plus a scenario shift.
  - Alphabet-level costs = prior quarter × Q2/Q1-26 sequential growth.
  - Build vs consolidated check, with the explicit recast / basis-difference row.
- **M&A lever:** spend ÷ EV/sales (15x), with intangibles at 28% of spend amortized over 8 years.
- **Pending GFiber divestiture:** modelled at 31-Dec-2026 ($1.5bn cash, $2.0bn note and a 49.99% equity interest; no gain assumed).
- **GAAP P&L from the build:**
  - Operating income = segment build. Cost of revenues is the balancing line; R&D, S&M and G&A are % of revenues.
  - OI&E = interest income on opening cash and marketable securities − interest on opening debt (equity gains not forecast).
  - Tax at 18% in Q3–Q4/26E, then 17.5%.
  - The preferred dividend is deducted and the preferred is if-converted in diluted EPS until May-2029.
- **GAAP → adjusted bridges** (model definitions; Alphabet publishes no EBITDA or adjusted EPS):
  1. **Income from operations → adjusted OI:** adds back only items the company reconciled in a published non-GAAP table: EC fines (Q2-17 $2,736m, Q2-18 $5,071m, Q1-19 $1,697m, Q3-25 $3,457m) and severance / office-space charges (Q1-23 $2,558m, Q1-24 $716m). Checked against every published figure (Q2-17, Q2-18, Q1-19, Q1-23, Q1-24, Q3-25).
  2. **Net income → EBITDA → adjusted EBITDA:** EBITDA = operating income + D&A (stock-based compensation not added back) + the adjusting items. Adjusted EBIT = adjusted OI (full-cost).
  3. **Net income → adjusted net income → adjusted EPS:**
     - removes discontinued operations, the operating items, equity-security gains / losses (ASU 2016-01, 2018+; the 2008 impairment), and the Tax Act (Q4-17);
     - tax effect at the statutory rate (35% to 2017, 21% after; fines not deductible).
     - Company non-GAAP EPS is a memo with checks: Google's excl.-SBC measure to Q4-16, rebuilt with the published SBC and derived tax effect; EPS excluding the EC fine / Tax Act for Q2-17, Q4-17, Q2-18 and Q1-19.
- **Other schedules:**
  - Cash flow, share schedule and the 6.25% mandatory convertible preferred: dividends accrued / paid, conversion rate 2.263–2.829 at the forecast price, conversion on 15-May-2029.
  - Balance sheet and working capital.
  - Wiz + Intersect PPA (Q1-26 column).
  - Debt: notes repaid at maturity and refinanced. Marketable securities are the liquidity buffer: sold to keep cash at $25bn before commercial paper is drawn.
  - Net-cash-floor buybacks 2027E+ (net debt / adjusted EBITDA −0.10x / −0.25x / −0.40x).
  - Ratios and valuation. Invested capital and EV exclude non-marketable equity stakes at carrying value (UBER lesson).
- **DCF basis:**
  - NOPAT on adjusted EBIT (full-cost, after SBC) less cash adjusting items, with the full D&A add-back.
  - UFCF after capex and M&A.
  - The equity bridge adds non-marketable equity stakes at carrying value.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.05) are assumptions: Treasury / FRED data are not reachable from the build environment.

## Key forecast assumptions (Base)
- **Revenue growth 2027E–2030E (scenario table):**
  - Search & other 11% → 7%; YouTube ads 11% → 8%; Network −3% p.a.; subscriptions / platforms / devices 14% → 10%.
  - Cloud 45% → 20% (1H26 +73%; $513.9bn backlog).
  - Other Bets −30% in 2027E (GFiber deconsolidated), then +25%.
- **Margins:** Google Services 42.0% → 38.5% and Google Cloud 33% → 32%. They step down as AI-infrastructure depreciation (6% → 14% of revenues) outpaces revenue; adjusted EBITDA margin rises 41% → 44.5%.
- **Costs:** Other Bets $(8.0)–(9.0)bn; Alphabet-level costs 5.0% → 4.6% of revenues.
- **Capex:** $200bn in 2026E — mid-point of the $195–205bn outlook, which is UNVERIFIED (Q2-26 call only). 2027E–30E $250–300bn (assumption).
- **Other drivers:**
  - Depreciation 11.5% of opening net PP&E.
  - Stock-based compensation 6.5% of revenues.
  - Tax 17.5%.
  - DPS +5% p.a.
  - Equity-plan issuance 120m shares p.a.; M&A $5bn p.a.
- **Share price $350.00:** user-provided, 13-Oct-2026. The latest SEC-filed Class C price was $340.45 (Form 4 sale, 30-Sep-2026). Update it at `Model!CA407`.

## Data corrections
- None. Known data exceptions (documented in `manual_items.json` → `known_exceptions` and in check-row comments):
  - FY2015 Σ quarters vs year net income: +$71m (Q1-15 tax revision).
  - Q3-16 free cash flow: the release figure ($7,291m) vs the 10-Q-derived figure ($7,262m).
  - 2017–18 segment recast (performance fees).
  - Q1–Q3 2014 cash held for sale.
  - 2013 legacy segments: unallocated items are not tagged by segment.

## Sources
SEC EDGAR only (CIK 1288776 Google Inc.; CIK 1652044 Alphabet Inc.):
- Forms 10-K / 10-Q 2006–Q2-2026. Statements come from the XBRL instance document of each filing (from Q2-2009); FY2006–08 from the 10-K text.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), 2006–Q2-2026: Q4 EPS, free cash flow, TAC, employees, Google non-GAAP to Q4-16, and the EC-fine / severance / Tax Act reconciliations.
- XBRL company facts of both registrants, used as a cross-check of revenue, operating income, net income, CFO and total assets.

The investor-relations site (abc.xyz) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes 263 filings, and each `data/<period>.json` lists its source URLs.
- `manual_items.json` holds:
  - the company-reconciled adjusting items and published adjusted figures;
  - splits and known exceptions;
  - the UNVERIFIED capex outlook;
  - debt, preferred, equity-raise, buyback and dividend facts;
  - the Wiz / Intersect PPA, GFiber and the share price.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export GOOG_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 966 checks: statement arithmetic, EPS, segment and revenue-type sums, cash and balance-sheet tie-outs, Q4 vs release, free cash flow vs release, Google non-GAAP EPS, quarters vs years, and XBRL company facts. The known exceptions are listed in the script.
3. Build: `python3 build.py --snap --recalc` writes `../GOOG_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../GOOG_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../GOOG_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../GOOG_Model.xlsx --extra WWD Woodward 382.17 Aerospace --allow Model!CF2` → 0 hits. GOOG's own switch cell is CF2, as in the template.

## Files
- `fw.py`: column map (template columns), style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts, sets the DCF fade reinvestment and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index (both CIKs), downloads (incl. XBRL instances), HTML → text.
- `xinst.py`: XBRL instance parser (contexts, dimensions, facts), cached per filing.
- `pre09.py`: FY2006–08 statements from the 10-K text.
- `parse_release.py`: earnings-release parser (Q4 EPS, FCF, TAC, employees, Google non-GAAP).
- `extract.py`: per-period extraction to `data/<period>.json` (statement facts, YTD cash flow, dimensional revenue types and segments, legacy split, release data).
- `normalize.py`: basis rules, split adjustment, Q4 derivation, discrete cash flow, flat model keys.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
