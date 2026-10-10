"""Loads the Hermès data extracted from the company's filings (models/data/rms/*.json) into a flat period → key map.

Source documents (finance.hermes.com): registration documents / Universal Registration Documents (annual financial
report, FY2010–FY2025; FY2006–09 key figures and comparatives from the 2010 document), half-year financial reports
(H1 2013–H1 2026) and quarterly revenue releases (Q1 2014–Q2 2026). Hermès International is not an SEC registrant
(only an unsponsored ADR exists on EDGAR), so the IR-site documents are the primary filings (they are the documents
filed with the AMF).
"""
from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data", "rms")

SECTORS = ["leather", "rtw", "silk", "other_hermes", "perfume", "watches", "other_products"]
AREAS = ["france", "europe", "japan", "apac", "americas", "other"]
BLOCKS = ("is", "memo", "sector", "geo", "bs", "cf", "apm")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load(data_dir=DATA_DIR):
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    P = defaultdict(dict)
    notes, conflicts, texts = [], [], defaultdict(dict)
    for f in files:
        d = json.load(open(f))
        base = os.path.basename(f)
        notes += [f"[{base}] {n}" for n in d.get("notes", []) if isinstance(n, str)]
        for per, v in d.get("periods", {}).items():
            if not isinstance(v, dict):
                continue
            # quarterly revenue → half-year columns (first / second quarter of the half)
            if per.startswith("Q") and "/" in per:
                q = int(per[1])
                yy = per.split("/")[1]
                half = f"H1/{yy}" if q <= 2 else f"H2/{yy}"
                slot = "qa" if q in (1, 3) else "qb"
                qd = v.get("q") or {}
                for k in ("revenue", "cc_growth", "cur_growth"):
                    if _num(qd.get(k)):
                        P[half][f"{slot}.{k}"] = qd[k]
                continue
            tgt = P[per]
            for blk in BLOCKS:
                for k, val in (v.get(blk) or {}).items():
                    key = f"{blk}.{k}"
                    if _num(val):
                        if key in tgt and abs(tgt[key] - val) > 0.051:
                            conflicts.append((per, key, tgt[key], val, base))
                        tgt[key] = val
                    elif isinstance(val, str) and val.strip():
                        texts[per][key] = val
    for f in files:   # raw cf_other lines needed for the D&A normalisation
        for per, v in json.load(open(f)).get("periods", {}).items():
            if isinstance(v, dict) and isinstance(v.get("cf_other"), dict):
                P[per]["_cf_other"] = v["cf_other"]
    normalise(P)
    for v in P.values():
        v.pop("_cf_other", None)
    return dict(P), notes, conflicts, texts


# Company-disclosed one-off tax items treated as non-recurring in the adjusted-net-income bridge (EURm, expense +).
# Hermès itself restates net income for the 2025–26 French exceptional contribution on large companies' profits.
EXCEP_TAX = {
    "2017": (20.0, "2017 URD tax note: two exceptional 15% French corporate-tax surtaxes, net of the refund of the 3% "
                   "tax on dividends (struck down Oct-2017) — net expense €20m."),
    "2025": (331.0, "2025 URD: exceptional contribution on the profits of large companies in France €331m (ETR 33.4%; "
                    "28.5% excluding it). Net income attributable excluding it: €4.86bn."),
    "H1/25": (257.0, "Estimate: (reported ETR 35.4% − ETR excluding the contribution 28.0%, H1/25 report) × pre-tax "
                     "income €3,475m. Hermès gives net income excluding it of '€2.5bn' (31.2% of sales)."),
    "H1/26": (255.0, "Estimate: (reported ETR 35.4% − ETR excluding the contribution 28.0%, H1/26 report) × pre-tax "
                     "income €3,441m. Hermès gives net income excluding it of '€2.5bn' (30.7% of sales); contribution "
                     "renewed for 2026."),
}
# Tax on non-recurring items (EURm, expense +). 2018 Hong Kong property gain and 2020 Shang Xia deconsolidation gain
# were not taxed (URD tax-rate commentary); 2006–07 items are not described (period ETR applied in the bridge).
NONREC_TAX = {"2018": 0.0, "H1/18": 0.0, "2020": 0.0}


def _cfo(v, needle):
    for k, val in (v.get("_cf_other") or {}).items():
        if needle in k.lower() and _num(val):
            return val
    return None


def normalise(P):
    for per, v in P.items():
        # Tableware was shown separately up to H1/13; the model folds it into "Other Hermès sectors" (current basis)
        if "sector.other_hermes" in v or "sector.tableware" in v:
            v["sector.other_hermes_c"] = v.get("sector.other_hermes", 0) + v.get("sector.tableware", 0)
        if "sector.cc_other_hermes" in v and "sector.tableware" in v and "sector.cc_tableware" in v:
            oh, tw = v.get("sector.other_hermes", 0), v.get("sector.tableware", 0)
            v["sector.cc_other_hermes_c"] = ((oh * v["sector.cc_other_hermes"] / (1 + v["sector.cc_other_hermes"])
                                              + tw * v["sector.cc_tableware"] / (1 + v["sector.cc_tableware"]))
                                             / (oh / (1 + v["sector.cc_other_hermes"])
                                                + tw / (1 + v["sector.cc_tableware"])))
        elif "sector.cc_other_hermes" in v:
            v["sector.cc_other_hermes_c"] = v["sector.cc_other_hermes"]
        # ---- D&A: total depreciation, amortisation & impairment incl. right-of-use assets (CF statement basis)
        fixed = _cfo(v, "depreciation and amortisation of fixed")
        rou = _cfo(v, "right-of-use")
        imp = _cfo(v, "impairment")
        da_cf = v.get("cf.da", v.get("memo.da_cf"))
        if fixed is not None or rou is not None or (imp is not None and da_cf is not None):
            tot = (fixed if fixed is not None else (da_cf or 0)) + (rou or 0) + (imp or 0)
        elif da_cf is not None and v.get("memo.da_rou") is not None:
            tot = da_cf     # combined line (2023+, H1/23+)
        elif da_cf is None and v.get("memo.da_fixed") is not None and v.get("memo.da_rou") is not None:
            tot = v["memo.da_fixed"] + v["memo.da_rou"] + abs(v.get("memo.impairment") or 0)   # H1/19–H1/22
        elif da_cf is not None:
            tot = da_cf + abs(v.get("memo.impairment") or 0)   # separate impairment line (2009–13, H1/13–18)
        else:
            tot = None
        if tot is not None:
            v["n.da_total"] = round(tot, 4)
        r = v.get("memo.da_rou") if v.get("memo.da_rou") is not None else rou
        if r is not None:
            v["n.da_rou"] = r
        # ---- capex: CF line from 2018; before, intangibles + PP&E purchases (= operating investments, key figures)
        if v.get("cf.capex") is not None:
            v["n.capex"] = v["cf.capex"]
        elif v.get("apm.operating_investments") is not None:
            v["n.capex"] = -abs(v["apm.operating_investments"])
        # ---- equity split & provisions / borrowings aggregates
        if v.get("bs.equity_parent") is None and v.get("bs.total_equity") is not None:
            v["bs.equity_parent"] = round(v["bs.total_equity"] - (v.get("bs.nci_eq") or 0), 4)
        if v.get("bs.share_capital") is not None:
            v["n.sc_sp"] = v["bs.share_capital"] + (v.get("bs.share_premium") or 0)
            if v.get("bs.equity_parent") is not None:
                v["n.reserves"] = round(v["bs.equity_parent"] - v["n.sc_sp"] - (v.get("bs.treasury_eq") or 0), 4)
        if v.get("bs.lt_borrowings") is not None or v.get("bs.st_borrowings") is not None:
            v["n.borrowings"] = (v.get("bs.lt_borrowings") or 0) + (v.get("bs.st_borrowings") or 0)
        if v.get("bs.total_assets") is not None:
            v["n.prov"] = sum(v.get(f"bs.{k}") or 0 for k in ("nc_prov", "nc_emp", "cur_prov", "cur_emp"))
            v["n.lease_lt"] = v.get("bs.lt_lease") or 0
            v["n.lease_st"] = v.get("bs.st_lease") or 0
        # 2006–08 key figures: non-recurring items = operating income − recurring operating income (not described)
        if v.get("is.nonrec") is None and v.get("is.op_inc") is not None and v.get("is.roi") is not None:
            v["is.nonrec"] = round(v["is.op_inc"] - v["is.roi"], 4)
        # bank overdrafts are printed in parentheses in the net-cash reconciliation; the model deducts a positive amount
        if v.get("apm.bank_overdrafts") is not None:
            v["apm.bank_overdrafts"] = abs(v["apm.bank_overdrafts"])
        # ---- one-off tax items
        if per in EXCEP_TAX:
            v["n.excep_tax"] = EXCEP_TAX[per][0]
        if per in NONREC_TAX:
            v["n.nonrec_tax"] = NONREC_TAX[per]
        if v.get("memo.ni_excl_excep") is None and per == "2025":
            v["memo.ni_excl_excep"] = 4860.0
        # dividends: total DPS in respect of the year (ordinary)
        if v.get("memo.shares_issued") is not None and v.get("memo.treasury_shares") is not None:
            v["n.shares_out"] = round(v["memo.shares_issued"] - v["memo.treasury_shares"], 6)
