# TLN data extraction: schema and rules

Written from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. Extraction is scripted (`extract.py`), not split across agents, because Talen's filing history is short (one S-1, two 10-Ks, eight 10-Qs).

## Sources
- **SEC EDGAR only** (CIK 1622536, Talen Energy Corporation). Predecessor Talen Energy Supply, LLC (CIK 1161976) stopped filing in 2016; its 2021–23 figures come from the S-1. The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$TLN_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1622536/<accession-no-dashes>/<doc>`. URLs are recorded in `sources`.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative; 10-Q cells read "( 27 )".
  - "—" means zero; "N/A" (Predecessor per-share data) is null.
- **Cross-check:** `$TLN_SRC/cf_1622536.json` (XBRL company facts), via `xbrl_check.py`.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **As originally reported:** documents are read in filing order and the first one that presents a period wins.
- **Raw tags** (one JSON per tag in `data/`):
  - fiscal years `2021` … `2025`; quarters `Q1-23` … `Q3-26`; year-to-date `H1-24`, `9M-24`, …;
  - partial 2023 periods around Emergence (17-May-2023): `P23` (1-Jan to 17-May, Predecessor), `S23` (18-May to 31-Dec, Successor), `P23b` (1-Apr to 17-May), `S23a` (18-May to 30-Jun), `S23c` (18-May to 30-Sep);
  - `P23x` / `S23x`: the same two periods as re-presented in the Q4-24 release (used for the Adjusted Free Cash Flow items only);
  - `Q4-24`, `Q4-25`: non-GAAP three-month columns of the Q4-25 release (only `Q4-25` is used).
- **Income statement:** three-month columns of the 10-Q / S-1; annual from the 10-K / S-1. There is no three-month Q4 statement: Q4 = FY − 9M (in `normalize.py`, noted).
- **Balance sheet:** the period-end statement. Derivative lines are stored as `der_ca`, `der_nca`, `der_cl`, `der_ncl`.
- **Cash flow:** the year-to-date statement under the YTD tag; discrete quarters are derived in `normalize.py`.
- **Units:** USD millions as published; weighted shares in millions (published in thousands); per-share as published.
- **Signs:** costs positive; gains / income items signed by their effect on income; cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = key omitted. **Never estimate.** Every derived value is noted in `normalize.py` and in a cell comment.

## Record
```json
{
  "is":  {"cap_rev": 0, "en_rev": 0, "unr_rev": 0, "rev": 0, "fuel": 0, "nfa": 0, "unr_exp": 0, "en_exp": 0, "om": 0, "ga": 0, "ga_sbc": 0,
          "dda": 0, "impair": 0, "restr_op": 0, "oth_op": 0, "oi": 0, "ndt": 0, "int": 0, "reorg": 0, "consol": 0, "gain_sale": 0,
          "oth_nonop": 0, "ebt": 0, "tax": 0, "ni_tot": 0, "nci": 0, "ni": 0, "eps_b": 0, "eps_d": 0, "sh_b": 0, "sh_d": 0},
  "bs":  {"cash": 0, "rcash": 0, "ar": 0, "inv": 0, "der_ca": 0, "oca": 0, "ahs": 0, "tca": 0, "ppe": 0, "ndt": 0, "der_nca": 0, "onca": 0, "ta": 0,
          "rcf": 0, "cpltd": 0, "accint": 0, "ap": 0, "der_cl": 0, "sbc_liab": 0, "ocl": 0, "lhs": 0, "tcl": 0, "ltd": 0, "lstc": 0, "der_ncl": 0,
          "pension": 0, "aro": 0, "dtl": 0, "acl": 0, "oncl": 0, "tl": 0, "apic": 0, "re": 0, "aoci": 0, "member": 0, "eq": 0, "nci": 0, "teq": 0, "tle": 0},
  "cf":  {"ni": 0, "unr": 0, "dda": 0, "nfa": 0, "ndt": 0, "def": 0, "sbc": 0, "gain": 0, "impair": 0, "restr": 0, "reorg": 0, "collat": 0, "sbc_cash": 0,
          "cfo": 0, "capex": 0, "nfuel": 0, "ndt_inv": 0, "acq": 0, "proceeds": 0, "cfi": 0, "bb": 0, "nci_rep": 0, "warr": 0, "sbc_fin": 0, "cff": 0,
          "net": 0, "beg": 0, "end": 0},
  "ng":  {"ni": 0, "int": 0, "tax": 0, "dda": 0, "nfa": 0, "MTM": 0, "NDT": 0, "SBC": 0, "GAIN": 0, "IMPAIR": 0, "RESTR": 0, "ACQ": 0, "OTHER": 0,
          "<CAT>_lab": "company wording and amounts of the lines grouped into the category", "adj_ebitda": 0,
          "f_capex": 0, "f_int": 0, "f_tax": 0, "f_pension": 0, "adj_fcf": 0},
  "seg": {"pjm": 0, "other": 0, "corp": 0, "nci": 0, "other_items": 0},
  "ops": {"gen_twh": 0, "carbon_free": 0, "cap_factor": 0},
  "sources": ["is: <url>", "ng: <url>"], "notes": []
}
```

## Non-GAAP categories
The company's reconciliation lines are mapped to categories by label (`NG_CAT` in `extract.py`); an unmapped label stops the run.
| Category | Company lines |
|---|---|
| MTM | Unrealized (gain) loss on commodity derivative contracts |
| NDT | Nuclear decommissioning trust funds (gain) loss, net |
| SBC | Stock-based compensation expense; long-term incentive compensation expense |
| GAIN | (Gain) loss on (non-core) asset sales, net |
| IMPAIR | Non-cash impairments; inventory net realizable value, obsolescence and other charges; environmental and ARO revisions |
| RESTR | Reorganization (gain) loss; hedge termination losses; operational and other restructuring; liability management costs; consolidation of subsidiary |
| ACQ | Acquisition and divestiture activities |
| OTHER | Legal settlements; unusual market events; net periodic defined benefit cost; development expenses; Cumulus Digital / noncontrolling interest; other |

## Self-checks (`check_data.py`, 396 checks)
- Revenues = energy + capacity + unrealized; energy expenses = fuel + nuclear fuel amortization − unrealized.
- Operating income, pre-tax income, net income and net income attributable (±0.6).
- Diluted EPS = net income attributable ÷ diluted shares (±0.015), quarters only.
- Bridge start = net income; bridge tax and nuclear fuel amortization = income statement.
- Net income + interest + tax + D&A + nuclear fuel amortization + Σ items = published Adjusted EBITDA (±0.6; ±1.6 on combined 2023 periods).
- Adjusted EBITDA − capex − interest − taxes − pension = published Adjusted Free Cash Flow (±1.6).
- CFO + CFI + CFF = Δcash; beginning + Δ = ending; cash-flow ending cash = balance-sheet cash + restricted cash.
- Total assets = total liabilities + equity; model asset and liability lines sum to the reported totals.
- Σ Q1–Q4 = FY for revenues, operating income, net income, Adjusted EBITDA, Adjusted FCF, CFO, capex, PJM segment Adjusted EBITDA and generation.
