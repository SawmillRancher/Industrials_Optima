# FICO model build kit

`models/FICO_Model.xlsx` is the Fair Isaac Corporation (NYSE: FICO) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD build kit (also a 30-September fiscal year):
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). Discount dates moved to FICO's 30-September fiscal year ends; FY2026E (ended 30-Sep-2026, two weeks before the build date) is the base year, so the explicit years are FY2027E–FY2031E and net debt is taken at 30-Sep-2026.
  - Charts: segment contribution to revenue growth, adjusted EBITDA / operating income, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 30 September; 2026 = Oct-2025 – Sep-2026)
- **C–I FY2006–FY2012:** annual, from the 10-K, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** the template's own grid, grouped and collapsed.
- **BZ Q4/26E, CA 2026E:** forecast, calibrated to the FY26 outlook (Q3 FY26 release, 29-Jul-2026) plus the Oct-2026 restructuring.
- **CB–CF 2027E–2031E:** scenario forecast (one more year than the template).
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported. The income statement, balance sheet, cash flow and non-GAAP table come from each quarter's earnings release (Ex. 99.1). Segment operating income, the interest split and the revenue KPIs come from that quarter's 10-Q / 10-K. FY2006–12 annual figures come from the 10-K; FY2013+ from the Q4 release twelve-month column (cross-checked to the 10-K XBRL).
- **Q4 items not in the Q4 release** (segment revenue / operating income, unallocated items, interest split, KPIs) = fiscal year (10-K) − nine months (Q3 10-Q year-to-date block). For FY2021, where the 10-K re-presented the segments as Scores / Software, the nine months come from the FY2022 Q3 10-Q prior-year column.
- **Segments as reported per year (legacy structures kept as memo rows):**
  - FY2006–09: Strategy Machine Solutions, Scoring Solutions, Professional Services, Analytic Software Tools. Segment results are after amortization and corporate costs.
  - FY2010–15: Applications, Scores, Tools, plus unallocated corporate expenses.
  - FY2016–Q3/21: Applications, Scores, Decision Management Software.
  - FY2021 10-K onward: Scores, Software.

  The model drives **Scores** (continuous; "Scoring Solutions" in FY2006–09, flagged) and **Software = consolidated revenue − Scores**, an aggregate the re-presentations don't change.
- **Revenue streams:** B2B / B2C Scores and platform / non-platform software, from the FY2021 10-K (FY2019–21) and the FY2022+ 10-Qs (FY2021 quarters from the prior-year columns). Professional services comes from the income statement (FY2021+).
- **Discontinued operations:** FY2007–09 (business units sold in FY2008), as reported.
- **Per-share data:** no stock splits; one share class. Shares outstanding from XBRL (CommonStockSharesOutstanding, as first filed).
- **Cash flow:** quarters derived from year to date (Q4 = FY − 9M). Working capital & other = CFO − net income − D&A − share-based compensation.

## Model structure (Model tab)
- **Segment build:**
  - Scores = B2B + B2C; Software = platform + non-platform + professional services. History falls back to segment revenue where the streams are not published.
  - Segment operating income = revenue × segment margin, + unallocated corporate expenses = **non-GAAP operating income**. This is a model measure: FICO publishes no non-GAAP operating income, and it equals GAAP operating income + the items FICO excludes (= the unallocated items of its segment summary). It is checked against the company segment summary in every period.
- **Future M&A lever:** spend ÷ EV/sales (6.0x), 20% margin, 30% intangibles over 8 years. Base spend is $0.
- **FY26 guidance calibration (Q4/26E):**
  - Revenue: one uniform Δ (−3.3pp) on the 9M FY26 y/y growth of every stream, solved to the $2.53bn guide.
  - Margins: one uniform Δ (−2.5pp) on the segment margins (prior-year quarter + 9M drift), solved to non-GAAP EPS of $42.43. The required Q4 non-GAAP operating income comes from (EPS × FY shares − 9M non-GAAP NI) ÷ (1 − 25.5%) + net interest − other income.
  - Guidance is a point estimate (high = mid = low).
  - SBC ($46.1m), the excess-tax-benefit line (+$3.4m) and the tax rate on items (24.5%) come from the company's guidance reconciliation less the 9M actuals.
  - The $27m Q4 restructuring (8-K Item 2.05, 6-Oct-2026) came after the guidance and is added on top. FY26E GAAP net income is $825m vs the $850m guide (information row).
- **GAAP P&L from the build:** operating income = non-GAAP operating income − SBC − amortization − restructuring − gains. SG&A is the balancing cost line. Net interest is calculated on opening balances. GAAP net income = non-GAAP net income − items − their tax effect − excess tax benefit, and tax is the residual.
- **Bridges** (checks vs published in every reported period):
  1. **Operating income → non-GAAP operating income:** checked against the segment summary (Σ segment operating income + unallocated corporate).
  2. **Net income → EBITDA → adjusted EBITDA:** model definitions (FICO publishes no EBITDA; adjusted EBITDA excludes SBC like FICO's non-GAAP measures). Continues to adjusted EBITA after SBC (the NOPAT basis).
  3. **Net income → non-GAAP net income → non-GAAP EPS:** company definition, published from Q1 FY2013.
     - Items: SBC, amortization, restructuring & acquisition, gains on product-line / business sales, a FY2018–19 realized gain on a cost-method investment, income tax adjustments, the excess tax benefit (excluded from FY2017), and discrete tax items (TCJA, valuation allowance, tax reserves).
     - The historical tax effect = published − GAAP − pre-tax items − excess tax benefit − discrete items (FY2013–Q2/16 items were shown net of tax).
     - FY2006–12: nothing published, so non-GAAP = GAAP (flagged).
  4. **Free cash flow:** company definition (CFO − capex incl. capitalized software). FY2013–Q2/17 the company also deducted dividends; a memo row and the check add them back.
- **Other schedules:**
  - Cash flow; buybacks (incl. the $1.5bn ASR: ~0.264m final shares assumed delivered in Q4 FY26); balance sheet; working capital (year-end levels).
  - Debt:
    - term-loan amortization per the credit agreement;
    - the June-2028 notes and the term-loan balloon refinanced with new notes in FY2028 (assumption);
    - revolver to a $150m minimum cash;
    - revolver draws above $750m termed out into new notes (financing assumption), with a headroom memo vs the $1.0bn commitment and a covenant memo (4.5x / 4.0x / 3.5x).
  - Leverage-targeted buybacks 2027E+: net debt / adjusted EBITDA of 3.25x / 3.0x / 2.5x.
  - Ratios: ROIC on book IC (equity deficit + net debt); ROE is n/m while equity is a deficit.
- **DCF basis:**
  - NOPAT = (adjusted EBITA after SBC − restructuring) × (1 − 25%), with a depreciation-only add-back. FICO's non-GAAP excludes SBC; the model deducts it.
  - UFCF after capex incl. capitalized software. Operating leases are left in operating costs and out of net debt.
  - Market inputs (risk-free 4.25%, ERP 5%, beta 1.10) are assumptions: U.S. Treasury / FRED data are not reachable from the build environment. Cost of debt is 6.0%, anchored on the 2025 / 2026 note coupons.

## Key forecast assumptions (Base)
- **Revenue streams 2027E–31E** (scenario table; assumptions citing the 9M FY26 / FY2023–25 trends in the 10-Q MD&A):
  - B2B scores +15% → +8% (mortgage score unit price drove +54% in 9M FY26);
  - B2C +4% → +3%;
  - platform software +30% → +15% (ARR +62%);
  - non-platform −15% → −4% (ARR −17%);
  - professional services −5% → 0%.
- **Margins:** Scores 90.5% flat (9M FY26 90.2%); Software 27% → 33% (platform scale; Oct-2026 workforce reduction, savings not quantified — assumption); corporate −7.5% of revenue.
- **Cost and capital inputs:** SBC 7.2% of revenue; non-GAAP tax 25%; tax rate on items 24.5%; excess tax benefit −$10m p.a. (assumption); capex 0.2% + capitalized software 1.4% of revenue; no dividend; no M&A.
- **Base results:** FY27E revenue $2.80bn and non-GAAP EPS $53.45; FY31E $3.98bn and $119.76 (buybacks ~$1–2bn a year cut diluted shares from 22.9m to 13.3m).
- **Share price $740.00:** user-provided (13-Oct-2026). It is not an SEC-sourced price, so update it to market at `Model!CA` in the valuation block. For reference, the Q3 FY26 10-Q average repurchase price was $1,148.84.

## Data corrections
- None. Documented derivations:
  - Q2-14 segment revenue = 6M − Q1 (the 10-Q has no quarter revenue table that the parser matches).
  - FY2013–Q2/17 FCF includes the dividend deduction (memo row).

## Guidance not on EDGAR
- None used. All FY26 guidance comes from the 8-K Ex. 99.1 releases. No call-transcript or investor-day targets are used. The scenario levers are labelled assumptions.

## Sources
SEC EDGAR only (CIK 814547):
- Forms 10-K FY2006–FY2025 and 10-Q Q1 FY13–Q3 FY26.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4 FY2005 – Q3 FY2026. Preliminary releases (Apr-2007, Jan-2008, Oct-2013) are superseded by the full release.
- 8-Ks:
  - 2026 Senior Notes (11-Mar-2026);
  - term loan / ASR (5-Jun-2026);
  - Item 2.05 workforce reduction (1-Oct-2026).
- XBRL company facts: shares outstanding; cross-checks of revenue, operating income, net income, total assets and CFO.

The investor-relations site (fico.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the FY26 guidance history, the Oct-2026 restructuring, debt terms, the buyback / ASR, shares and the share price, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl beautifulsoup4 lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export FICO_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 period_index.py && python3 extract.py && python3 -c "import xbrl; xbrl.dump_subset()"`.
   3. `python3 check_data.py` runs 1,671 checks with no exceptions:
      - statement arithmetic;
      - segment summary vs operating income;
      - interest split vs non-operating total;
      - B2B + B2C = Scores, platform + non-platform = on-premises & SaaS;
      - non-GAAP items, EPS and FCF vs published;
      - cash and balance-sheet tie-outs;
      - Σ quarters = fiscal year;
      - XBRL cross-checks.
3. Build: `python3 build.py --snap --recalc` writes `../FICO_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate (all pass in Base, Bull and Bear):
   - `python3 ../tools/inspect_model.py ../FICO_Model.xlsx` → 0 error cells, 0 non-zero check rows.
   - `python3 ../tools/cyc.py ../FICO_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../FICO_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`, `period_index.py`: EDGAR filings index, downloads, HTML → text, period → document map.
- `ptab.py`: HTML table parser. It assigns numbers to columns by grid position, so blank cells keep their column.
- `extract.py`: per-period extraction (statements, non-GAAP, segment summaries incl. year-to-date blocks, interest split, revenue KPIs).
- `xbrl.py`: XBRL company-facts helper and subset dump.
- `normalize.py`: basis rules, flat model keys, Q4 derivations, discrete quarterly cash flow.
- `check_data.py`: data consistency checks.
- `inspect_model.py`, `cyc.py`: QA tools (copied from `models/tools`).
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
