# META data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. The extraction is programmatic (`extract.py` with `parse_release.py`); this file documents what each record holds and the rules the code follows.

## Sources
- **SEC EDGAR only** (CIK 0001326801; Facebook, Inc. until 28-Oct-2021, same CIK). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$META_SRC/txt` (`h2t.py`): one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1326801/<accession-no-dashes>/<doc>`; each record's `sources` lists them.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "—" means zero.
  - A footnote marker after a number ("6,436 (1)") is dropped, but a bare "(7)" is −7.
  - Year headers may carry markers ("2016 (1)", "2019*").
- **Column order:** the 2012–16 releases print the prior year first and 2017+ the current year first. Columns are resolved from each table's year header, never by position.
- **XBRL company facts** (`$META_SRC/cf_1326801.json`; subset in `data/_xbrl.json`): cross-checks plus interest income / expense and dividends per share.
- **EDGAR requests:** User-Agent on every request, < 5 per second, back-off on errors.

## Basis rules
- **Quarters (Q2-12 – Q2-26):** that quarter's release, three-month columns, as originally reported. The cash flow is also three-month (every release presents it), so no year-to-date derivation is needed.
- **Fiscal years 2012–2025:** the Q4 release's year columns (income statement, cash flow, reconciliations) and the Q4 balance sheet.
- **FY2009–2011:** the IPO prospectus (424B4): statements of income and cash flows, balance sheets at 31-Dec-2010 and 2011, the MD&A advertising revenue, and the EPS note (two-class shares; `manual_items.json` → `pre_ipo_eps`).
- **Segments:** Q4-2021 release (Q4/Q3/Q2/Q1-2021, Q4-2020, FY2019–2021); then each release's three-month and year columns.
- **Prior-year comparatives (`py.is`):** the prior-year column as presented a year later. They are kept to flag re-presentations (normalised as `*_py` keys where they differ by more than $0.5m).
- **10-Q / 10-K extras (`q10`):**
  - Ad impressions / "number of ads delivered" and average price per ad y/y % (from the MD&A sentence naming the quarter; the year from the 10-K).
  - Revenue by geography (customer billing address).
  - Class A + Class B shares issued and outstanding at the balance-sheet date (balance-sheet caption).
- **Units:** USD millions as published; shares and people in millions; per-share as published; growth KPIs as fractions (0.14 = 14%).
- **Signs:** costs positive; provision for income taxes positive (a "(Provision for) benefit" caption is flipped); cash flow as presented.
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented = absent (null). **Never estimate.** Derived values (Q4 geography = year − nine months; working capital = CFO − NI − D&A − SBC − deferred tax) are made in `normalize.py` and noted in the model.

## Record layout (`data/<period>.json`)
```json
{
  "period": "Q2-26", "release_date": "2026-07-29", "sources": ["https://...ex991.htm", "https://...10q.htm"], "notes": [],
  "is":    {"rev", "cogs", "rd", "mm", "ga", "costs", "oi", "int_exp", "oth", "io_net", "ebt", "tax", "ni", "ni_part", "ni_common",
            "eps_b", "eps_d", "sh_b", "sh_d", "sbc_is"},
  "bs":    {"cash", "ms", "ar", "itr", "prepaid", "tca", "nme", "ppe", "rou", "gw", "intang", "oa", "ta", "ap", "pp", "olc", "accr", "defrev",
            "clc", "tcl", "oln", "cll", "ltd", "ltt", "ol", "tl", "pref", "apic", "aoci", "re", "te", "tle"},
  "cf":    {"ni", "dda", "sbc", "def", "cfo", "capex", "ppe_proc", "ms_net", "nme", "acq", "cfi", "eq_iss", "netshare", "bb", "div",
            "debt_iss", "debt_rep", "lease", "cff", "fx", "net", "beg", "end"},
  "ngaap": {"adv", "adv_exfx", "rev_exfx", "ng_costs", "sbc_ng", "payroll", "amort", "ng_oi", "tax_adj", "ng_ni", "ng_sh", "ng_eps",
            "fcf_cfo", "fcf_capex", "fcf_cl", "fcf_flp", "fcf"},
  "seg":   {"foa_adv", "foa_oth", "foa_rev", "rl_rev", "rev", "foa_oi", "rl_oi", "oi"},
  "kpi":   {"dau", "mau", "mobile_dau", "dap", "map", "headcount", "impr_g", "price_g"},
  "q10":   {"impr_g", "price_g", "geo_usc", "geo_eu", "geo_ap", "geo_row", "sh_out"},
  "py":    {"is": {...}}
}
```
Keys are present only where the period's documents present the line.

## One-off items (`manual_items.json` → `one_offs`)
Only items the company **quantified** in a release are recorded, with the release wording, amount, the company's "excluding" EPS where stated, and the URL:
- `legal`: FTC 2019, Q2-23 accrual, Q4-24 release (negative), Q2-26.
- `restr`: Q3-22 lease impairment, Q4-22–Q4-23 restructuring, Q2-26 severance.
- `tax`: Q4-17 Tax Act, Q2-19 Altera, Q3-20 R&D election, Q3-25 OBBBA charge, Q1-26 Notice 2026-7 benefit.

Items named but not quantified (Q2-24 Texas settlement) are listed under `named_not_adjusted` and left in.

## Self-checks (`check_data.py`; ~1,500 checks)
- **IS:** cost lines sum to total costs; revenue − costs = income from operations; + interest & other = pre-tax; − tax = net income; − participating = common; EPS = NI ÷ diluted shares (±0.01; ±0.011 for 2013, rounded shares).
- **Segments:** FoA + RL revenue = revenue; FoA + RL results = income from operations; advertising + other = FoA revenue.
- **Geography:** Σ regions = revenue (±1.1 where Q4 is derived).
- **Non-GAAP (IPO–2016):** OI + SBC + payroll tax + amortization = non-GAAP OI; + tax adjustments = non-GAAP NI; non-GAAP NI ÷ non-GAAP shares = non-GAAP EPS.
- **FCF:** CFO + capex (+ capital-lease acquisitions 2013–14) (+ finance-lease principal) = published FCF.
- **Cash and balance sheet:** beginning + change = ending cash; total assets = total liabilities and equity.
- **Cross-checks and sums:** XBRL (earliest-filed fact) for revenue, operating income, net income, diluted EPS, CFO and total assets; Σ quarters = year for flows (documented exceptions listed in the script).
