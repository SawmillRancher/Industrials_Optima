# <TICKER> data extraction: schema and rules

<!-- Copy to models/<ticker>_build/EXTRACTION_SCHEMA.md. Replace <…>, then add company-specific keys (volumes, KPIs, backlog,
end markets, guidance). Give this file, unchanged, to every extraction agent. Derived from the DHR / TDY / WAB schemas. -->

## Sources
- **SEC EDGAR only** (CIK <##########>; predecessor CIKs: <…>). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$<TICKER>_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/<cik>/<accession-no-dashes>/<doc>`. Record those URLs in `sources`.
- **Period index:** `$<TICKER>_SRC/period_index.json` maps each period key to `release`, `filing` (10-Q, or 10-K for annual / Q4), `next_release` and `next_filing` (the same documents one year later, for comparatives).
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "—" means zero.
- **Optional cross-check:** `$<TICKER>_SRC/companyfacts.json` (XBRL company facts).
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** income statement, non-GAAP bridges and segment data come from that quarter's release (three-month columns), **as originally reported**.
  - Q4 = the Q4 release's three-month column. Only if that is missing, use FY − 9M, and say so in `notes`.
- **Balance sheet:** the quarter-end statement.
- **Cash flow:** the **year-to-date** statement; set `cf.ytd_months` to 3, 6, 9 or 12.
- **Annual records:** the Q4 release twelve-month columns plus that year's 10-K. **The 10-K wins** when they differ.
- **Prior-year comparatives (`py`):** the prior-year column as presented in this period's documents. Set `py.restated` true, with the reason, if it differs from what was originally reported.
- **Units:**
  - <currency> millions to one decimal as published (thousands ÷ 1,000);
  - shares in millions (3 dp);
  - per-share as published;
  - percentages as numbers in percent (3.5 = 3.5%).
- **Stock splits:** record shares / EPS / DPS **exactly as published**, with `is.per_share_basis`. Don't adjust them yourself.
- **Signs:**
  - costs positive;
  - two-sided items signed by their effect on earnings / cash (income or inflow +, expense or outflow −);
  - cash flow as presented.
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented = null. **Never estimate.** Any computed value (sum, difference, FY − 9M) is stated in `notes`.

## Output
One JSON file per period: `models/<ticker>_build/data/<period_key>.json`. Keys look like `2008`, `Q1-13`, `Q4-25`, `H1-26` or `9M-25`. Write valid JSON: no comments, no trailing commas.

```json
{
  "period": "Q2-26", "period_end": "YYYY-MM-DD",
  "sources": {"release": "https://...", "filing": "https://..."},
  "is": {
    "sales": null, "cogs": "positive", "gp": null, "sga": "positive", "rnd": "positive",
    "other_op_lines": [["exact label", "positive = expense"]], "op_profit": null,
    "nonop_lines": [["exact label", "signed: income positive"]],
    "interest_exp": "positive", "interest_inc": "positive", "ebt": null, "tax": "positive = expense",
    "cont_ops": null, "disc_ops": "signed", "net_income": null, "nci": "positive = deducted", "ni_parent": null,
    "shares_basic": null, "shares_diluted": null, "eps_basic": null, "eps_dil": null, "eps_dil_cont": null,
    "dps": null, "per_share_basis": "pre_split | post_split"
  },
  "seg": {
    "segments": [{"name": "exact", "sales": null, "op_profit": null, "adj_op": null, "amort": null, "dep": null,
                  "growth_total": null, "growth_acq": null, "growth_fx": null, "growth_organic": null}],
    "corporate": "signed", "total_growth": {"total": null, "acq": null, "fx": null, "organic": null},
    "kpis": {"<volume / price / backlog / units>": null},
    "seg_note": "structure in force / recasts"
  },
  "ngaap": {
    "adj_ebitda_pub": null, "adj_op_pub": null, "adj_ni_pub": null, "adj_eps_pub": null, "fcf_pub": null,
    "eps_bridge_start": null, "eps_bridge_start_label": "exact",
    "eps_bridge": [["exact label", "per-share value as added"]],
    "item_amounts": [["exact label", "pretax $m as added", "after-tax $m", "op | nonop | tax | below_ni | discops", "CAT"]],
    "guidance": "forward guidance text (ranges for revenue, organic growth, margins, adj. EPS / EBITDA, tax, interest, capex, FCF, shares)",
    "notes": "definition of each adjusted measure in this period"
  },
  "cf": {
    "ytd_months": 12, "net_income": null, "dep": null, "amort": null, "sbc": null, "deferred_tax": null,
    "gains": null, "wc_change": "signed sum of change lines", "cfo": null,
    "capex": "negative", "capex_disposals": null, "acquisitions": "negative", "divest": null, "cfi": null,
    "debt_proceeds": null, "debt_repay": "negative", "debt_net_short": null, "dividends": "negative",
    "buyback": "negative", "stock_iss": null, "cff": null, "fx": null, "net_change": null,
    "cash_begin": null, "cash_end": null, "cash_basis": "cash | cash+restricted",
    "lines_raw": [["exact label", "value as shown"]]
  },
  "bs": {
    "cash": null, "ar": null, "inventories": null, "other_ca": null, "tca": null, "ppe": null, "rou": null,
    "goodwill": null, "intangibles": null, "other_nca": null, "ta": null,
    "st_debt": null, "ap": null, "accrued": null, "other_cl": null, "tcl": null, "ltd": null, "lease_ltl": null,
    "other_ncl": null, "tl": null, "equity_parent": null, "nci": null, "te": null, "tle": null, "shares_out": null,
    "lines_raw": [["exact label", "value"]]
  },
  "py": {"restated": false, "notes": null, "is": {}, "segments": [], "adj_eps_pub": null},
  "extra": {
    "employees": null, "acquisitions": [["name", "close date", "consideration $m", "segment"]],
    "divestitures": [["name", "date", "notes"]], "debt_maturities": [["year", "$m"]],
    "amort_schedule": [["year", "$m"]], "notes": null
  },
  "notes": "computed values; any self-check that does not pass and why"
}
```

## Adjusting-item categories (CAT)
| Code | Meaning |
|---|---|
| AMORT | Acquired-intangible amortization |
| ACQ | Acquisition, transaction and integration costs |
| STEPUP | Inventory step-up and other purchase accounting |
| RESTR | Restructuring |
| PENSION | Pension items |
| SBC | Stock-based compensation |
| DEBT | Debt extinguishment |
| GAIN | (Gain) / loss on sale |
| IMPAIR | Impairment |
| LEGAL | Litigation |
| OTHER | Any other item; keep the company's label |
| TAX | Tax effect of the items |
| TAXD | Discrete tax items |
| NCI | Share attributable to NCI |

## Self-checks before writing each period
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:** gp − sga − rnd − Σ other_op = op_profit; op_profit + Σ nonop − interest_exp + interest_inc = ebt; ebt − tax = cont_ops; cont_ops + disc_ops = net_income (±0.6).
- **Segments:** Σ segment sales = sales; Σ segment op_profit + corporate = op_profit (±1).
- **Non-GAAP:** eps_bridge_start + Σ eps_bridge = adj_eps_pub (±0.01).
- **Cash flow:** cfo + cfi + cff + fx = net_change; cash_begin + net_change = cash_end (±0.6).
- **Balance sheet:** ta = tle; components sum to subtotals (±1).
