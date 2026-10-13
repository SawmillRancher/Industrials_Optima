# MA data extraction: schema and rules

Mastercard's data comes from two routes, both SEC EDGAR only:
1. **Scripted statements** (`extract.py` + `parse_release.py`): income statement, balance sheet, cash flow and the GDV
   operating-performance rows from each earnings release, written to `data/<period>.json`.
2. **Transcribed tables** (parallel agents, one period range each, this file given to every agent unchanged): non-GAAP
   reconciliations, release-narrative KPIs and revenue by category from the 10-Q / 10-K, written to
   `data/_agent/<range>.json` and merged by `normalize.py`.

## Sources
- **SEC EDGAR only** (Mastercard Incorporated, CIK 1141391; no predecessor registrant: IPO 25-May-2006). The investor-relations
  site is blocked; its releases are the 8-K Item 2.02 Ex. 99.1 exhibits. The 8-K Ex. 99.2 slide decks (filed to 2019) are
  image-based and carry no usable outlook numbers.
- **Text versions** of every document are in `$MA_SRC/txt` (one table row per line, cells joined by ` | `).
  `$MA_SRC/period_index.json` maps each period key to its `release` (8-K Ex. 99.1; annual = the Q4 release) and `filing`
  (10-Q, or the 10-K for annual and Q4 periods), each with `txt`, `url` and `date`. Record the URLs in `sources`.
- **Text quirks:** a cell that was only ")" is dropped, so "(25,433" is negative; "—" means zero; "**" means not applicable
  (treat as null); words are sometimes split by stray line breaks ("Second qu / arter").
- **XBRL company facts** (`$MA_SRC/cf_1141391.json`; subset committed as `data/_xbrl.json`) are used only for cross-checks
  and for shares outstanding.

## Periods and columns
- **Annual FY2006–FY2025:** the Q4 release's twelve-month columns; balance sheet at 31-Dec; cash flow for the year.
- **Quarters Q1-13 – Q2-26:** the three-month column of each quarter's own release, as originally reported. Q4 uses the Q4
  release's three-month column.
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Units:** USD millions (releases filed before Apr-2010 are in USD thousands, ÷ 1,000); shares in millions; per share as
  published. Percentages as numbers in percent (12 = 12%).
- **Stock split:** 10-for-1, effective 21-Jan-2014. Record shares and per-share data exactly as published; `normalize.py`
  restates documents filed before 22-Jan-2014 (shares × 10, per share ÷ 10).
- **Signs:** costs positive; two-sided items signed by their effect on income; cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = null (omit). **Never estimate.** Any computed value is stated in `notes`.

## Scripted record keys (`data/<period>.json`)
```
period, fy, q, sources{release, release_date}, notes[]
is:      rev, ga, am, lit, char, da (or dep + amo), opex, oi, inv_inc, eq_gl, int_exp (negative as presented), oth, oth_tot,
         ebt, tax, ni_tot, nci, ni_ma, eps_b, sh_b, eps_d, sh_d
py.is:   the same keys from the prior-year column of this release (restatement checks)
bs:      cash, rcash_lit / rcash, rsd_a (+ rsd_a_2 = liability), inv_cur (+ inv_cur_2 noncurrent), ar, settle_a, tca, ppe, dta (+ dta_2 = DTL),
         gw, intang, ta, ap, settle_l, lit_l (+ lit_l_2 noncurrent), accr, std, tcl, ltd, tl, rnci, minority, eq_ma, nci, teq, tle
cf:      ytd_months, ni, da, sbc, deftax, eq_gl, cust_inc, cfo, capex, capsw, acq, cfi, bb, div, cff, fx, net, beg, end
*_raw:   every statement row as [label, [values]] (USD m)
op_q / op_rows: 'Worldwide' rows of the operating-performance (GDV) tables: [GDV $bn, growth USD %, growth local %, purchase volume $bn, ...];
         op_rows[0] = current three months, op_rows[3] = current year to date (all programs)
```

## Transcribed record (`data/_agent/<range>.json`: a JSON list, one object per period key)
```json
{
  "period": "Q2-26",
  "sources": {"release": "https://...", "filing": "https://..."},
  "ngaap": {
    "published": true,
    "gaap":  {"opex": 3690, "oth_inc": -101, "ni": 4388, "eps_d": 4.97, "etr": 20.0, "op_margin": 60.2},
    "items": [
      {"label": "exact company label", "cat": "EQGL", "opex_pre": null, "oth_pre": 2, "ni": 5, "eps": 0.01},
      {"label": "Litigation provisions", "cat": "LEGAL", "opex_pre": 82, "oth_pre": null, "ni": 59, "eps": 0.07}
    ],
    "adj":   {"rev": null, "opex": 3608, "oth_inc": -100, "ni": 4453, "eps_d": 5.04, "etr": 20.0, "op_margin": 61.1},
    "def_note": "what the company says its non-GAAP measures exclude in this period (short quote)"
  },
  "kpi": {
    "rev_g": 14, "rev_g_cn": 12, "gdv_g_local": 8, "xb_g_local": 12, "xb_label": "Cross-border volume",
    "sw_g": 9, "sw_label": "Switched transactions", "cards_bn": 3.7,
    "pn_g": 10, "pn_g_cn": 8, "vas_g": 20, "vas_g_cn": 18, "rebates_g": 22
  },
  "revcat": {
    "basis": "legacy | current",
    "q": [["exact label", 5451]],
    "ytd": [["exact label", 10399]],
    "fy": [["exact label", 32791]]
  },
  "notes": "anything computed, any self-check that fails and why"
}
```
- **ngaap.published:** true if the release reconciles GAAP to adjusted (non-GAAP / "excluding special items") figures for this
  period's own column (three months for a quarter, twelve months for a year). If the release gives only GAAP figures, set
  false, leave `items` empty and `adj` null.
- **ngaap.items, sign rules (amounts as the reconciliation shows them, converted to these signs):**
  - `opex_pre`: pre-tax amount removed from operating expenses (a charge excluded = positive; a credit excluded = negative).
  - `oth_pre`: pre-tax amount by which adjusted other income (expense) is higher than GAAP (a loss excluded = positive; a gain
    excluded = negative).
  - `rev_pre`: pre-tax amount by which adjusted net revenue is higher than GAAP (rare; e.g. a revenue-related special item).
  - `ni` / `eps`: effect on net income / diluted EPS (adjusted − GAAP; positive when the item raises adjusted figures).
    Tax-only items (cat TAXD) have no pre-tax amount.
- **Categories (`cat`):** LEGAL (litigation provisions / settlements, including U.S. merchant class, European Commission,
  interchange), EQGL ((gains) losses on equity investments), RESTR (restructuring), TAXD (discrete tax items: U.S. tax reform,
  tax-law changes, tax settlements), GAIN (gains on sale of businesses or securities, e.g. Redecard), FOUNDATION (charitable
  contribution to the Mastercard Foundation), IMPAIR, ACQ (acquisition-related), OTHER (keep the label; e.g. indirect-tax
  matter, Russia / Ukraine charges, termination of customer agreement).
- **ngaap.adj:** the published adjusted figures for this period's column. If the release gives only a net-income or EPS
  bridge, fill what is given and leave the rest null.
- **kpi:** growth rates as stated in the release text for this period (three months for quarters, the full year for annual
  records), in percent. `xb_g_local` = cross-border volume growth on a local-currency basis; `sw_g` = switched transactions
  growth (called "processed transactions" in older releases: record the label in `sw_label`). Leave null what is not stated.
  `rev_g_cn` = currency-neutral (or "adjusted for currency" / "FX-adjusted") net revenue growth.
- **revcat:** net revenue by category from the 10-Q / 10-K (MD&A revenue table or revenue note), exact labels, USD m:
  - quarter records: `q` = three-month column, `ytd` = year-to-date column (Q1: `ytd` = `q`);
  - annual records: `fy` = the 10-K full-year column; for Q4 records leave `revcat` null (normalize.py derives FY − 9M);
  - `basis` = "legacy" for the domestic assessments / cross-border / transaction processing / other revenues / rebates and
    incentives presentation, "current" for payment network / value-added services and solutions. If a filing presents both
    (the payment-network "key metrics" assessments and the two-category split), put the two-category split in `q` / `ytd` /
    `fy` and the assessments in `q_metrics` / `ytd_metrics` / `fy_metrics` with the same structure.
  - Rebates and incentives are recorded with the sign shown (contra-revenue: negative).

## Self-checks (before writing each record; failures stay in `notes`)
- **Non-GAAP:** gaap.opex − Σ opex_pre = adj.opex; gaap.oth_inc + Σ oth_pre = adj.oth_inc; gaap.ni + Σ ni = adj.ni;
  gaap.eps_d + Σ eps = adj.eps_d (±0.02; "tables may not sum due to rounding").
- **Revenue categories:** Σ lines = net revenue (±1) for each column.

## Normalisation (`normalize.py`)
- Basis: as originally reported in each period's own release (prior-year restatements kept as `py` memo keys).
- Split restatement by document filing date; cash-flow discrete quarters from year to date; Q4 revenue categories = FY − 9M.
- Self-checks in `check_data.py`: statement arithmetic, bridges vs published, quarters vs years, cash and BS tie-outs, XBRL
  cross-checks (revenue, operating income, net income, diluted EPS, CFO, total assets).
