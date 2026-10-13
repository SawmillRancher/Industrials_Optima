# GE data extraction: schema and rules

Extraction for this kit is scripted (`extract.py`, using `tables.py`), not done by hand or by agents. This file documents what each `data/<period>.json` holds and the rules the scripts apply. It follows `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`, adapted to GE's documents.

## Sources
- **SEC EDGAR only**, CIK 0000040545 (General Electric Company, operating as GE Aerospace since 2-Apr-2024). The investor-relations site is blocked from the build environment; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$GE_SRC/txt` (`fetch.py` → `h2t.py`): one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/40545/<accession-no-dashes>/<doc>`. Each record lists its URLs in `sources`.
- **XBRL company facts:** `$GE_SRC/cf_40545.json`, used for the cross-check in `xbrl.py` (subset saved to `data/_xbrl.json`).
- **EDGAR requests:** a User-Agent is sent on every request, and requests are throttled (`make_index.py`, `fetch.py`).
- **Text quirks handled by `tables.py`:**
  - "( 177 )" and "(177)" are negative; "—" is zero.
  - Release rows carry the V% column only on totals, so a row has 4 tokens (3M current, 3M prior, YTD current, YTD prior) or 6 tokens (with V%). One Q3-25 row has a trailing 12-month cell (7 tokens).
  - Table-of-contents hits are skipped by requiring the next row to be a units row ("(In millions…)").

## Basis rules (period → document)
The basis is GE Aerospace continuing operations. GE HealthCare (spun 3-Jan-2023) and GE Vernova (spun 2-Apr-2024) are both in discontinued operations. Each period comes from the **first filing that presents it on that basis**.

| Period | Statements and segments (10-Q / 10-K) | Non-GAAP and orders (release) |
|---|---|---|
| FY2022 | FY2024 10-K, 2022 column | not published on this basis |
| FY2023 | FY2024 10-K, 2023 column | Q4-24 release, prior-year 12-month column |
| Q1-23 | Q2-24 10-Q: H1-23 − Q2-23 (derived) | Q2-24 release: H1-23 − Q2-23. Adjusted EPS $0.63 and continuing EPS $5.98 from the 11-Apr-2024 8-K Ex. 99.1 |
| Q2-23 / Q3-23 | Q2-24 / Q3-24 10-Q, prior-year 3M column | Q2-24 / Q3-24 release, prior-year 3M column |
| Q4-23 | FY2023 (FY2024 10-K) − 9M-23 (Q3-24 10-Q) | Q4-24 release, prior-year 3M column |
| Q1-24 | Q1-25 10-Q, prior-year column (the Q1-24 10-Q still consolidated GE Vernova) | Q1-25 release, prior-year column |
| Q2-24 onward | That quarter's 10-Q; Q4 = FY (10-K) − 9M (Q3 10-Q) | That quarter's release; Q4 from the Q4 release 3M column |

Other rules:
- **Balance sheets:** from 31-Dec-2023, the first GE Aerospace balance sheet (FY2024 10-K comparative). 31-Mar-2024 is not used because it still consolidated GE Vernova.
- **Cash flow:** year-to-date statements in `data/_cf_ytd.json`: H1-23, 9M-23, FY2022–25, then every 2024–26 YTD. Q1-23 and Q2-23 cash flows are not available on this basis (only H1-23 was re-presented).
- **Segments:** CES / DPT as reported in each period. The Jan-2026 recast (Aeroderivative CES → DPT; T&O site revenue and cost from Corporate & Other to the segments) has two sources:
  - Q1-25 and Q2-25 recast are taken from the 2026 10-Q prior-year columns (`seg_rc`, `ng_rc`).
  - FY2025 revised ($bn, unaudited estimates, Q4-25 release guidance table) is in `manual_items.json`.
- **Units and signs:**
  - USD millions as published; shares in millions; per-share as published.
  - Costs positive. The tax provision is stored positive as an expense. Non-operating benefit cost (income) is kept as published (income negative).
  - Cash flow as presented.
- **Never estimate.** Derived values (H1 − Q2, FY − 9M, 4 × FY − ΣQ1–Q3 for Q4 shares) are stated in `notes` or in the normalisation log.

## Record layout (`data/<period>.json`)
```json
{
  "period": "Q2-26", "sources": ["https://www.sec.gov/Archives/edgar/data/40545/..."], "notes": [],
  "is":  {"rev_eq", "rev_sv", "rev_ins", "rev", "cogs_eq", "cogs_sv", "sga", "sep", "gw_imp", "debt_ext", "rd", "int", "ins_cost",
          "nonop", "tcost", "oth", "ebt", "tax", "ni_cont", "disc", "ni", "nci", "ni_co", "pref", "ni_common", "nci_cont",
          "ni_cont_common", "eps_cont_d", "eps_cont_b", "eps_d", "eps_b", "sh_d", "sh_b", "ni_cc_eps"},
  "seg": {"ces_eq", "ces_sv", "ces", "ces_op", "ds", "pat", "dpt", "dpt_eq", "dpt_sv", "dpt_op",
          "u_ce", "u_leap", "u_isv", "u_def", "rpo_tot", "rpo_ces", "rpo_dpt",
          "c_ins_rev", "c_elim", "c_rev", "c_g_biz", "c_g_eq", "c_restr", "c_sep", "c_ins_op", "c_te_op", "c_imp", "c_ru",
          "c_op_gaap", "c_adj", "c_costs", "c_elim_op"},
  "seg_rc": {"... Jan-2026 structure (Q1-25 / Q2-25 only)"},
  "ng":  {"op_*": "operating-profit reconciliation rows", "c_*": "adjusted Corporate & Other",
          "ae_*": "adjusted earnings / net income bridge (pre-tax and tax per item, start, adjusted, EPS)",
          "fcf_*": "free cash flow bridge", "ord_ces", "ord_dpt", "r_ces", "r_dpt", "r_ces_op", "r_dpt_op", "eps_cont"},
  "bs":  {"cash", "inv_sec_cur", "ar", "inv", "ca_ctr", "oca", "hfs_a", "tca", "inv_sec", "ppe", "gw", "intang", "ctr_def", "oa", "dta",
          "disc_a", "ta", "std", "ap", "prog", "ctr_liab", "sda", "ocl", "hfs_l", "tcl", "def_inc", "ltd", "ins_liab", "comp", "ol",
          "disc_l", "tl", "aoci", "oc", "re", "treas", "eq", "nci", "te", "tle", "shares_out"}
}
```

## Adjusting-item categories (company labels)
| Model row | Company label |
|---|---|
| Insurance | Insurance earnings / net income (pre-tax), tax effect |
| U.S. tax equity | U.S. tax equity earnings / net income (pre-tax), tax effect (shown from the Q2-24 release, with 2023 comparatives) |
| Non-operating benefit | Non-operating benefit (cost) income (pre-tax), tax effect |
| Gains | Gains (losses) on purchases and sales of business interests; gains (losses) on retained and sold ownership interests and other equity securities |
| Restructuring | Restructuring & other (pre-tax), tax effect |
| Separation | Separation costs (pre-tax), tax effect |
| Other | Goodwill impairments (Q3-24); Russia and Ukraine charges (2022–23); excise tax and accretion of preferred share redemption (2023) |

## Self-checks (`check_data.py`, 630 checks; all pass)
- **Statements:**
  - revenue lines = total revenue;
  - cost lines = total costs;
  - revenue − costs + other income = profit before tax;
  - less tax = continuing net income;
  - plus discontinued operations = net income.
- **Segments:**
  - CES + DPT + Corporate & Other revenue = total revenue;
  - equipment + services = CES; D&S + P&AT = DPT;
  - segment profit + Corporate & Other − interest + non-operating benefit income − debt extinguishment = profit before tax − NCI;
  - Corporate & Other GAAP − items = adjusted Corporate & Other.
- **Non-GAAP:**
  - operating-profit bridge vs published (±3);
  - segment build vs published operating profit (±2);
  - adjusted-earnings bridge vs published (±4);
  - adjusted EPS (±0.01);
  - FCF bridge vs published (±2), with CFOA and capex tied to the cash-flow statement.
- **EPS:** NI to common ÷ diluted shares = continuing EPS (±0.01; ±0.03 where Q4 shares are derived).
- **Cash and balance sheet:**
  - beginning + change = ending cash (±2 in derived quarters);
  - ending − discontinued cash = continuing cash;
  - TA = TL&E.
- **Quarters vs years:** Σ quarters = FY for 2023–25 (±3; adjusted net income ±4). Documented exemption: FY2025 FCF, because the definition changed in the Q3-25 release.
- **XBRL cross-check** (`xbrl.py`, 88 facts compared, accession-matched): revenue, profit before tax, continuing net income (GE tags it after NCI), continuing diluted EPS, continuing CFO, total assets and diluted shares. All match.
