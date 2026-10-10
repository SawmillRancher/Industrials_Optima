# Three-statement model build playbook

The standard process for building a new company model from scratch. It folds in everything learned across the ~30 models built
so far (TFI, Copart, R&Y, HII, RBA, TDY, KRMN, MLM, VMC, RMS, CLH, WAB, XPO, CHRW, ODFL, SAIA, BC, WCN, HEI, LOAR, ONON, CSGP,
DHR, TMO, CTAS, STE, UBER, LECO, BWXT, CW, ESAB).

Use it with:
- **Template workbook:** [`templates/MLM_Model.xlsx`](templates/MLM_Model.xlsx), the current MLM template (6-Oct-2026 version: reworked DCF, Bull-Base-Bear buyback rows).
- **Fill-in docs:** [`templates/NEW_MODEL_README_TEMPLATE.md`](templates/NEW_MODEL_README_TEMPLATE.md) and [`templates/EXTRACTION_SCHEMA_TEMPLATE.md`](templates/EXTRACTION_SCHEMA_TEMPLATE.md).
- **QA tools:** [`tools/inspect_model.py`](tools/inspect_model.py) (formula errors and non-zero check rows) and [`tools/cyc.py`](tools/cyc.py) (circular references).
- **Per-model lessons:** [`MODEL_LESSONS.md`](MODEL_LESSONS.md) records each model's specific nuances (basis, bridges, data quirks, deals, calibration, valuation) and reusable rules. Read the entries for the most similar companies before you start.
- **Reference builds** (all in `models/`, indexed in [`README.md`](README.md)): STE (`ste_build`), DHR (`dhr_build`), ONON (`onon_build`), LOAR (`loar_build`) and WWD (`wwd_build`) are the most complete build kits. Copy the closest one and adapt it; don't start from a blank script.

---

## 1. How the standard evolved

Each row is a change that is now part of the standard. The checklist in section 3 enforces all of them.

| Stage | Models | What changed (and is now standard) |
|---|---|---|
| Moog-based generator | TFI (May-26) | Parameterized builder over a reference workbook. **Lessons:** template hardcodes leak into the forecast (Moog's `=888*(1+g)` FY26 base), so every forecast cell must reference the new company's actuals. A column-index bug (4-digit vs 2-digit fiscal years) silently wrote all data to off-screen columns, so you must confirm values land in the visible period columns. Rows that don't apply (COGS / R&D / backlog for an IFRS logistics company) must be cleared, not left computing zero. |
| TFI forecast wiring | TFI | Segment revenue forecast = volume × yield drivers. Bull / Base / Bear anchored to stated long-term targets. The BS must balance: the cash-as-plug approach exposed a financing gap, which is why the template now has a revolver / minimum-cash debt schedule. Buybacks and dividends are driven (DPS × shares; buybacks capped by FCF / leverage), not held flat. |
| SEC-only Copart builder | Copart v1 (Jul-26) | EDGAR-only sourcing (XBRL company facts + filing instances). Colour code: blue = reported input, black = formula, yellow = scenario forecast. Q1–Q4 + FY grid (1H columns dropped). Non-GAAP reconciliation section with a live bridge and a tie-out check to the published figure. NI split into total and attributable to the parent, so EPS ties exactly. Verified with a spreadsheet engine: zero error cells. |
| Private company + LBO | R&Y Tool & Die | Built from compilation statements. The implied cash flow from BS changes ties to reported cash. PP&E roll-forward with an implied useful life. Returns / RONTA / ROE ratio block. LBO tab: interest on beginning debt (no circularity), sources = uses check, IRR checked against an independent Python replication. |
| DSV → HII template | HII (2-Oct-26) | Tabs Model / Bull-Base-Bear / DCF / Charts. Q4 = FY − 9M where needed. Current-year Q3/Q4 = FY guidance less 1H actuals. Scenario switch with a table where Bull/Bear = Base + Δ, and the guidance block = high / mid / low. Share price as a valuation-row input. |
| HII → RBA framework | RBA | Python generator plus committed per-period JSON source data. Revenue build replaces the segment P&L for single-segment companies. Bridges follow **the company definition in force in each period**, with a definition-flag row and cell comments. "Each period uses the latest filing that presents it", cross-checked to XBRL company facts. |
| RBA → TDY | TDY, KRMN, VMC | Segment P&L with GAAP OI → amortization → non-GAAP segment OI. Future-M&A lever. A current-definition memo series drives the valuation outputs. Uniform calibration Δ solves the current year to guided EPS / EBITDA. Debt: scheduled maturities plus a revolver to minimum cash, with interest on opening balances. LibreOffice Calc recalculation, then 0 errors and all checks tie. |
| TDY → MLM template | MLM and every build since | Unit-economics build (shipments × ASP, price / volume bridge, fall-through). Pending / closed acquisitions modelled as their own block with a PPA and synergies. Legacy segments kept as memo rows. Leverage-targeted buybacks. DuPont ROIC and RONTA. Modelling Notes column, CAGR columns and the scenario table on the right of the forecast. |
| MLM build-kit process | WAB, ODFL, SAIA, LOAR, ONON, STE, DHR | Standard kit: `fw.py` (column map, archetype-row style cloning, row registry), `spec.py` / `spec2.py` (row specs), `build.py` (inputs, compute, scenario table, definition flags), `other_sheets.py` (rewire BBB / DCF / Charts, re-inject chart XML), `extract.py` / `normalize.py` / `check_data.py`, `inspect_model.py`, `cyc.py`. Columns re-based to the company's history (template column − N). `--snap` fills Bull/Bear snapshots; `--recalc` stores values. |
| MLM template update (6-Oct-26) | ONON, DHR, CTAS, STE, LECO, ESAB | DCF: live valuation date, 5-year fade, implied ROIC / RONIC, target-IRR max entry price, WACC × g grid, reverse DCF, Mauboussin EV/NOPAT. Bull-Base-Bear: buyback rows (40–42). `DCF_old` dropped. View: frozen at C8, quarterly columns grouped and collapsed. Cached values stored so the file reads correctly in any viewer. |
| Special cases | RMS, BC, ONON, CHRW, UBER, CTAS, DHR, STE | Non-SEC / IFRS / foreign-currency reporters (half-year columns, constant-currency + FX build). Deal pro forma tabs (CHRW RXO PF: S&U, PPA, synergies, accretion). Pending deals behind a toggle (CTAS UniFirst, UBER Delivery Hero). Hybrid recast basis around spin-offs (DHR). Non-calendar fiscal years (STE March, CTAS May). |

---

## 2. Process overview

```
0 Scope ─► 1 Sources ─► 2 Extract ─► 3 Normalise & check data ─► 4 Lay out columns ─► 5 Build Model tab
   ─► 6 Scenarios & calibration ─► 7 BBB / DCF / Charts ─► 8 Document ─► 9 QA ─► 10 Package & commit
```

Rules that apply at every step:
- **SEC EDGAR is the system of record.** Investor-relations sites (and SEDAR) are blocked from the build environment. The 8-K Ex. 99.1 / 6-K releases are the same documents. Send a User-Agent on every EDGAR request and stay under 5 requests per second.
- **Never estimate a historical number.** If it is not published, it is null. Any computed value (sum, difference, FY − 9M) is noted at its source.
- **Every historical input is blue and traceable** to a URL in the data JSON, a cell comment, or the notes column.
- **Every forecast cell is a formula.** No template-company hardcodes survive.
- **Every reconciliation has a check row that reads 0** in every period the company published the measure.

---

## 3. Master checklist

Copy this section into the new model's PR description or working notes and tick items as you go.

### Phase 0 — Scope and setup
- [ ] Confirm the company, ticker, exchange and SEC CIK(s). Include predecessor registrants: VMC had a pre-2007 CIK; STE has three (STERIS Corp / UK plc / Ireland plc).
- [ ] Record reporting basis: US GAAP or IFRS; reporting currency; fiscal year end (calendar, 52/53-week, March, May…).
- [ ] Record the history window (default: FY2006–12 annual, quarterly from Q1/13), re-based where the company is younger: IPO prospectus years for LOAR, ONON, KRMN; post-spin start for XPO, BWXT.
- [ ] Record the interim frequency: quarterly by default; half-yearly for H1/FY-only reporters (RMS, BC).
- [ ] Record the forecast window: remaining quarters of the current year (calibrated to guidance), current-year total, then 4–5 annual scenario years.
- [ ] List reportable segments and every segment recast, spin-off, discontinued operation and major acquisition since the start of history.
- [ ] List stock splits and share-class structures (ONON Class A + B/10; HEI's seven 5-for-4 splits; CTAS 4-for-1).
- [ ] List pending or recently closed deals that need their own block (PPA, financing, synergies, toggle).
- [ ] Choose the closest reference build kit and copy its scripts into `models/<ticker>_build/`. Copy `templates/MLM_Model.xlsx` in next to them.
- [ ] Get the share price from the user, or the latest observable close, and record its date.
- [ ] Create or check out the working branch.

### Phase 1 — Source collection
- [ ] `make_index.py`: build `filings.csv` from the EDGAR submissions JSON: 10-K, 10-Q, 8-K Item 2.02 Ex. 99.1, deal 8-Ks, S-4/424B3, 424B4 IPO prospectus, 20-F/40-F/6-K for foreign filers.
- [ ] `fetch.py`: download into `$<TICKER>_SRC` (outside the repo; raw filings are not committed). Use a User-Agent, throttle, and retry/back off on 503s.
- [ ] `h2t.py`: convert HTML to text (one table row per line, cells joined by ` | `). Known quirk: a dropped ")" means "(25,433" is negative, and "—" is zero.
- [ ] Download the XBRL company facts JSON (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`) for cross-checks and for items releases omit (D&A, SBC, deferred tax, shares outstanding, DPS).
- [ ] Collect the latest guidance / outlook (release text, mid-quarter updates such as ODFL's Item 7.01, investor-day targets). Note anything that is not verifiable from EDGAR (for example call transcripts) as unverified.
- [ ] For acquired or pending targets, collect the target's own filings (Masimo for DHR, UniFirst for CTAS, RXO for CHRW).

### Phase 2 — Extraction (per period)
- [ ] Write `EXTRACTION_SCHEMA` for the company from `templates/EXTRACTION_SCHEMA_TEMPLATE.md`: sections `is`, `seg`, `ngaap`, `cf`, `bs`, `py`, `extra`, `notes`, plus company keys (volumes, KPIs, backlog, organic growth).
- [ ] Use one JSON per period: `data/<period>.json` with keys like `2008`, `Q1-13`, `Q4-25`, `H1-26`, `9M-25`.
- [ ] Every record carries `sources` (URLs) and `notes`.
- [ ] Units: USD (or reporting currency) millions to one decimal as published; shares in millions; per-share as published; percentages as numbers.
- [ ] Signs: costs positive; two-sided items signed by their effect on income; cash flow as presented.
- [ ] Null vs zero: "—" = 0.0; a line not presented = null (omit the key). Never fill a gap with an estimate.
- [ ] Quarters use the release's three-month column. Q4 comes from the Q4 release three-month column, else FY − 9M (noted).
- [ ] Cash flow is extracted year-to-date with `ytd_months`. Discrete quarters are derived later.
- [ ] Extract the prior-year comparative (`py`) as presented in each period, flagged `restated` with the reason. This is what makes recast bases possible.
- [ ] Non-GAAP: capture the bridge start and every adjusting item with the company's exact label, a category (AMORT, ACQ, STEPUP, RESTR, PENSION, SBC, DEBT, GAIN, IMPAIR, LEGAL, OTHER, TAX, TAXD, NCI), pre-tax and after-tax amounts, and where it sits (op / nonop / tax / below NI / disc ops). Record the published adjusted figures and the definition wording.
- [ ] Annual records add the 10-K extras: employees, segment D&A / capex / assets, acquisitions, divestitures, debt maturities, and the expected amortization schedule. Where the release and 10-K differ, the 10-K wins.
- [ ] `manual_items.json` holds anything not machine-extractable (guidance, PPAs, debt terms, one-off items, corrections), each with its source.
- [ ] Run the self-checks before saving each period. Write any check that fails, and why, into `notes`:
  - [ ] GP − opex = operating income; OI + non-op − interest = EBT; EBT − tax = continuing ops; + disc ops = NI (±0.6).
  - [ ] Σ segment sales = sales; Σ segment OI + corporate = OI (±1).
  - [ ] Bridge start + Σ items = published adjusted EPS (±0.01) / adjusted measure.
  - [ ] CFO + CFI + CFF + FX = Δcash; beginning cash + Δ = ending cash.
  - [ ] TA = TL&E; components sum to subtotals.
- [ ] Large extraction can be split across parallel agents by period range (RBA / TDY used a1…a8 files). Give every agent the same schema, paths and self-checks.

### Phase 3 — Normalisation and data checks
- [ ] `normalize.py` maps the extraction to flat model keys `DATA[period]['x'][key]` and records the basis used per period.
- [ ] Choose and document **one basis policy**:
  - [ ] Default: as originally reported.
  - [ ] Or a hybrid recast, where periods restated by the next year's filing take the restated comparative, so y/y is like-for-like (DHR around Fortive / Envista / Veralto; STE for Dental). Put a cell comment on each recast period.
  - [ ] Or "latest filing that presents the period" (RBA / TDY).
- [ ] Derive discrete quarterly cash flow from YTD (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = FY − 9M).
- [ ] Apply split adjustments to shares and per-share data by the filing date of each source document. Don't adjust in extraction.
- [ ] Apply share-class conversions (Class A-equivalent shares) so NI ÷ shares reproduces the published EPS.
- [ ] Convert currency / units where the filing basis changed (thousands → millions; prospectus share reorganisations, e.g. ONON ×1,250).
- [ ] Document data corrections (a company typo is overridden only when the arithmetic proves it, e.g. ONON Q4-21 operating result) in `manual_items.json`.
- [ ] `check_data.py`: statement arithmetic, segment / revenue-type sums, bridge totals, quarters vs FY sums (Σ Q1–Q4 = FY), cash and BS tie-outs, and missing quarters. **All pass, or every exception is explained in the README.**
- [ ] Cross-check sales, OI, NI, EPS, CFO and total assets against XBRL company facts.

### Phase 4 — Workbook layout (Model tab)
- [ ] Start from `templates/MLM_Model.xlsx`. Clear the Model sheet values, comments, outline levels and data validations, but keep styles. Drop `DCF_old`.
- [ ] Columns (template default): C–I FY2006–12 annual | J… quarterly Q1–Q4 + FY subtotal per year | current-year actual quarters | QnE estimate quarters | current-year E | 4–5 scenario years | **Modelling Notes** | spacer | CAGR columns (5Y fwd, 5Y, 10Y, full history) | spacer | **scenario input table** (label, Bull, Base, Bear, note).
- [ ] Re-base the column map in `fw.py` for the company's history. Right-of-forecast blocks keep template order (template column − shift); assert the key column letters.
- [ ] Each column carries kind (A / Q / QE / E / AE), `prior` (same period last year) and `prevq`. Formulas use these, never hard-coded letters.
- [ ] Header rows: row 1 switch caption; row 2 company name `(EXCHANGE: TICKER) — 3-Statement Financial Model` and scenario switch cell; row 3 basis · currency · units · sources · CIK; row 4 basis notes (fiscal calendar, recasts, acquisitions / disposals with dates); row 5 Forecast / Historical over the CAGR columns; row 6 period labels and "(USDm)"; row 7 CAGR spans.
- [ ] Formatting by cloning template archetype rows (section, block, line, total, growth, pct, memo, check, driver, text, eps, schedule):
  - [ ] Blue font = hard-coded input or published data. Black = formula. Grey = historical growth / ratios. Green = cross-sheet link. Red = definition-flag text.
  - [ ] Light-yellow fill = forecast columns. Grey-green fill = FY subtotal columns on key rows.
  - [ ] Number formats from the template (`#,##0;(#,##0);-`, `0.0%`, `0.00` per share, `0.0x`).
- [ ] View: freeze panes at C8; quarterly columns grouped and collapsed under each FY; ~70% zoom; open on a recent year.

### Phase 5 — Model tab sections (in template order)
Build each section with history as blue inputs, forecast as formulas, and a check row wherever a total can be compared with the reported figure.

1. [ ] **Operating build** (replaces MLM's product lines; pick what the company discloses):
   - [ ] Segments / product lines / end markets / regions / métiers. A single-segment company builds revenue by stream (RBA GTV × take rate; KRMN end markets).
   - [ ] Unit drivers where disclosed: volume × price (shipments × ASP; tons/day × work days × rev/cwt; GTV × take rate; gross bookings × take rate; headcount × cost per head).
   - [ ] Growth decomposition: organic / core + acquisitions + FX (constant-currency growth + currency effect), with a check to reported growth.
   - [ ] Price / volume bridge and fall-through or incremental-margin rows.
   - [ ] Segment profit (company measure) and margin; segment adjusted OI = GAAP OI + amortization + other items, where published.
   - [ ] Legacy segment structures as grouped memo rows, as originally reported, with a Σ check.
   - [ ] Operating KPIs and memo rows (backlog / book-to-bill, OR %, network stats, mix).
2. [ ] **Acquisition blocks** for closed-in-period or pending deals: standalone history from the target's filings, days consolidated / stub, run-rate, growth and margin levers, synergies (phased), purchase-accounting D&A, inventory step-up, toggle / closing-date switch. Flag undisclosed price assumptions loudly (DHR StatLab).
3. [ ] **Future M&A lever:** spend (scenario) ÷ EV/sales → acquired sales; margin; PP&E / intangibles / goodwill split; amortization life.
4. [ ] **Group total:** build vs consolidated checks (revenue, profit), guidance end-point memo rows, calibration helper rows (see Phase 6), and the "Check: FY vs guidance end-point (should be 0)" rows.
5. [ ] **Reportable segments memo** (if the build is not by segment): Σ segment OI + corporate vs consolidated check.
6. [ ] **Cost drivers:** D&A, SG&A, R&D, SBC as % of revenue; corporate cost.
7. [ ] **Income statement** as the company presents it (continuing ops, disc ops, NCI, attributable NI). Include "Check: NI attributable vs reported", memo D&A and SBC, basic / diluted shares, EPS basic / diluted / continuing, memo EPS as reported, DPS and DPS growth.
   - [ ] Forecast GAAP from the build: GAAP OI = adjusted OI (or Adj. EBITDA − D&A) − amortization − adjusting items. Gross profit or SG&A is the implied balancing line.
   - [ ] Interest from the debt schedule on **opening** balances; interest income on opening cash; tax rate from guidance, then scenario.
8. [ ] **GAAP → adjusted bridges** (usually three), each with "Company-published …", "Check: model vs company-published (should be 0)" and "Definition basis" rows:
   - [ ] Net income → EBITDA → Adjusted EBITDA (→ Adjusted EBIT / EBITA). Use the company definition, or a model definition labelled as such when the company publishes none (ODFL, DHR, STE).
   - [ ] GAAP OI → adjusted OI (company definition), or GP → adjusted GP / AGP where relevant.
   - [ ] GAAP NI / EPS → adjusted NI → adjusted EPS: tax effect of items, other company items / rounding row, diluted shares (if-converted where the company uses it).
   - [ ] Follow the **definition in force in each period**. Flag changes in the definition row (red text, in the column where they take effect) with cell comments quoting the company wording. Add a current-definition memo series when the definition changed (TDY, LOAR) and drive valuation off it.
   - [ ] Where only per-share reconciliations exist, $m = EPS × diluted shares, with a labelled rounding line.
   - [ ] Basis-difference lines (disc ops / NCI / pre-ASU) are explicit, never buried.
9. [ ] **Growth & margins** block (y/y, margins, incremental margins, opex %).
10. [ ] **Cash flow statement:**
    - [ ] Quarters derived from YTD; "Other … (derived)" rows absorb residuals so subtotals tie.
    - [ ] Checks: CFO + CFI + CFF (+ FX) = Δcash; beginning + Δ = ending.
    - [ ] Memo: FCF (company definition if published, with a check), FCF %, conversion, FCF/share, capex % and capex / D&A.
11. [ ] **Share buyback schedule:** buyback price (share price × appreciation), cash deployed, shares repurchased, issuance, beginning / ending shares.
12. [ ] **Balance sheet** (condensed as in the releases):
    - [ ] "derived" other lines so totals tie to reported.
    - [ ] Checks: "BS tie-out (TA − TL&E)" = 0 in every column including the forecast; model TA vs reported; BS cash vs CF ending cash.
    - [ ] Shares outstanding memo.
13. [ ] **Working capital:** DSO, DIO, DPO (only where COGS exists), accrued % of revenue, NWC % of revenue, ΔNWC. Forecast drivers are blue inputs, held at the last actual or set explicitly.
14. [ ] **BS forecast schedules:**
    - [ ] PPA table(s) with "Check: assets − liabilities − consideration = 0".
    - [ ] Asset roll-forwards (PP&E, intangibles amortization from the 10-K schedule, ROU / lease schedule for IFRS 16).
    - [ ] Debt schedule: note maturities (input), refinancing %, revolver / CP / term loan drawn or repaid to a minimum cash balance (cash sweep). No circularity.
    - [ ] Leverage-targeted buybacks: repurchases plug to a minimum net debt / Adjusted EBITDA (scenario); or a cash-return target (ODFL); or an authorized program schedule (ONON).
    - [ ] Equity roll-forward: equity = prior + NI − dividends − buybacks + issuance (no stale template SUMs).
15. [ ] **Ratio analysis:** DuPont ROIC (NOPAT on adjusted EBIT; IC = equity + net debt; margin × turnover × tax burden), RONTA, ROE, net debt / Adjusted EBITDA. Repoint any template references to rows the company doesn't populate.
16. [ ] **Valuation:** share price input (blue, dated in the notes), diluted shares, market cap, net debt, NCI (and leases / preferred where they count as debt), EV, EV / sales / EBITDA / EBIT / IC, P/E GAAP and adjusted, FCF yield, dividend yield. Foreign listings: price × FX input.

### Phase 6 — Scenarios and current-year calibration
- [ ] The scenario switch cell (`Bull / Base / Bear`, data-validated) sits in the notes column, row 2.
- [ ] Scenario input table on the right: Base values per year, with Bull / Bear = Base + Δ (Δ on each block header). The outlook block is High / Mid / Low of guidance. Point estimates (tax, interest, D&A, capex) apply to all cases. Every lever has a rationale note citing history or guidance.
- [ ] Levers: segment / line growth, margins, M&A spend, synergy realisation, buyback leverage floor, and any company-specific driver (cc growth, FX, take rate).
- [ ] **Current-year calibration** (remaining quarters):
  - [ ] Revenue lines: prior-year quarter × (1 + YTD y/y trend + a uniform Δ), with Δ solved so FY = the guidance end-point for the active scenario.
  - [ ] Margins: prior-year quarter margin + YTD drift + a uniform Δ, solved to the anchor KPI (adjusted EPS, Adj. EBITDA or adjusted OI, whichever the company guides).
  - [ ] Show each calibration Δ and the "before calibration" helper rows, plus a check row "FY vs guidance end-point (should be 0)".
  - [ ] Other guided items (GAAP EPS, FCF, capex) are information rows, not forced.
  - [ ] No guidance (ODFL, RMS): anchor on mid-quarter updates or historical seasonality (best / average / worst by scenario) as formulas on the history.
- [ ] Out-years (E+1 … E+4) are driven only by the scenario table. The LT targets used for Base are shown against the model as info rows (ONON Investor Day).

### Phase 7 — Bull-Base-Bear, DCF and Charts tabs
- [ ] Rewire every `Model!` reference through a template-row → new-row map (`other_sheets.py` `MAP` / `CMAP`). Never leave a reference to an MLM row number.
- [ ] **Bull-Base-Bear:**
  - [ ] Live panel (current switch): revenue, KPI growth, Adj. EBITDA, GAAP OI, adjusted NI, FDSO, adjusted EPS, assumed P/E → price target / upside / IRR, FCF, net debt / leverage, buyback rows, ROIC / RONTA, implied EV.
  - [ ] Bull and Bear **value snapshots**, filled by rebuilding with the switch on each case, recalculating, and pasting the values (`build.py --snap`). P/E rows stay panel-specific inputs.
- [ ] **DCF (current layout):**
  - [ ] WACC build (risk-free, ERP, beta with peer rationale, cost of debt, target D/V).
  - [ ] Live valuation date with discount periods to each fiscal year end (move the dates for non-December year ends).
  - [ ] UFCF: NOPAT on adjusted EBIT / EBITA (tax on pre-amortization profit, D&A add-back without perpetual amortization), − capex and M&A in the explicit years only, − ΔWC.
  - [ ] 5-year fade, Gordon terminal value, implied ROIC / reinvestment / terminal RONIC.
  - [ ] EV → equity bridge (net debt + NCI, leases / preferred if counted), implied price, upside, target-IRR max entry price.
  - [ ] WACC × g sensitivity, reverse DCF instructions, Mauboussin EV/NOPAT with company-specific rationale.
  - [ ] Opening invested capital includes deal consideration for acquisitions closing in the forecast.
  - [ ] Basis choices stated (e.g. ONON rent-as-opex: UFCF after lease principal, leases excluded from net debt; currency of the risk-free rate).
- [ ] **Charts:** retitle; re-range to the company's years; re-inject the template chart XML after saving (openpyxl drops combo charts), removing cached values so Excel redraws. Intentional `#N/A` (years with no BS / CF) is documented.
- [ ] **Deal tabs** where needed (CHRW `RXO PF`): consideration, sources & uses, PPA, standalone target, synergies and costs to achieve, pro forma P&L / shares / leverage, accretion / dilution on the company's deal definition, cross-checks to company deal metrics, sensitivity grid.
- [ ] **Optional LBO tab** (R&Y): toggles (leverage, rates, fees, amortization, sweep, entry / exit multiples), S&U = 0 check, interest on beginning debt, MOIC / IRR (closed form plus live `=IRR`), entry × exit grids.

### Phase 8 — Documentation inside the workbook
- [ ] Remove every trace of the template company: header rows, labels, Modelling Notes, cell comments, scenario-table notes, DCF rationale text, chart titles, BBB title, and the comment author name.
- [ ] Modelling Notes column: a "— modelling logic" header note on every section, and a forecast-logic note on every driver row.
- [ ] Source notes as cell comments on row labels (or on the specific cells: recast periods, corrections, definition changes).
- [ ] Definition-flag rows filled in for every bridge.
- [ ] Assumptions that are not company-disclosed are labelled "assumption" in the note (integration costs, undisclosed deal price, analyst tax rate / capex).

### Phase 9 — QA and validation
- [ ] `python3 build.py --snap [--recalc]` runs end to end from committed data.
- [ ] Recalculate with LibreOffice Calc (`libreoffice-calc`; `libreoffice-core` alone cannot open .xlsx) using the xlsx skill's `recalc.py` (`XLSX_RECALC` / `RECALC_SCRIPT`).
- [ ] `python3 models/tools/inspect_model.py <recalculated.xlsx>` reports **0 error cells and 0 non-zero check rows** (the DuPont row is skipped by design).
- [ ] `python3 models/tools/cyc.py <file>` reports **0 cycles**.
- [ ] Flip the switch to Bull and Bear: still 0 errors, the BS still balances, and the results are ordered Bull > Base > Bear on revenue / EPS / price target.
- [ ] Spot-check against the source: three random historical cells per statement; latest quarter's revenue, OI, NI, EPS, CFO, cash and total assets; published adjusted EPS and EBITDA.
- [ ] Sanity-check the forecast: margins vs history and LT targets; tax rate; capex / D&A; cash never negative unless the debt schedule draws; leverage path vs company target; buybacks vs FCF; DPS growth; ROIC trend; implied multiples.
- [ ] Every column has values where it should: no off-template ghost columns, and forecast cells that reference actuals rather than template constants.
- [ ] Store cached values in the final file (inject the recalculated values, or ship the recalculated copy) and set `fullCalcOnLoad`.
- [ ] Open the file at least once in a viewer: grouping collapsed, freeze panes, charts render, no `#REF!`.

### Phase 10 — Package and commit
- [ ] Output `models/<TICKER>_Model.xlsx`.
- [ ] Build kit `models/<ticker>_build/`: scripts, `filings.csv`, `data/*.json` (committed), `manual_items.json`, the template copy, and `README.md` from `templates/NEW_MODEL_README_TEMPLATE.md` (columns, basis, structure, bridges, sources, rebuild, validate, files).
- [ ] Don't commit raw filings (~200 MB), scratch Bull/Bear files or caches. Check `.gitignore`.
- [ ] Add a row to `models/README.md` (ticker, company, template, workbook, build kit and rebuild command).
- [ ] Add the model's entry to `models/MODEL_LESSONS.md` in the standard format (coverage and basis, operating build, bridges, data quirks, deals, calibration, BS / cash / capital, valuation, reusable lessons). Promote any general lesson to this playbook.
- [ ] Commit message: `Add <Company> (<TICKER>) 3-statement model built on the MLM template`, with a body covering the build, bridges and checks, history and sources, calibration and scenarios, deal blocks, and the share price and date.
- [ ] Push to the working branch. Open a PR only if asked.

---

## 4. Reference

### 4.1 Standard check rows (each must read 0)
| Area | Check |
|---|---|
| Build | Build vs consolidated revenue / profit; Σ segments + corporate vs consolidated OI; growth decomposition vs reported growth |
| Calibration | Current-year revenue / anchor KPI vs guidance end-point |
| IS | NI attributable vs reported; EPS vs reported (memo) |
| Bridges | Model vs company-published Adj. EBITDA / adjusted OI / adjusted EPS / FCF / AGP |
| CF | CFO + CFI + CFF (+ FX) = Δcash; beginning + Δ = ending |
| BS | TA − TL&E = 0 (all columns); TA vs reported; BS cash vs CF ending cash |
| Schedules | PPA: assets − liabilities − consideration = 0; S&U = 0 (deal / LBO tabs) |

### 4.2 Adapting the template by company type
| Situation | Precedent | Adaptation |
|---|---|---|
| Single reportable segment | RBA, KRMN, LOAR | Revenue-stream or end-market build; margins at group level; anchor on the company's guided KPI |
| Unit economics disclosed | MLM, VMC, ODFL, SAIA, XPO, CHRW | Volume × price build, price / volume bridge, fall-through; fuel surcharge from DOE diesel × surcharge table (SAIA) |
| No guidance | ODFL, RMS | Mid-quarter updates; seasonality best / avg / worst; scenario-only forecast |
| No non-GAAP published | ODFL, DHR (EBITDA), STE (EBITDA) | Model-defined bridges, clearly labelled, checked against XBRL / GAAP |
| Definition changed over time | TDY, LOAR, RBA, MLM | Definition-flag row, in-force definition per period, current-definition memo series |
| Spin-offs / disc ops | DHR, STE, BWXT, XPO | Hybrid recast or post-spin history; recast cell comments; rebuild originally reported adjusted EPS in memo |
| IFRS / foreign currency | ONON, RMS, BC, TFI | Reporting currency; constant-currency + FX build; price × FX input; IFRS 16 lease schedule; rent-as-opex DCF option |
| Half-year reporters | RMS, BC | H1 / H2 / FY columns (H2 = FY − H1); quarterly revenue memo |
| Recent IPO | LOAR, ONON, KRMN | Annual columns from the prospectus; P&L-only years flagged; BS / CF start when available |
| Non-December fiscal year | STE (Mar), CTAS (May), HEI (Oct) | Column labels by fiscal year; DCF discount dates moved to FY ends |
| Pending / new acquisition | DHR, MLM, CTAS, ESAB, CSGP, UBER, CHRW | Separate block, PPA, financing, synergies, closing-date toggle; deal tab for large deals |
| Dual-class / splits | ONON, HEI, CTAS, ODFL | Class-equivalent shares; split-adjust by source filing date |
| Private company | R&Y | Compilation statements; implied CF from BS changes; LBO tab |

### 4.3 Pitfalls that have bitten before
- Template-company constants left in forecast formulas or notes (Moog `888`, MLM LNA rows, MLM-specific DCF text).
- Writing to the wrong columns (4-digit vs 2-digit year index), so the data is invisible in the period columns.
- Template SUMs over rows the new company doesn't populate (equity bridge = 0, ratios off the empty adjusted block). Repoint or clear them.
- Formulas referencing COGS for a company without COGS (inventory / AP days). Use a revenue basis or hold flat.
- Using cash as the BS plug instead of the debt schedule. It hides financing gaps; use revolver / CP to minimum cash.
- Circular interest. Always calculate on opening balances.
- Mixing restated and original bases in one y/y comparison. Pick a basis policy and comment the recast cells.
- Missing Q4s / release-only quarters (no MD&A exhibit). Derive FY − 9M and note it.
- Issuer sign flips between years (TFI FinanceCosts). Normalise signs in `normalize.py` and note them.
- Saving with openpyxl drops chart formatting. Re-inject the template chart XML after every save.
- Files without cached values look blank in viewers. Store calculated values.
- `libreoffice-core` cannot open .xlsx; install `libreoffice-calc`.
