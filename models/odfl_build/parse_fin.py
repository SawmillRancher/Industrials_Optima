"""Parse the balance sheet and statement of cash flows of an ODFL 10-Q / 10-K (h2t text).
Rows are captured as (label, current-period value) — ODFL presents the current period in the first column —
then classified into the extraction schema; residual 'other' lines keep every section summing to its subtotal."""
import re
from parse_release import numbers, _cells

def _rows(lines, i0, stop_rx, max_n=160):
    out = []
    for l in lines[i0:i0 + max_n]:
        if '|' not in l: continue
        lab = _cells(l)[0]
        n = numbers(l)
        if n: out.append((lab, n[0]))
        if re.match(stop_rx, lab, re.I): break
    return out

def find_bs(lines):
    for i, l in enumerate(lines):
        if re.match(r'(?i)^cash and (cash )?equivalents\s*\|', l):
            # require 'Total assets' within the next 40 rows (skip TOC / MD&A mentions)
            if any(re.match(r'(?i)^total current assets\s*\|', x) for x in lines[i:i + 20]) and any(re.match(r'(?i)^total assets\s*\|', x) for x in lines[i:i + 60]):
                return _rows(lines, i, r"^total liabilities and (shareholders|stockholders)|^total liabilities & ")
    return None

def find_cf(lines):
    for i, l in enumerate(lines):
        if re.match(r'(?i)^net income\s*\|', l):
            nxt = ' '.join(lines[i:i + 8]).lower()
            if 'depreciation' in nxt and any(re.match(r'(?i)^net cash (provided by|used in|\(used in\))? ?(operating|provided by operating)', x) or
                                             re.match(r'(?i)^net cash provided by operating', x) for x in lines[i:i + 40]):
                return _rows(lines, i, r"^cash and (cash )?equivalents(, (and )?restricted cash)?,? (at )?end|^cash.*end of (period|year)")
    return None

def _m(rx, lab): return re.match(rx, lab.strip(), re.I) is not None

def classify_bs(rows):
    b, raw = {}, [[a, v] for a, v in rows]
    sec = 'ca'
    for lab, v in rows:
        L = lab.lower().strip()
        if _m(r'^total current assets', L): b['total_current_assets'] = v; sec = 'nca'; continue
        if _m(r'^total assets', L): b['total_assets'] = v; sec = 'cl'; continue
        if _m(r'^total current liabilities', L): b['total_current_liab'] = v; sec = 'ncl'; continue
        if _m(r'^total long-term liabilities', L): b['total_ncl'] = v; continue
        if _m(r'^total liabilities and|^total liabilities &', L): b['total_le'] = v; continue
        if _m(r'^total liabilities', L): b['total_liabilities'] = v; sec = 'eq'; continue
        if _m(r"^total (shareholders|stockholders)", L): b['total_equity'] = v; continue
        if sec == 'ca':
            if _m(r'^cash and', L): b['cash'] = v
            elif _m(r'^short-term investments', L): b['sti'] = v
            elif _m(r'^customer receivables', L): b['receivables'] = v
            elif _m(r'^other receivables', L): b['other_rec'] = v
        elif sec == 'nca':
            if _m(r'^revenue equipment', L): b['ppe_rev_equip'] = v
            elif _m(r'^land and structures', L): b['ppe_land'] = v
            elif _m(r'^other fixed assets', L): b['ppe_other'] = v
            elif _m(r'^leasehold', L): b['ppe_lease'] = v
            elif _m(r'^total property and equipment', L): b['ppe_gross'] = v
            elif _m(r'^less accumulated', L): b['accum_dep'] = v
            elif _m(r'^net property', L): b['ppe'] = v
            elif _m(r'^goodwill', L): b['goodwill'] = b.get('goodwill', 0) + v
            elif _m(r'^(other )?intangible', L): b['intangibles'] = v
            elif _m(r'^operating lease right', L): b['rou'] = v
        elif sec == 'cl':
            if _m(r'^accounts payable', L): b['ap'] = v
            elif _m(r'^compensation and benefits', L): b['accrued_comp'] = v
            elif _m(r'^claims and insurance', L): b['claims_cur'] = v
            elif _m(r'^current maturities', L): b['current_debt'] = v
        elif sec == 'ncl':
            if _m(r'^long-term debt', L): b['ltd'] = v
            elif _m(r'^deferred income taxes', L): b['deferred_tax'] = v
        elif sec == 'eq':
            if _m(r'^common stock', L): b['common'] = v
            elif _m(r'^capital in excess', L): b['apic'] = v
            elif _m(r'^retained earnings', L): b['retained'] = v
    if b.get('accum_dep') is not None: b['accum_dep'] = -abs(b['accum_dep'])
    b['lines_raw'] = raw
    return b

def classify_cf(rows):
    c = {'lines_raw': [[a, v] for a, v in rows]}
    sec = 'op'
    acc = {k: 0.0 for k in ('wc_change', 'debt_proceeds', 'debt_repay', 'sti_net')}
    for lab, v in rows:
        L = lab.lower().strip()
        if _m(r'^net cash .*operating', L): c['cfo'] = v; sec = 'inv'; continue
        if _m(r'^net cash .*investing', L): c['cfi'] = v; sec = 'fin'; continue
        if _m(r'^net cash .*financing', L): c['cff'] = v; sec = 'tot'; continue
        if sec == 'op':
            if _m(r'^net income', L): c['net_income'] = v
            elif _m(r'^depreciation', L): c['dda'] = v
            elif re.search(r'(gain|loss).*(sale|disposal)s? of property', L): c['gain_loss'] = c.get('gain_loss', 0) + v
            elif _m(r'^deferred income tax', L): c['deferred_tax'] = v
            elif _m(r'^(stock|share)-based compensation', L): c['sbc'] = v
            elif _m(r'^(changes in (operating )?assets|customer and other receivables|.*receivable|prepaid|other assets|accounts payable|compensation|claims|'
                    r'other liabilities|other accrued|accrued|income taxes|deferred compensation)', L) and not _m(r'^other, net', L):
                acc['wc_change'] += v
        elif sec == 'inv':
            if _m(r'^(purchase of|purchases of|additions to) property', L): c['capex'] = v
            elif _m(r'^proceeds from (the )?sale of property', L): c['proceeds_disp'] = v
            elif _m(r'^(purchase|sale|proceeds|maturit).*short-term investments|short-term investment', L): acc['sti_net'] += v
            elif _m(r'^(acquisition|purchase of business|business acquisition)', L): c['acquisitions'] = c.get('acquisitions', 0) + v
        elif sec == 'fin':
            if re.search(r'repurchase', L): c['buyback'] = c.get('buyback', 0) + v
            elif re.search(r'dividend', L): c['dividends'] = c.get('dividends', 0) + v
            elif re.search(r'revolving|line of credit|credit agreement|credit facility', L):
                if v >= 0: acc['debt_proceeds'] += v
                else: acc['debt_repay'] += v
            elif _m(r'^proceeds from (issuance of )?(long-term debt|senior notes|notes|borrowing)', L): acc['debt_proceeds'] += v
            elif _m(r'^(principal )?(payments|repayment)s? (on|of|under) (long-term debt|senior notes|capital lease|notes|debt)|^principal payments', L):
                acc['debt_repay'] += v
        else:
            if re.search(r'(beginning|begin) of', L): c['cash_begin'] = v
            elif re.search(r'end of', L): c['cash_end'] = v
            elif re.search(r'increase|decrease|net change', L): c['net_change'] = v
    c.update(acc)
    return c

def parse(text):
    lines = [l.strip() for l in text.split('\n')]
    bs, cf = find_bs(lines), find_cf(lines)
    return (classify_bs(bs) if bs else None), (classify_cf(cf) if cf else None)
