"""Loads the SEC-extracted Teledyne data (models/data/tdy/*.json) into a flat period → key map."""
from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data", "tdy")

SEGS = ["di", "inst", "ade", "es"]

# Adjusting-item categories, in bridge order. (key, label, in OI bridge?, in NI bridge?)
CATS = [
    ("AMORT", "Acquired intangible asset amortization", True, True),
    ("ACQ", "Acquisition-related transaction and integration costs (FLIR, Excelitas A&D, other)", True, True),
    ("STEPUP", "Inventory step-up / purchase-accounting adjustments", True, True),
    ("RESTR", "Restructuring / severance / facility consolidation charges", True, True),
    ("IMPAIR", "Impairment / asset write-downs", True, True),
    ("GAIN", "(Gain) loss on sale of businesses / assets", True, True),
    ("LEGAL", "Litigation / legal settlements", True, True),
    ("PENSION", "Pension expense (excluded in 2005–06 'pro forma' EPS)", True, True),
    ("SBC", "Stock option expense (excluded in 2005–06 'pro forma' EPS)", True, True),
    ("DEBT", "Debt extinguishment / acquisition financing costs", True, True),
    ("OTHER", "Other adjusting items (company-defined — see cell comments)", True, True),
    ("ROUND", "Per-share rounding (company reconciled in per-share amounts only; $m = EPS × diluted shares)", False,
     True),
    ("BASIS", "Basis difference: company bridge starts from OI as originally reported (pre-ASU 2017-07 recast)", True,
     False),
]
POST_CATS = ["TAX", "TAXD", "NCI"]


def load_files(data_dir=DATA_DIR):
    files = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    raw = [json.load(open(f)) for f in files]
    return files, raw


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def flatten(files, raw):
    P = defaultdict(dict)
    item_labels = defaultdict(lambda: defaultdict(list))
    notes, supp, outlook, conflicts = [], {}, {}, []
    pending, pending_pub = [], []
    for f, d in zip(files, raw):
        base = os.path.basename(f)
        notes += [f"[{base}] {n}" for n in d.get("notes", []) if isinstance(n, str)]
        if isinstance(d.get("supplemental"), dict):
            supp.update(d["supplemental"])
        if isinstance(d.get("outlook"), dict):
            outlook = d["outlook"]
        for per, v in d.get("periods", {}).items():
            tgt = P[per]

            def put(k, val, tgt=tgt, per=per):
                if not _num(val):
                    return
                if k in tgt and abs(tgt[k] - val) > 0.051:
                    conflicts.append((per, k, tgt[k], val, base))
                tgt[k] = val
            for blk in ("is", "ops", "bs", "cf", "seg"):
                for k, val in (v.get(blk) or {}).items():
                    put(f"{blk}.{k}", val)
            # segment-level non-GAAP items → per-segment sums
            seg = v.get("seg") or {}
            sums = defaultdict(float)
            for it in seg.get("seg_items", []) or []:
                if isinstance(it, dict) and _num(it.get("value")) and it.get("seg") in SEGS + ["corp"]:
                    sums[it["seg"]] += it["value"]
                    item_labels[per][f"segitems.{it['seg']}"].append(f"{it.get('label')}: {it['value']:,.1f}")
            for s, val in sums.items():
                tgt[f"seg.items_{s}"] = round(val, 4)
            for blk, pre in (("adj_oi", "adjO"), ("adj_ni", "adjN")):
                a = v.get(blk) or {}
                if not a:
                    continue
                for k in ("adj_oi_published", "adj_om_published", "oi_gaap", "adj_ni_published", "adj_eps_published"):
                    if k in a:
                        put(f"{pre}.{k}", a[k])
                sums = defaultdict(float)
                shd = None          # per-share items are converted after all files are loaded
                per_share = False
                for it in a.get("items", []) or []:
                    if not isinstance(it, dict):
                        continue
                    cat = it.get("cat", "OTHER")
                    cat = cat if cat in {c[0] for c in CATS} | set(POST_CATS) else "OTHER"
                    val = it.get("value")
                    if not _num(val):
                        eps = it.get("value_eps") if _num(it.get("value_eps")) else (
                            it.get("memo_eps") if cat == "TAX" and _num(it.get("memo_eps")) else None)
                        if eps is not None:
                            pending.append((per, pre, cat, eps, f"{it.get('label')}: ${eps:.2f}/sh"))
                        continue
                    sums[cat] += val
                    item_labels[per][f"{pre}.{cat}"].append(f"{it.get('label')}: {val:,.1f}")
                for cat, val in sums.items():
                    tgt[f"{pre}.{cat}"] = round(val, 4)
                if pre == "adjN" and a.get("adj_ni_published") is None and _num(a.get("adj_eps_published")):
                    pending_pub.append((per, a["adj_eps_published"]))
                if a.get("base"):
                    tgt[f"{pre}._base"] = a["base"]
    # historical acquired-intangible amortization by year (latest 10-K presenting each year) — annual periods
    hist_am = (supp.get("amort_schedule") or {}).get("historical") or {}
    if isinstance(hist_am, dict):
        for y, val in hist_am.items():
            if _num(val) and str(y) in P:
                P[str(y)]["is.amort_intangibles"] = val
    # per-share-only reconciliations (2006–07, Q4/16–2017): convert at weighted diluted shares
    ps_periods = set()
    for per, pre, cat, eps, lab in pending:
        shd = P[per].get("is.shares_diluted")
        if _num(shd):
            k = f"{pre}.{cat}"
            P[per][k] = round(P[per].get(k, 0.0) + eps * shd, 4)
            item_labels[per][k].append(lab + f" × {shd:.1f}m diluted shares")
            ps_periods.add(per)
    for per, eps in pending_pub:
        shd = P[per].get("is.shares_diluted")
        if _num(shd):
            P[per]["adjN.adj_ni_published"] = round(eps * shd, 4)
            item_labels[per]["adjN._per_share"].append(f"Published non-GAAP EPS ${eps:.2f} × {shd:.1f}m diluted "
                                                      f"shares (no $m figure published)")
            ps_periods.add(per)
    for per in ps_periods:
        t = P[per]
        ni = t.get("is.ni_teledyne")
        if not _num(ni) or not _num(t.get("adjN.adj_ni_published")):
            continue
        items = sum(v for k, v in t.items() if k.startswith("adjN.") and k[5:] not in
                    ("adj_ni_published", "adj_eps_published", "_base") and _num(v))
        resid = t["adjN.adj_ni_published"] - ni - items
        if abs(resid) > 0.05:
            t["adjN.ROUND"] = round(resid, 4)
            item_labels[per]["adjN.ROUND"].append(f"Per-share rounding residual {resid:,.1f}")
    for per, t in P.items():
        # gain (loss) on debt extinguishment shown as a separate non-operating line in 2021–23 → other income
        g = t.get("is.gain_debt_ext")
        if _num(g) and all(_num(t.get(k)) for k in ("is.op_income", "is.interest_exp_net", "is.pretax")):
            base = (t["is.op_income"] - t["is.interest_exp_net"] + t.get("is.non_service_pension", 0)
                    + t.get("is.other_income", 0))
            if abs(base - t["is.pretax"]) > 0.05 and abs(base + g - t["is.pretax"]) < 0.06:
                t["is.other_income"] = round(t.get("is.other_income", 0) + g, 4)
        # non-GAAP corporate expense: positive = expense (files differ in sign convention)
        if _num(t.get("seg.adj_corp")):
            t["seg.adj_corp"] = abs(t["seg.adj_corp"])
        # company OI bridge on a different GAAP basis (2017: pre-ASU 2017-07) → explicit basis-difference item
        og, oi = t.get("adjO.oi_gaap"), t.get("is.op_income")
        if _num(og) and _num(oi) and abs(og - oi) > 0.05:
            t["adjO.BASIS"] = round(og - oi, 4)
            item_labels[per]["adjO.BASIS"].append(f"Company bridge starts from OI as originally reported {og:,.1f} "
                                                  f"vs recast {oi:,.1f}")
    for per, t in P.items():
        # 2021: cash-flow D&A includes the FLIR inventory step-up (an adjusting item) — use D&A ex step-up on the IS
        if _num(t.get("is.da_ex_stepup")):
            t["is.da_cf"] = t.get("is.da")
            t["is.da"] = t["is.da_ex_stepup"]
        # 2024+: acquired-intangible amortization presented as a separate IS line (extracted inside other_op)
        am, oo = t.get("is.amort_intangibles"), t.get("is.other_op")
        if _num(am) and _num(oo) and am > 0 and oo <= -0.95 * am:
            t["is.amort_line"] = am
            t["is.other_op"] = round(oo + am, 4)
        if t.get("bs.total_assets") is not None:
            t["bs.total_assets_rep"] = t["bs.total_assets"]
        if t.get("is.net_income") is not None:
            t["is.ni_rep"] = t["is.net_income"]
        # total debt
        if t.get("bs.ltd") is not None:
            t["bs.total_debt"] = round(t.get("bs.current_ltd", 0) + t["bs.ltd"], 4)
        # folded BS lines
        def combo(newk, parts):
            vals = [t[p] for p in parts if _num(t.get(p))]
            if vals:
                t[newk] = round(sum(vals), 4)
        combo("bs.oca_plus", ["bs.prepaid_other_ca", "bs.held_for_sale", "bs.dta_current"])
        combo("bs.onca_plus", ["bs.other_assets", "bs.prepaid_pension", "bs.dta"])
        combo("bs.ocl_plus", ["bs.held_for_sale_liab"])
        combo("bs.oncl_plus", ["bs.other_ncl", "bs.redeemable_nci_liab"])
        combo("bs.sc_apic", ["bs.common_stock", "bs.apic"])
        combo("cf.debt_net", ["cf.debt_issued", "cf.st_debt_net"])
        combo("cf.other_fin_plus", ["cf.other_fin", "cf.debt_issue_costs", "cf.tax_benefit_sbc", "cf.dividends"])
        combo("cf.other_inv_plus", ["cf.other_investing"])
        combo("cf.pension_plus", ["cf.pension_cf", "cf.pension_contrib"])
        combo("cf.other_nc_plus", ["cf.other_noncash", "cf.disc_ops_cf", "cf.gain_disp"])
        if t.get("cf.da") is None and _num(t.get("cf.depreciation")) and _num(t.get("cf.amortization")):
            t["cf.da"] = round(t["cf.depreciation"] + t["cf.amortization"], 4)
        if t.get("is.da") is None and _num(t.get("cf.da")):
            t["is.da"] = t["cf.da"]
    return P, item_labels, notes, supp, outlook, conflicts


def load(data_dir=DATA_DIR):
    files, raw = load_files(data_dir)
    return flatten(files, raw)
