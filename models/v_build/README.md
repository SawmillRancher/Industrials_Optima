# V model build kit

`models/V_Model.xlsx` is the Visa Inc. (NYSE: V) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit (same 30-September fiscal year):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CE2`, scenario table in `Model!CM:CQ`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates are moved to Visa's 30-September fiscal year ends. FY2026E (ended 30-Sep-2026, just before the valuation date) is the base year, so the explicit years are FY2027E–FY2031E and net debt is taken at 30-Sep-2026.
  - Charts: net revenue growth split into payments-volume growth and net-revenue-yield change, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 September; 2026 = Oct-2025 – Sep-2026)
- **C–G FY2008–FY2012:** annual, as originally reported. FY2008 is the first Visa Inc. 10-K year (IPO 19-Mar-2008; reorganization Oct-2007).
- **H–BT Q1/13–Q4/25 with FY subtotals; BU–BW Q1/26–Q3/26:** grouped and collapsed like the template.
- **BX Q4/26E, BY 2026E:** forecast, calibrated to the Q4 FY26 outlook given on the Q3 FY26 call (UNVERIFIED, see Basis).
- **BZ–CD 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column − 1): CE notes, CG–CJ CAGRs (5Y fwd '26–'31, 5Y, 10Y, 17Y), CM–CQ scenario table.

## Basis
- **Policy:** as originally reported.
  - Q1–Q3 statements come from the 10-Q three-month column, which is identical to the earnings release as first published.
  - Q4 three-month figures come from the Q4 release where its tables are text (FY2013–17, FY2021+). For FY2018–20 they are fiscal year (10-K) − nine months (Q3 10-Q), because those releases are slide images.
  - Every tabular Q4 release was compared with FY − 9M and agrees within $1m.
- **Image-based releases:** Q1 FY2018 – Q2 FY2021 (except Q4 FY18 – Q2 FY19, which are plain text) are Workiva slide exhibits. Their tables are images with a hidden white text layer, which `period_index.py` writes to `$V_SRC/txt_hidden`. The non-GAAP reconciliations were read from that layer; the statements come from the 10-Q / 10-K.
- **Per-share data:**
  - 4-for-1 split effective 18-Mar-2015: shares ×4 and per-share ÷4 for every document filed before that date (applied in `normalize.py`).
  - Class A EPS is on an as-converted basis: diluted class A shares include class B / C common and series A / B / C preferred as converted. Net income ÷ diluted class A shares therefore reproduces diluted EPS (±$0.01).
  - Exception: FY2008, where the company computed EPS on income allocated to class A from the IPO. It is flagged n/m.
  - Q4 FY18–20 diluted shares = 4 × fiscal year − (Q1 + Q2 + Q3).
- **Revenue:** one reportable segment. Revenue by category (service, data processing, international transaction, other) less client incentives ("volume and support incentives" to FY2012) = net revenue. Categories are on the face of the statement of operations to FY2018 and in the revenue note / MD&A from FY2019 (ASC 606). FY2008 uses the 10-K MD&A table ("service fees" etc.).
- **KPIs (10-Q / 10-K MD&A):**
  - Nominal payments volume ($bn): the calendar quarter that drives the period's service revenue, i.e. one quarter earlier. Q4 = twelve months − nine months.
  - Processed transactions (millions). FY2008 is not tabulated on this basis.
- **Cash flow:**
  - Quarters are derived from year to date (Q4 = FY − 9M).
  - From FY2019 (ASU 2016-18) the cash basis includes restricted cash and equivalents (U.S. litigation escrow, customer collateral, other). The BS cash vs CF cash check therefore applies before FY2019, and a derived "restricted cash" memo row covers later periods.
  - Litigation-escrow deposits and payments were financing flows to FY2018.
- **Non-GAAP:** each period's own release, as first published. Changes in the definition are flagged in the definition rows; a period whose release presents no reconciliation for it shows adjusted = GAAP and is marked n/p. Those periods are:
  - Q1–Q3 FY13 and FY2013;
  - Q1–Q3 FY14;
  - Q1–Q2 FY15 and Q4 FY15;
  - Q1, Q3 and Q4 FY17;
  - Q2 FY18;
  - Q1–Q3 FY19. The FY2020 releases later re-presented these under the new definition; the model keeps the originally published basis.
- **Guidance:** since FY2020 Visa gives its outlook only on the earnings call (no outlook in the 8-K release). The Q4 FY26 outlook used here comes from secondary summaries of the 28-Jul-2026 call found by web search, and is labelled **UNVERIFIED** in the header, the scenario table and every row that uses it.
  - Some summaries also cite full-year net revenue growth "at the low end of low teens". That cannot be reconciled with 9M FY26 growth of +15.3% (it would imply about +3% in Q4), so it is not used.

## Model structure (Model tab)
- **Revenue build:**
  - Service revenue = nominal payments volume × service yield.
  - Data processing revenue = processed transactions × revenue per transaction.
  - International transaction and other revenue are driven by growth.
  - Client incentives = % of gross revenue.
  - Future acquisitions are added on top.
  - Checks: the build vs reported net revenue, and a growth decomposition into payments volume and net revenue yield.
- **Q4 FY26 calibration (Q4/26E):**
  - **Payments volume is published:** the Q3 FY26 release gives +11% nominal for the quarter ended 30-Jun-2026, which drives Q4 service revenue.
  - **Revenue:** one uniform Δ on service yield, data processing yield, and international / other revenue growth solves Q4 net revenue to Q4 FY25 × (1 + 14% / 13% / 12%). The solve is closed-form (sensitivity helper row).
  - **EPS:** one Δ on non-GAAP operating-expense growth solves Q4 non-GAAP EPS to Q4 FY25 × (1 + 15% / 14% / 13%). It works through required adjusted operating income = EPS × shares ÷ (1 − t) − adjusted non-operating income.
  - **Information rows:** implied FY26 revenue and EPS growth, and Q4 opex growth (Base +14.4% vs "low double digits" in the unverified commentary).
- **Non-GAAP operating expenses and adjusted operating income:**
  - Adjusted opex = GAAP opex − operating adjusting items, checked against the published non-GAAP opex.
  - 2027E+: net revenue × (1 − adjusted operating margin lever).
  - Expense lines are allocated from adjusted opex by the 9M FY26 mix, and adjusting items are added back on their GAAP line (severance → personnel, acquired amortization → D&A, acquisition costs → G&A, litigation → litigation provision).
- **GAAP P&L from the build:** GAAP operating income = adjusted OI − operating items. Interest is calculated on opening debt; investment income = yield × opening cash and investments. Tax = non-GAAP tax + the tax effect of the items.
- **Bridges** (checks vs published in every reported period):
  1. **GAAP operating income → adjusted operating income** (company non-GAAP opex). Items: litigation provision, acquired-intangible amortization, acquisition costs, severance / restructuring / lease consolidation, Visa Europe items, other. The company's labels for each period are in cell comments.
  2. **Net income → EBITDA → adjusted EBITDA:** a model definition, because Visa publishes no EBITDA. It continues to adjusted EBIT, full-cost (for NOPAT / DCF).
  3. **Net income → non-GAAP net income → non-GAAP EPS:**
     - Historical tax effect = published non-GAAP NI − GAAP NI − pre-tax items. This covers the FY2008–09 normalized-41% tables and tax-only items: TCJA, deferred-tax remeasurements, tax-reserve reversals.
     - Forecast: items × the non-GAAP tax rate.
- **Other schedules:**
  - Cash flow; buybacks on as-converted shares, starting from a 30-Jun-2026 proxy (Q3 weighted diluted − half the Q3 repurchases); balance sheet.
  - Working capital: settlement balances, client incentives and other items as fiscal-year-end ratios to net revenue. Collateral, escrow and accrued litigation are held.
  - Visa Europe PPA (Q3 FY16).
  - Debt: senior notes repaid at maturity and refinanced; commercial paper as the plug to $12bn minimum cash.
  - Leverage-target buybacks, 2027E+: net debt (debt − cash − investment securities) / adjusted EBITDA of 0.50x / 0.35x / 0.25x.
  - Ratios and valuation.
- **DCF basis:**
  - NOPAT on adjusted EBIT, full-cost (after acquired amortization and share-based compensation), less acquisition and severance costs.
  - Covered-litigation provisions are excluded: they are funded via the escrow and class B conversion-rate reductions, which show up in the share count.
  - Preferred stock is in the as-converted share count, not deducted; there is no NCI.
  - Market inputs are assumptions (risk-free 4.25%, ERP 5%, beta 0.95), because rate sources are not reachable from the build environment.

## Key forecast assumptions (Base)
- **Payments volume:** +8.5% → +7.5% a year 2027E–31E. FY2023–25 +5–7.5%; 9M FY26 +10.2% nominal.
- **Processed transactions:** +9% → +8% (FY2023–25 ~+10%).
- **Yields:** service yield +1.0% → +0.5% a year; data processing per transaction +2.5% → +1.5%.
- **Revenue categories:** international +10% → +8%; other (value-added services) +22% → +13%; client incentives 28.9% → 29.7% of gross revenue (FY2025 28.3%).
- **Margin:** adjusted operating margin 67.5% → 68.2% (FY2025 67.7%).
- **Non-GAAP tax rate:** 18.5%.
- **Capex:** 3.5–3.7% of net revenue.
- **Share-based compensation:** 2.3% of net revenue.
- **DPS:** +12% a year.
- **M&A:** $1.0bn a year (assumption).
- **Adjusting items:** no litigation provisions or severance assumed after Q3 FY26. Acquired amortization runs $230m → $80m (assumption from the 10-K schedules).
- **Base outputs:**
  - FY26E net revenue $45.9bn (+14.7%), non-GAAP EPS $13.19 (+15.0%), GAAP EPS $12.50;
  - FY31E net revenue $73.9bn, non-GAAP EPS $24.92;
  - DCF $418 per share.
- **Share price $389.00:** user-provided (12-Oct-2026); update it at `Model!BY` in the valuation block. The latest SEC-filed price is $330.82, the weighted-average June-2026 repurchase price (Q3 FY26 10-Q Part II Item 2).

## Data corrections
- None. Known exceptions (documented, not corrected):
  - **FY2008 class A EPS:** company two-class allocation from the IPO date; flagged n/m.
  - **Non-GAAP self-checks for FY2008–10:** they don't sum item by item. FY2008–09 apply a normalized 41% tax rate, and FY2010 prints no per-item EPS. The model ties to the published totals.
  - **Payments volume:** Σ quarters vs fiscal year differs by up to $6bn of ~$13tn in some years (company rounding and updates to previously reported volume); the check tolerance is ±$10bn.

## Sources
SEC EDGAR only (CIK 0001403161):
- Forms 10-K FY2008–FY2025 and 10-Q Q1 FY2013 – Q3 FY2026.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Apr-2008 – Jul-2026: non-GAAP reconciliations, Q4 statements, dividend announcements, key business drivers.
- XBRL company facts: cross-checks of revenue, net income, total assets and CFO, and the quarterly dividend rate where a release has no dividend sentence.

The investor-relations site (investor.visa.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR. The Q4 FY26 outlook is not on EDGAR (call only) and is marked UNVERIFIED.
- `filings.csv` indexes the filings.
- `data/<period>.json` holds the statements and KPIs (with source URLs and the raw rows parsed); `data/ngaap/<period>.json` holds the non-GAAP reconciliations.
- `data/_dps.json` holds the dividends; `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the outlook (unverified, with its sources), the Q4 inputs, debt, amortization schedules, the buyback authorization, the share-count proxy, the Visa Europe PPA and the share price.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc (`apt-get install libreoffice-calc`) for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export V_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 period_index.py && python3 extract.py`.
   3. Extract the non-GAAP reconciliations of new periods into `data/ngaap/` following `EXTRACTION_SCHEMA.md`. They were extracted by agents with the schema's self-checks; `check_data.py` re-verifies them.
   4. `python3 check_data.py` runs 1,515 checks: statement arithmetic, revenue categories, EPS, non-GAAP NI / EPS / opex vs published, cash and balance-sheet ties, quarters vs fiscal years, and XBRL cross-checks. Known exceptions are in `EXC`.
3. Build: `python3 build.py --snap --recalc` writes `../V_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../V_Model.xlsx` → 0 error cells and 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../V_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../V_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`, `period_index.py`: EDGAR filings index, downloads, HTML → text, period index and the hidden text layer of image-based releases.
- `parse_doc.py`, `extract.py`: table helpers; per-period extraction of statements, revenue categories, EPS / shares, balance sheet, cash flow and KPIs.
- `xbrl.py`: XBRL company-facts helper (30-September fiscal year).
- `normalize.py`: basis rules, split adjustment, Q4 derivation, flat model keys, discrete quarterly cash flow, non-GAAP categories, dividends.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules (non-GAAP record).
