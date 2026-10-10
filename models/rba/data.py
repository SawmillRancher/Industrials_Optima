"""Loads the SEC-extracted RB Global data (models/data/rba/*.json) into a flat period → key map."""
from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data", "rba")

# Adjusting-item categories, in bridge order. (key, label, appears in EBITDA bridge?, appears in NI bridge?)
CATS = [
    ("SBC", "Stock-based compensation expense (added back from Q1/23)", True, True),
    ("ACQ", "Acquisition-related and integration costs", True, True),
    ("RESTR", "Restructuring / management reorganization / severance", True, True),
    ("AMORT", "Amortization of acquired intangible assets (adj. NI only, from Q1/23)", False, True),
    ("DISP", "(Gain) loss on disposition of PP&E / excess property and related costs", True, True),
    ("IMPAIR", "Impairment losses (property, goodwill, customer relationships)", True, True),
    ("EXEC", "Executive transition / CEO separation costs", True, True),
    ("DIVEST", "(Gain) loss on divestiture / deconsolidation and related costs", True, True),
    ("DEBT", "Debt refinancing / extinguishment costs", True, True),
    ("LEGAL", "Other legal, advisory and non-income-tax expense", True, True),
    ("FV", "Change in fair value of derivatives / hedges", True, True),
    ("TERM", "Merger termination costs / fees (Euro Auctions)", True, True),
    ("PCV", "IAA prepaid consigned vehicle charges (purchase accounting, 2023–Q2/25)", True, True),
    ("REMEAS", "Remeasurements in connection with business combinations", True, True),
    ("ACCR", "Accretion of deferred acquisition consideration (adj. NI only, from Q3/25)", True, True),
    ("FXFIN", "Net foreign-exchange impact on financing transactions (2007–09)", True, True),
    ("OTHER", "Other adjusting items (company-defined — see cell comments)", True, True),
]
POST_CATS = ["TAX", "TAXD", "PREF", "RNCI"]
EBITDA_BUILD = {"D&A", "INT", "INTINC", "TAXEXP", "NI"}


def split_other(label: str) -> str:
    s = label.lower()
    if "prepaid consigned" in s:
        return "PCV"
    if "remeasure" in s:
        return "REMEAS"
    if "accretion" in s:
        return "ACCR"
    if "foreign exchange" in s and "financing" in s:
        return "FXFIN"
    return "OTHER"


def load_files(data_dir=DATA_DIR):
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    raw = [json.load(open(f)) for f in files]
    return files, raw


def flatten(files, raw):
    P = defaultdict(dict)
    item_labels = defaultdict(lambda: defaultdict(list))   # (period) -> key -> labels
    notes = []
    supp = {}
    conflicts = []
    for f, d in zip(files, raw):
        notes += [f"[{os.path.basename(f)}] {n}" for n in d.get("notes", [])]
        if "supplemental" in d:
            supp.update(d["supplemental"])
        for per, v in d.get("periods", {}).items():
            tgt = P[per]

            def put(k, val):
                if val is None or isinstance(val, (str, list, dict)):
                    return
                if k in tgt and abs(tgt[k] - val) > 0.051:
                    conflicts.append((per, k, tgt[k], val, os.path.basename(f)))
                tgt[k] = val
            for blk in ("is", "ops", "bs", "cf"):
                for k, val in v.get(blk, {}).items():
                    put(f"{blk}.{k}", val)
            # ASC 606 was adopted full-retrospectively: the company recast 2017 (quarters and FY) in its 2018
            # filings. Use the latest presentation (same rule as the HII model).
            if v.get("is_asc606"):
                for k in [k for k in tgt if k.startswith("is.")]:
                    del tgt[k]
                for k, val in v["is_asc606"].items():
                    put(f"is.{k}", val)
            ae = v.get("adj_ebitda", {})
            for k in ("ebitda_published", "adj_ebitda_published"):
                if k in ae:
                    put(f"adjE.{k}", ae[k])
            sums = defaultdict(float)
            for it in ae.get("items", []):
                cat = it["cat"]
                if cat in EBITDA_BUILD:
                    continue
                if cat == "OTHER":
                    cat = split_other(it["label"])
                sums[cat] += it["value"]
                item_labels[per][f"adjE.{cat}"].append(f"{it['label']}: {it['value']:,.1f}")
            for cat, val in sums.items():
                tgt[f"adjE.{cat}"] = round(val, 4)
            # interest income bundled in other income on the IS but split out in the company EBITDA bridge
            intinc = [it["value"] for it in ae.get("items", []) if it["cat"] == "INTINC"]
            if intinc and tgt.get("is.interest_income") is None and tgt.get("is.other_income") is not None:
                ii = -sum(intinc)
                tgt["is.interest_income"] = round(ii, 4)
                tgt["is.other_income"] = round(tgt["is.other_income"] - ii, 4)
            an = v.get("adj_ni", {})
            for k in ("adj_ni_published", "adj_eps_published"):
                if k in an:
                    put(f"adjN.{k}", an[k])
            sums = defaultdict(float)
            for it in an.get("items", []):
                cat = it["cat"]
                if cat == "OTHER":
                    cat = split_other(it["label"])
                sums[cat] += it["value"]
                item_labels[per][f"adjN.{cat}"].append(f"{it['label']}: {it['value']:,.1f}")
            for cat, val in sums.items():
                tgt[f"adjN.{cat}"] = round(val, 4)
            if an.get("base"):
                tgt["adjN._base"] = an["base"]
    # FY2006 'adjusted' EPS was stated pre-split ($1.61); 3-for-1 split Apr-2008 → $0.537
    if P.get("2006", {}).get("adjN.adj_eps_published") and P["2006"]["adjN.adj_eps_published"] > 1:
        P["2006"]["adjN.adj_eps_published"] = round(P["2006"]["adjN.adj_eps_published"] / 3, 3)
        notes.append("FY2006 adjusted EPS $1.61 (pre-split, FY2006 MD&A) restated ÷3 for the April-2008 3-for-1 split.")
    # derived / combined keys
    for per, t in P.items():
        def g(k):
            return t.get(k)

        def combo(newk, parts):
            vals = [t[p] for p in parts if t.get(p) is not None and not isinstance(t[p], str)]
            if vals:
                t[newk] = round(sum(vals), 4)
        # legacy presentation: all revenue was service revenue (commissions + fees; inventory gains netted)
        if g("is.service_rev") is None and g("is.total_rev") is not None and g("is.inv_sales_rev") is None:
            t["is.service_rev"] = t["is.total_rev"]
        # 2023+: keep only the current seller / buyer / marketplace-services split
        if g("is.seller_rev") is not None:
            for k in ("is.comm_rev", "is.fee_rev"):
                t.pop(k, None)
        combo("cf.impairment_plus", ["cf.impairment", "cf.loss_deconsol"])
        combo("cf.debt_issued_net_plus", ["cf.debt_issued", "cf.st_debt_net"])
        combo("cf.other_fin_plus", ["cf.other_fin", "cf.debt_issue_costs"])
        combo("bs.other_current_plus", ["bs.other_current", "bs.held_for_sale"])
        combo("bs.other_noncurrent_plus", ["bs.other_noncurrent", "bs.equity_investments"])
        combo("bs.other_cl_plus", ["bs.held_for_sale_liab", "bs.other_cl"])
        combo("bs.share_cap_apic", ["bs.share_capital", "bs.apic"])
        combo("bs.temp_rnci", ["bs.temp_rnci", "bs.temp_other"]) if g("bs.temp_other") else None
        if g("bs.total_assets") is not None:
            t["bs.total_assets_rep"] = t["bs.total_assets"]
    return P, item_labels, notes, supp, conflicts


def load(data_dir=DATA_DIR):
    files, raw = load_files(data_dir)
    return flatten(files, raw)
