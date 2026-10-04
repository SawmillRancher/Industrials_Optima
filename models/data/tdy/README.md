# Teledyne Technologies (TDY) data-extraction spec

Company: Teledyne Technologies Incorporated, SEC CIK 0001094285. Fiscal year = 52/53 weeks ending on the Sunday nearest
31-Dec; quarters end on Sundays (13-week quarters; Q4 of FY2009, FY2015 and FY2020 has 14 weeks — FY2009 ended 3-Jan-2010,
FY2015 ended 3-Jan-2016, FY2020 ended 3-Jan-2021). Period keys follow the fiscal year, not the calendar date.
Sources: SEC EDGAR only (www.sec.gov/Archives/edgar/data/1094285/...). investors.teledyne.com is NOT reachable from this
environment — every earnings release is filed on EDGAR as Form 8-K Ex. 99.1, so use those.
Use a User-Agent header on every request:
`curl -sS -A "Industrials Optima research payton.liske@gmail.com" <url>` (EDGAR rejects requests without one; keep to <5 req/s).

Local cache (reuse; download anything missing into the same folders):
- Filing list (accession, form, primary doc, report date): `$S/tdy/filings.txt`
- All 10-K primary documents: `$S/tdy/raw/10k/<reportDate>_<doc>` (FY2005–FY2025)
- Earnings-release exhibits (8-K Ex. 99.1): `$S/tdy/raw/er/<filingDate>_<exhibit>`, index in `$S/tdy/er_index.txt`.
  Known gaps in the cache: the Q4-2008 release (filed ~Jan-2009) and the Q2-2014 release (filed ~Jul-2014) — find them in
  the EDGAR filing index (https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001094285&type=8-K&dateb=&owner=include&count=100
  or https://data.sec.gov/submissions/CIK0001094285-submissions-001.json) and download.
- 10-Qs: not cached — download from filings.txt (primary doc URL = https://www.sec.gov/Archives/edgar/data/1094285/<accession-no-dashes>/<primaryDoc>) into `$S/tdy/raw/10q/`.
- XBRL company facts (2009+): `$S/tdy/raw/companyfacts.json` — use for cross-checks (us-gaap:Revenues / SalesRevenueNet,
  NetIncomeLoss, OperatingIncomeLoss, EarningsPerShareDiluted, NetCashProvidedByUsedInOperatingActivities, Assets).
where `$S` = /tmp/claude-0/-home-user-Industrials-Optima/27dc6f25-6725-5219-80ee-7857735318e3/scratchpad

Parse HTML with python (bs4 + lxml installed; pandas.read_html works too). Prefer parsing tables programmatically over
reading by eye, but verify totals.

## Units & signs
- USD millions (Teledyne reports in $ millions with one decimal; keep the decimal). Shares in millions. Per-share in USD.
- Revenue / expense lines: positive magnitudes (expenses positive).
- Lines that can be either sign (other income/expense, non-service pension, gains/losses, NCI, discontinued ops): signed by
  their effect on income (income/gain = +, expense/loss = −).
- Cash flow: signed as presented (outflows negative).
- If a value is not disclosed for a period, OMIT the key (do not write 0). Write 0 only when the filing shows "—"/nil.
- Always use the LATEST filing that presents a period (recast figures), unless told otherwise; note restatements in `notes`.
  Exception: segment data for FY2006–07 exists only on the legacy segment basis — record it in the legacy keys.

## Period keys
Quarter: "Q1/13" … "Q4/25", "Q1/26", "Q2/26". Annual: "2006" … "2025". Six-month: "1H/26".
For quarterly-era years also give FY figures (key "2015" etc.) from the 10-K / Q4 release so totals can be checked.
Q4: Teledyne's Q4 releases present fourth-quarter figures (three/four months) — use them directly; if a line is only
available FY and 9M, Q4 = FY − 9M and say so in notes.

## Output JSON (one file per agent, written to /home/user/Industrials_Optima/models/data/tdy/<file>.json)
```
{
  "periods": {
     "<period key>": {
        "is":   { <IS keys> },
        "seg":  { <segment keys> },
        "ops":  { <operating-metric keys> },
        "adj_oi":  { "oi_gaap": x, "adj_oi_published": x, "adj_om_published": x (fraction),
                     "items": [ {"label": "<company wording>", "cat": "<CAT>", "value": x}, ... ] },
        "adj_ni":  { "adj_ni_published": x, "adj_eps_published": x, "base": "<GAAP line the company bridge starts from>",
                     "items": [ {"label": "...", "cat": "<CAT>", "value": x}, ... ] },
        "bs":   { <BS keys> },      # only where asked
        "cf":   { <CF keys> },      # only where asked
        "src":  ["<url>", ...]
     }
  },
  "notes": ["<free text: definition changes, basis/restatement notes, anything odd — cite period + url>"]
}
```
`adj_oi` = the company's consolidated GAAP operating income → non-GAAP operating income reconciliation (2021+; and any
earlier period where the company published an adjusted operating income/margin). `adj_ni` = net income (attributable to
Teledyne) → non-GAAP net income / non-GAAP diluted EPS reconciliation, in whatever form the company published it in that
period (2005–06 "excluding pension and stock option expense"; Q4/16–2017 "non-GAAP" EPS ex restructuring/other charges;
2021+ FLIR-era definition). If in a period the company published NO adjusted EPS/NI, omit `adj_ni` entirely.
Adjusting items: `value` = amount ADDED in the company's reconciliation (add-back of a cost = positive; removal of a gain =
negative; tax effect usually negative). Where the company gives per-share amounts only, also give the $m amount if stated
anywhere; otherwise record {"label":..., "cat":..., "value_eps": x} and say so in notes.

## IS keys (consolidated statement of income)
net_sales, product_sales, service_sales (only where presented), cost_sales (total cost of sales incl. product + service),
sga (selling, general and administrative incl. R&D as presented), rd_company (company-funded R&D, from MD&A/notes, memo),
other_op (any other line inside operating income, signed by income effect — label in notes; e.g. "gain on sale",
"impairment"), op_income,
interest_exp_net (interest and debt expense, net — positive = expense; Teledyne nets interest income), interest_income
(only if separately disclosed), non_service_pension (non-service retirement benefit income/(expense), signed; ASU 2017-07
from 2018, recast 2017), other_income (other income (expense), net, signed), pretax (income from continuing operations
before taxes), tax (provision, expense positive), income_cont (income from continuing operations), disc_ops (income/(loss)
from discontinued operations net of tax, signed; e.g. Teledyne Continental Motors piston engines sold Apr-2011),
net_income (net income incl. NCI), nci (net income attributable to NCI, signed as reported — positive = NCI share of
income), ni_teledyne (net income attributable to Teledyne), shares_basic, shares_diluted (weighted avg, m), eps_basic,
eps_diluted (net income attributable to Teledyne per diluted share), eps_diluted_cont (continuing ops, if presented).
Memo: da (total depreciation and amortization, from CF statement or release), depreciation, amort_intangibles
(amortization of acquired intangible assets — total, from release/10-K), sbc (stock-based compensation), pension_expense
(total pension / retirement benefit expense (income) incl. service cost, signed as expense positive, if disclosed in the
release), capex (from release, positive).

## Segment keys ("seg")
Current basis (FY2008+ as recast in the FY2010 10-K; current four segments):
sales_di, sales_inst, sales_ade, sales_es (segment net sales — external sales as reported in the segment table),
oi_di, oi_inst, oi_ade, oi_es (segment operating income as reported),
corp_exp (corporate expense, positive = expense), other_seg (any other reconciling line between total segment OI and
consolidated OI, signed by income effect, label in notes — e.g. "pension expense" not allocated in some years),
amort_di, amort_inst, amort_ade, amort_es (segment acquired-intangible amortization, 2021+ releases),
adj_oi_di, adj_oi_inst, adj_oi_ade, adj_oi_es, adj_corp (non-GAAP operating income by segment / corporate, 2021+),
seg_items (list of other segment non-GAAP items {"seg": "ade", "label": ..., "cat": ..., "value": x}),
Annual only (10-K segment note): da_di, da_inst, da_ade, da_es, da_corp (segment D&A), capex_di … capex_corp,
assets_di … assets_corp (identifiable assets), intersegment sales if disclosed.
Product lines (as given in releases/10-K MD&A): inst_marine, inst_env, inst_etm (Instrumentation: marine,
environmental, electronic test & measurement); ade_aero, ade_def (A&DE: aerospace electronics, defense electronics);
es_eng, es_energy (Engineered Systems: engineered products & services, energy systems / turbine engines as labelled —
put exact labels in notes). Only where disclosed.
Legacy basis (FY2006–07, and FY2008–09 as originally reported if easily available): leg_sales_ec, leg_sales_ses (Systems
Engineering Solutions / Engineered Systems), leg_sales_aec (Aerospace Engines and Components), leg_sales_eps (Energy
(and Power) Systems), leg_oi_ec, leg_oi_ses, leg_oi_aec, leg_oi_eps, leg_corp_exp, leg_other (signed).

## Ops keys
acq_sales (incremental sales from acquisitions in the period, as stated in the release — "included $x million in
incremental sales from recent acquisitions"; label acquisitions in notes), orders, funded_backlog (period end),
sales_us_gov (sales to US Government — annual 10-K), sales_intl / sales_us (geographic, annual 10-K: give what's
disclosed, e.g. rev_us, rev_intl or by country/region with keys rev_<region>), fcf_published (company free cash flow),
capex_published, net_debt_published, leverage_published (company leverage ratio, x), employees (annual).
Outlook (only in Q2/26 file, also Q4/25 and Q1/26 for context): put under top-level key "outlook" in the file:
{"source_period": "Q2/26", "fy_gaap_eps": [low, high], "fy_nongaap_eps": [low, high], "q3_gaap_eps": [low, high],
"q3_nongaap_eps": [low, high], "tax_rate": x, "fy_amort": x (if given), "other": "<any other stated outlook items:
sales, capex, FCF, amortization, interest, pension, SBC>"} and the full outlook text in notes.

## Adjusting-item categories (CAT)
AMORT (acquired intangible asset amortization), ACQ (acquisition-related transaction and integration costs / FLIR
transaction costs), STEPUP (inventory step-up / fair-value adjustment of acquired inventory, and other purchase-accounting
items e.g. deferred revenue fair value), RESTR (restructuring / severance / facility consolidation), PENSION (pension
expense or non-service pension exclusion), SBC (stock option / stock-based compensation exclusion, 2005–06 style),
DEBT (debt extinguishment / bridge financing / make-whole), GAIN ((gain)/loss on sale of business or assets),
IMPAIR (impairment / write-downs), LEGAL (litigation / legal settlements), OTHER (any other pre-tax item — keep label),
TAX (tax effect of the pre-tax adjustments), TAXD (discrete tax items: FLIR acquisition-related tax matters, tax-law
changes, other discrete tax benefits), NCI (portion attributable to NCI, if any).

## BS keys (period end)
cash, receivables (accounts receivable net), unbilled (unbilled receivables / contract assets), inventories,
prepaid_other_ca (prepaid expenses and other current assets), held_for_sale, total_ca, ppe (net), rou (operating lease
ROU), goodwill, intangibles (acquired intangibles net), prepaid_pension, dta, other_assets, total_assets,
ap (accounts payable), accrued_liab (accrued liabilities), contract_liab (customer deposits / contract liabilities /
advance billings if separate), current_ltd (current portion of LTD and other debt / short-term borrowings),
held_for_sale_liab, total_cl, ltd, lt_lease_liab, pension_liab (accrued pension / postretirement), dtl,
other_ncl, total_liab, redeemable_nci (temporary equity if any), common_stock, apic, retained_earnings, treasury_stock
(negative), aoci, equity_teledyne, nci, total_equity, total_le, shares_outstanding_end (m, from 10-K/10-Q cover or
equity note). Components must sum to reported totals; put residuals in prepaid_other_ca / other_assets / other_ncl and say so.

## CF keys (annual, and 1H/26 = six months)
net_income (incl. NCI, as on CF), disc_ops_cf (if CF starts from continuing ops / adjusts disc ops), depreciation,
amortization (or da if only combined; give da as total always), sbc, deferred_tax, pension_cf (pension / retirement
benefit expense or income adjustment), pension_contrib (contributions, if a separate line), gain_disp (as presented),
other_noncash, chg_wc (total change in operating assets & liabilities, all lines combined — list the lines in notes if
material), cfo;
capex (PP&E purchases, negative), acquisitions (net of cash acquired, negative), proceeds_disp (sale of businesses /
assets, positive), other_investing, cfi;
debt_issued (proceeds from debt incl. credit facility borrowings), debt_repaid (negative), st_debt_net (net change if
presented net), debt_issue_costs, buybacks (purchase of treasury stock, negative), options_proceeds (proceeds from
stock option exercises, positive), tax_benefit_sbc (excess tax benefit, pre-2017), dividends (if any — Teledyne pays
none; confirm), other_fin, cff; fx_effect, chg_cash, cash_begin, cash_end.
Check: cfo + cfi + cff + fx_effect (+ disc ops cash if separate — key disc_ops_cash) = chg_cash; components sum to
subtotals (put residuals in other_* and say so).

## Supplemental (top-level key "supplemental", agent A6 only)
amort_schedule (expected future amortization of acquired intangibles from the FY2025 10-K: 2026–2030 + thereafter;
also historical total amortization by year 2006–2025), debt (FY2025 10-K and 30-Jun-26 debt table: each instrument,
principal, coupon, maturity), goodwill_by_segment (FY2025), acquisitions (list by year 2006–2026: name, close date,
consideration, segment — from 10-K acquisitions notes), buyback_authorization (current), pension (funded status FY2025).
