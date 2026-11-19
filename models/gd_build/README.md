# GD model build kit

`models/GD_Model.xlsx` is the General Dynamics Corporation (NYSE: GD) three-statement model. It is built on the MLM template (`MLM_Model.xlsx`, included here, 6-Oct-2026 version) with the standard process in `models/MODEL_BUILD_PLAYBOOK.md`, adapted from the WWD / STE build kits:
- **Formatting and rows:** the template's archetype rows and colour conventions:
  - blue = input / published data;
  - black = formula;
  - grey = historical growth;
  - green = cross-sheet link.

  It also keeps the template's check rows and notes column. The view is frozen at C8 with quarterly columns grouped.
- **Scenarios:** Bull / Base / Bear switch in `Model!CG2`, scenario table in `Model!CO:CS`.
- **Other tabs:**
  - Bull-Base-Bear: live panel plus Bull / Bear value snapshots, including the buyback rows.
  - DCF: current layout (live valuation date, fade, implied ROIC, target-IRR entry price, WACC × g, reverse DCF, Mauboussin EV/NOPAT). 2026E (ten and a half months done at the 19-Nov-2026 valuation date) is the base year, so the explicit years are 2027E–2031E and net debt is taken at 31-Dec-2026.
  - Charts: Aerospace vs defense-segment contribution to revenue growth, adjusted EBITDA / operating earnings, returns.
  - The template's `DCF_old` tab is dropped.
- **Calculated values stored**, so the workbook reads correctly in any viewer (`fullCalcOnLoad` stays set).

## Columns (fiscal year ends 31 December; quarters end on the Sunday nearest quarter end)
- **C–I FY2006–FY2012:** annual, as originally reported.
- **J–BV Q1/13–Q4/25 with FY subtotals; BW–BY Q1/26–Q3/26:** grouped and collapsed like the template.
- **BZ Q4/26E, CA 2026E:** forecast. Q4/26E = prior-year quarter × (1 + 9M-26 y/y growth) at the prior-year margin + 9M drift; an optional FY26 target activates the calibration (none by default — see Calibration).
- **CB–CF 2027E–2031E:** scenario forecast.
- **Right of the forecast** (template column + 1): CG notes, CI–CL CAGRs (5Y fwd '26–'31, 5Y, 10Y, 19Y), CO–CS scenario table.

## Basis
- **Policy:** as originally reported, from each period's own earnings release (8-K Ex. 99.1). The 10-K wins for annual balance sheets (FY2017: total assets $35,046m vs a preliminary $34,994m; FY2006: the release had no balance sheet).
- **Restatements not recast** (restated comparatives in cell comments): ASC 606 (adopted 1-Jan-2017; 2016 restated in the 2017 releases), ASU 2017-07 (2018), the 2020 retrospective change in accounting principle (Q4-20 release), and the axle business moved to discontinued operations in Q3-14 (Q1–Q2/14 as reported include $59m of axle revenue, so the 2014 quarters do not sum to the year).
- **Segments:** one continuous Technologies line = Information Systems and Technology (2006 – Q1-18) = Information Technology + Mission Systems (Q2-18 – 2019, after the CSRA acquisition) = Technologies (Q4-20 release onward; 2019 recast). IS&T, IT and Mission Systems are memo rows with a Σ check. Aerospace, Marine Systems and Combat Systems are unchanged throughout.
- **Gulfstream deliveries:** green deliveries to 2016 (release exhibit 2006–09; 10-Q / 10-K MD&A 2010–16, Q4 = FY − 9M) and outfitted deliveries from 2017 (ASC 606), flagged in the deliveries-basis row.
- **Per-share data:** one share class; no splits since 24-Mar-2006. Dividends declared per share: XBRL for Q1–Q3, 10-K for the year, Q4 = FY − 9M.
- **Cash flow:** quarters derived from year-to-date (Q4 = FY − 9M); discontinued-operations cash flow as a separate line, as GD presents it.

## Model structure (Model tab)
- **Segment build:** four segments, each revenue = prior year × (1 + growth lever) × operating margin lever; backlog roll-forward (opening + orders − revenue, orders = revenue × book-to-bill input) with funded / unfunded / estimated potential contract value memo rows, implied orders and backlog coverage; Gulfstream deliveries (input, information row) with implied revenue per delivery; Aerospace published orders memo. Corporate is a point estimate / input.
- **Future M&A lever:** spend ÷ EV/sales (2.0x, CSRA ~1.9x), 10% margin, PP&E / intangibles / goodwill split from the CSRA PPA, 12-year amortization. Base nil.
- **Calibration (optional):** GD gives guidance on the earnings call only — nothing is on EDGAR. The FY26 revenue and diluted-EPS target cells in the scenario table hold "none" by default (Δ = 0). If a number is entered it is **UNVERIFIED** (outside EDGAR) and the uniform growth Δ / segment-margin Δ solve FY26 to it with check rows.
- **GAAP P&L from the build:** operating earnings = Σ segments + corporate; operating costs implied; interest, net on opening notes and cash; tax rate input (17.5%); discontinued operations nil.
- **GAAP → adjusted bridges** (checks vs published in every reported period):
  1. **Operating earnings → adjusted operating earnings:** model definition = GAAP + the items GD itself quantified in its Q4-2012 / FY2012 reconciliation (goodwill and intangible impairments, contract disputes, restructuring, inventory charges); adjusted = GAAP everywhere else. Checked against the published adjusted segment totals ($836m / $3,596m).
  2. **Net earnings → EBITDA → adjusted EBITDA:** model definition (operating earnings + D&A, plus the 2012 items); full-cost adjusted EBIT for NOPAT.
  3. **Earnings from continuing operations → adjusted earnings → adjusted EPS:** GD's Q4-12 / FY2012 reconciliation (incl. the $123m debt retirement charge and the company tax effect; company diluted shares) and the Q4-17 / FY2017 tax-law item; adjusted = GAAP continuing operations elsewhere. Items GD named but did not adjust (2018 CSRA one-time charges) are left in.
- **Other schedules:** cash flow (working capital from the release lines; other operating items derived); buybacks; balance sheet (unbilled receivables and customer advances as separate lines); working capital days / percentages; CSRA PPA (Q2-18); debt (fixed-rate notes repaid at maturity and refinanced per input; commercial paper to a $1.5bn minimum cash); leverage-target buybacks (net debt / adjusted EBITDA 0.5x / 0.25x / 0.0x); ratios and valuation.
- **DCF basis:** NOPAT on adjusted EBIT (full-cost; = operating earnings in the forecast) less cash adjusting items; UFCF after capex and M&A; operating leases not treated as debt; USD; market inputs are labelled assumptions (government rate sources not reachable from the build environment).

## Key forecast assumptions (Base)
- **Segment revenue growth 2027E–31E:** Aerospace 8% → 4%; Marine Systems 12% → 5% (Columbia / Virginia throughput, $147bn backlog); Combat Systems 5% → 3%; Technologies 5% → 4% (9M-26: +10.9% / +17.3% / +3.7% / +6.3%).
- **Segment margins:** Aerospace 15.0% → 16.0%; Marine 8.0% → 9.0%; Combat 14.0–14.2%; Technologies 9.5–9.7%; corporate $(200)–(220)m.
- **Book-to-bill inputs:** Aerospace 1.05x then 1.0x; Marine 0.8x / 0.9x then 1.0x (working off the Q3-26 awards); Combat and Technologies 1.0x.
- **Other drivers:** tax 17.5%; capex 2.2% → 2.0% of revenue; depreciation 1.4%; amortization per the FY2025 10-K schedule + ~$70m of finance-lease ROU amortization; equity-based compensation 0.4%; DPS +6% p.a.; dilutive securities 3.6m; interest on notes 3.7% → 4.2%, cash yield 3.5%; Q4/26E buybacks $200m (Bull $300m / Bear $100m); M&A nil (Bull $1bn p.a.).
- **Working capital:** drivers at the 4-Oct-2026 levels (receivables 16d, unbilled 56d, inventories 64d, payables 22d, customer advances 19.0% of revenue), because the Q3-26 submarine awards structurally raised advances (judgement; 31-Dec-2025 levels quoted in the note).
- **Share price $362.97:** average price paid for shares repurchased 31-Aug – 4-Oct-2026 (Q3-26 10-Q Part II Item 2), the latest share price in an SEC filing; update to market at `Model!CA` in the valuation block.

## Data corrections
- None. Known source exceptions (documented, not corrected; `manual_items.json` → `sumq_exceptions`, `fcf_exceptions`):
  - FY2014: Q1–Q2/14 as reported include the axle business ($59m of Combat Systems revenue); FY2014 excludes it.
  - FY2016: discontinued operations $(107)m vs Σ quarters $(94)m (Q4-16 release restated earlier quarters).
  - FY2020: Q1–Q3/20 as reported differ from FY2020 by $26m of operating costs / other, net (retrospective accounting change in the Q4-20 release).
  - Q2-16: the published quarterly free cash flow ($324m) does not reconcile with the release's own year-to-date figures (H1 $739m − Q1 $374m = $365m); excluded from the published-FCF check.

## Sources
SEC EDGAR only (CIK 0000040533):
- Forms 10-K FY2005–FY2025 and 10-Q 2006–Q3/26.
- Form 8-K Item 2.02 earnings releases (Ex. 99.1), Q4-2005 – Q3-2026 (84 releases; the Q4-2009 release is in the 8-K body).
- Deal / financing 8-Ks: CSRA (Feb–Apr 2018), notes issues (Mar-2020, May-2021, May-2025).
- XBRL company facts: dividends declared per share, G&A, cover-page shares, cross-checks of revenue / operating earnings / net earnings / total assets.

The investor-relations site (gd.com) is blocked from the build environment; its releases are the same documents as filed on EDGAR.
- `filings.csv` indexes the filings.
- Each `data/<period>.json` lists its source URLs; `data/_releases.json` indexes the releases and `data/_xbrl.json` holds the XBRL subset.
- `manual_items.json` holds the Q4-12 / FY2012 and Q4-17 / FY2017 adjusted-earnings reconciliations, the CSRA PPA, the debt ladder, the amortization schedule, the buyback authorization, dividends, the share price, the guidance policy and the known source exceptions, each with its source.

## Rebuild
1. Install the tools: `pip install openpyxl lxml`, plus LibreOffice Calc for recalculation.
2. Refresh the data (only needed for new filings; `data/` is committed):
   1. `export GD_SRC=/path/to/src SEC_UA="name email"`.
   2. Run `python3 make_index.py && python3 fetch.py && python3 extract.py`.
   3. `python3 check_data.py` runs 1,901 checks: statement arithmetic, segment and backlog sums, EPS, the 2012 / 2017 adjusted bridges, cash and balance-sheet tie-outs, XBRL cross-checks and quarters vs years. The 10 remaining items are the known source exceptions above.
3. Build: `python3 build.py --snap --recalc` writes `../GD_Model.xlsx`. It reruns with the switch on Bull and Bear to fill the snapshot panels, then stores calculated values. Set `XLSX_RECALC` to a LibreOffice recalculation script (default: the xlsx skill's `recalc.py`).
4. Validate:
   - `python3 ../tools/inspect_model.py ../GD_Model.xlsx` → 0 error cells, 0 non-zero check rows (also with the switch on Bull and Bear).
   - `python3 ../tools/cyc.py ../GD_Model.xlsx` → 0 cycles.
   - `python3 ../tools/residue_scan.py ../GD_Model.xlsx --extra WWD Woodward 382.17` → 0 residue hits.
   - `python3 review.py ../GD_Model.xlsx` prints the key annual rows and the DCF / Bull-Base-Bear outputs.

## Files
- `fw.py`: column map, style cloning from the MLM template archetype rows, row registry, previous-balance helper.
- `spec.py`, `spec2.py`: Model row specification.
- `build.py`: inputs (V0), compute engine, scenario table, definition flags, restatement comments, column layout, Bull / Bear snapshots, cached-value injection.
- `other_sheets.py`: rewires Bull-Base-Bear / DCF / Charts and re-injects the template chart XML.
- `make_index.py`, `fetch.py`, `h2t.py`: EDGAR filings index, downloads, HTML → text.
- `parse_release.py`: text-based release parser (exhibit blocks typed by title / content; columns resolved from the year and period headers, with the FY2012 prior-year-first order and the 2006 "Quarter | Year-to-date" layouts).
- `extract.py`: per-period extraction (statements, segments, backlog, deliveries incl. the 10-Q / 10-K MD&A tables, free cash flow, cash flow, balance sheet incl. the 10-K fallback, prior-year comparatives, XBRL extras).
- `xbrl.py`: XBRL company-facts helper (us-gaap and dei; Sunday-nearest quarter ends).
- `normalize.py`: basis rules, flat model keys, segment mapping, discrete quarterly cash flow, Q4 = FY − 9M derivations.
- `check_data.py`: data consistency checks.
- `review.py`: key-row printout of a recalculated workbook.
- `EXTRACTION_SCHEMA.md`: per-period JSON schema and rules.
