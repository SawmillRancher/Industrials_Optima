"""Per-period extraction for UPS: one JSON per period in data/ (annual 2006-2025, quarters Q1-13 .. Q3-26).

Sources (SEC EDGAR only, CIK 1090727):
  * earnings release (8-K Item 2.02, Ex. 99.1 / 99.2): Selected Financial Data (segment revenue and operating profit, other income,
    tax, net income, EPS, shares, "as adjusted" / non-GAAP adjusted data), Selected Operating Data (revenue by product, operating
    days, average daily volume and revenue per piece by product), reconciliation tables (adjusting items), free cash flow;
  * Form 10-Q / 10-K face statements: operating-expense detail, balance sheet, cash flow (year to date), shares issued by class.
The Q3-2026 8-K carries no Ex. 99.2, so its statement and operating data come from the Q3-2026 10-Q (MD&A tables).
Nothing is estimated; a line not presented is omitted. See EXTRACTION_SCHEMA.md."""
import json, os, re, glob, sys
import parse_release as P

S = os.environ.get('UPS_SRC', '/tmp/ups_src')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
CIK = '1090727'
FIL = json.load(open(os.path.join(S, 'filings.json')))
QEND = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
QNAME = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth'}


def url(o, doc):
    return f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{doc}"


def txt(o, doc):
    p = os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
    if not os.path.exists(p): return None
    t = open(p, encoding='utf-8', errors='replace').read()
    if doc.lower().endswith('.txt'):          # fixed-width release (2007): 2+ spaces separate cells
        out = []
        for l in t.split('\n'):
            s = l.strip()
            if re.match(r'^[-=\s]+$', s) or s.startswith('<'): continue
            if re.match(r'UNITED PARCEL SERVICE[.,] INC\.?$', s, re.I): out.append('United Parcel Service, Inc.'); continue
            s = re.sub(r'\$\s*', '', s)
            out.append(' | '.join(c for c in re.split(r'\s{2,}', s) if c))
        t = '\n'.join(out).replace('EINANCIAL', 'FINANCIAL')
    return t


def release_for(y, q):
    """The earnings release for fiscal quarter q of year y: 8-K Item 2.02 filed in the ~7 weeks after the quarter end which carries a
    'Selected Financial Data' schedule for three months (or the release text itself). Latest such filing wins."""
    lo = {1: f'{y}-04-01', 2: f'{y}-07-01', 3: f'{y}-10-01', 4: f'{y + 1}-01-01'}[q]
    hi = {1: f'{y}-05-31', 2: f'{y}-08-31', 3: f'{y}-11-30', 4: f'{y + 1}-03-05'}[q]
    best = None
    for o in FIL:
        if o['form'] != '8-K' or '2.02' not in o['items'] or not (lo <= o['date'] <= hi): continue
        docs = [d for d in o['files'] if d != o['primary'] and re.search(r'99', d)]
        texts = [(d, txt(o, d)) for d in docs]
        texts = [(d, t) for d, t in texts if t]
        secs = [s for d, t in texts for s in P.sections(t)]
        if any(re.search(r'selected financial', s['title'], re.I) for s in secs) or (y, q) == (2026, 3):
            best = (o, texts, secs)
    return best


def filing_for(y, q):
    form = '10-K' if q == 4 else '10-Q'
    end = f'{y}-{QEND[q]}'
    for o in FIL:
        if o['form'] == form and o['report'] == end:
            return o, txt(o, o['primary'])
    return None, None


# ---------------------------------------------------------------- Selected Financial Data
SEGS = [('us', r'u\.s\. domestic package'), ('intl', r'international package'), ('scs', r'supply chain (&|and) freight|supply chain solutions')]


def fin_data(sec, col=0):
    """Selected Financial Data -> dict (col 0 = current period, 1 = prior-year comparative)."""
    d = {}; blk = ''; adj = False; foot = []; infoot = False
    for l in sec['lines']:
        s = l.strip()
        if not s: continue
        lab = P.norm(P.cells(s)[0])
        if re.search(r'adjusted income data|as adjusted', lab) and ' | ' not in s:
            adj = True; continue
        lab2, vals = P.row(s)
        if adj and (re.match(r'^\(\d\)', s) or infoot) and (not vals or all(v is None for v in vals) or re.match(r'^\(\d\)\s*\|', s)):
            if re.match(r'(certain )?prior year amounts|certain amounts are calculated', s, re.I): continue
            infoot = True
            foot.append(re.sub(r'\s+', ' ', s.replace(' | ', ' '))); continue
        if ' | ' not in s or not vals or all(v is None for v in vals):
            if re.match(r'(revenue|operating expenses|operating profit|other income|per share amounts|weighted-average shares)', lab):
                blk = lab.split(' (')[0]
            continue
        lab = P.norm(lab2)
        v = vals[col] if len(vals) > col else None
        if v is None: continue
        seg = next((k for k, p in SEGS if re.fullmatch(p, lab)), None)
        pre = 'a_' if adj else ''
        if seg and blk.startswith('revenue') and not adj: d[f'rev_{seg}'] = v
        elif seg and blk.startswith('operating expenses') and not adj: d[f'opex_{seg}'] = v
        elif seg and (blk.startswith('operating profit') or adj): d[f'{pre}op_{seg}'] = v
        elif lab == 'total revenue': d['rev'] = v
        elif lab == 'compensation and benefits': d['comp'] = v
        elif lab == 'other' and blk.startswith('operating expenses'): d['oth_opex'] = v
        elif lab == 'total operating expenses': d['opex'] = v
        elif lab.startswith('total operating profit'): d[f'{pre}op'] = v
        elif lab.startswith('other pension income'): d['pen_inc'] = v
        elif lab.startswith('investment income'): d['inv_inc'] = v
        elif lab == 'interest expense': d['int_exp'] = -v
        elif lab.startswith('total other income'): d[f'{pre}oth'] = v
        elif re.match(r'income \(?loss?\)? ?before income taxes|income before income taxes', lab): d[f'{pre}ebt'] = v
        elif lab.startswith('income tax') or lab == 'income taxes': d[f'{pre}tax'] = v
        elif re.match(r'net income( \(loss\))?$', lab): d[f'{pre}ni'] = v
        elif lab.startswith('basic earnings'): d[f'{pre}eps_b'] = v
        elif lab.startswith('diluted earnings'): d[f'{pre}eps_d'] = v
        elif lab == 'basic': d['sh_b'] = v
        elif lab == 'diluted': d['sh_d'] = v
    if foot: d['a_footnotes'] = ' '.join(foot)[:1700]
    return d


PROD = {'us': [('nda', 'next day air'), ('def', 'deferred'), ('gnd', 'ground'), ('cargo', 'cargo and other|cargo & other|cargo')],
        'intl': [('dom', 'domestic'), ('exp', 'export'), ('cargo', 'cargo and other|cargo & other|cargo')],
        'scs': [('fwdlog', 'forwarding and logistics'), ('fwd', 'forwarding'), ('log', 'logistics'), ('frt', 'freight'), ('oth', 'other')]}


def op_data(sec, col=0):
    """Selected Operating Data -> dict: revenue / average daily volume (thousands) / revenue per piece by product, operating days."""
    d = {}; blk = ''; seg = ''
    for l in sec['lines']:
        s = l.strip()
        if not s: continue
        lab2, vals = P.row(s)
        lab = P.norm(lab2)
        if ' | ' not in s or not vals or all(v is None for v in vals):
            if lab.startswith('revenue'): blk = 'rev'
            elif lab.startswith('average daily package'): blk = 'adv'
            elif lab.startswith('average revenue per piece'): blk = 'rpp'
            k = next((k for k, p in SEGS if re.fullmatch(p, lab)), None)
            if k: seg = k
            continue
        v = vals[col] if len(vals) > col else None
        if v is None: continue
        if lab.startswith('consolidated volume'): d['vol'] = v; continue
        if lab.startswith('operating weekdays') or lab.startswith('operating days'): d['days'] = v; continue
        if lab == 'consolidated': d[f'{blk}_tot'] = v; continue
        m = re.match(r'total (.*)', lab)
        if m:
            k = next((k for k, p in SEGS if re.fullmatch(p, m.group(1))), None)
            if k: d[f'{blk}_{k}'] = v
            continue
        for key, pat in PROD.get(seg, []):
            if re.fullmatch(pat, lab):
                d[f'{blk}_{seg}_{key}'] = v; break
    return d


def opex_detail(sec, col=0):
    m = {'compensation and benefits': 'comp', 'repairs and maintenance': 'rm', 'depreciation and amortization': 'da', 'purchased transportation': 'pt',
         'fuel': 'fuel', 'other occupancy': 'occ', 'other expenses': 'othx', 'total operating expenses': 'opex'}
    d = {}
    for l in sec['lines']:
        if ' | ' not in l: continue
        lab, vals = P.row(l); lab = P.norm(lab)
        if lab in m and len(vals) > col and vals[col] is not None: d[m[lab]] = vals[col]
    return d


# ---------------------------------------------------------------- reconciliation items (company labels)
KIND = (('op', r'operating profit \(gaap\)'), ('ebt', r'income (\(loss\) )?before income taxes \(gaap\)'), ('oth', r'other income( and)? \(expense\) \(gaap\)'),
        ('tax', r'income tax expense( \(benefit\))? \(gaap\)'), ('ni', r'net income( \(loss\))? \(gaap\)'))


def recon_items(secs, months):
    """Adjusting items with the company's labels from the left-hand tables of the 'Reconciliation of GAAP and Non-GAAP Adjusted
    Measures' schedules (Q4-2018 release onward) for the given number of months.
    -> {'op' | 'ebt' | 'oth' | 'tax' | 'ni': {'gaap': v, 'adj': v, 'items': [[label, value as added back]]}}; first table of each kind wins."""
    out = {}
    for s in secs:
        t = s['title'].lower()
        if not re.search(r'reconciliation of gaap and (non-gaap )?(as )?adjusted', t) or 'by segment' in t or 'cost per piece' in t: continue
        if s['months'] != months: continue
        cur = None
        for l in s['lines']:
            if ' | ' not in l: continue
            cs = P.cells(l)
            lab = cs[0]; n = P.norm(lab)
            v = next((P.num(c) for c in cs[1:] if P.num(c) is not None), None) if len(cs) > 1 and P.num(cs[1]) is not None else None
            k = next((k for k, pat in KIND if re.match(pat, n)), None)
            if k:
                cur = k if k not in out else None
                if cur: out[cur] = {'gaap': v, 'items': []}
                continue
            if not cur: continue
            if n.startswith('non-gaap adjusted') or n.startswith('as adjusted') or n.startswith('adjusted '):
                out[cur]['adj'] = v; cur = None; continue
            if v is None: continue
            if n in ('transformation 2.0', 'fit to serve', 'network reconfiguration and efficiency reimagined', 'business portfolio review',
                     'financial systems', 'spans and layers', 'transformation 1.0', 'network reconfiguration', 'other'):
                continue                                   # components of the transformation total
            out[cur]['items'].append([re.sub(r'\s*\(\d\)(,\s*\(\d\))*', '', lab).strip().rstrip(':'), v])
    return out


def grab(secs, title_pat, months, label_pat, nth=0):
    """First section matching title / months: the nth number following the cell that matches label_pat."""
    for s in secs:
        if not re.search(title_pat, s['title'], re.I) or (months and s['months'] != months): continue
        for l in s['lines']:
            cs = P.cells(l)
            for i, c in enumerate(cs):
                if re.match(label_pat, P.norm(c)):
                    vals = []
                    for c2 in cs[i + 1:]:
                        v = P.num(c2)
                        if v is None: break
                        vals.append(v)
                    if len(vals) > nth: return vals[nth]
    return None


def seg_recon(secs, months):
    """'Reconciliation ... by Segment' -> {'us': (gaap op, adjusted op), ...} (operating profit = 4th number of the row)."""
    out = {}
    for s in secs:
        if 'by segment' not in s['title'].lower() or s['months'] != months: continue
        seg = None
        for l in s['lines']:
            cs = P.cells(l)
            k = next((k for k, p in SEGS if re.fullmatch(p, P.norm(cs[0]))), None)
            if k: seg = k; continue
            lab, vals = P.row(l)
            n = P.norm(lab)
            if seg and n == 'gaap' and len(vals) >= 5: out.setdefault(seg, {})['op'] = vals[3]
            if seg and n.startswith('non-gaap adjusted measure') and len(vals) >= 5: out.setdefault(seg, {})['a_op'] = vals[3]
        if out: return out
    return out


def narrative_segments(text):
    """Segment revenue / operating profit from the release narrative tables ('U.S. Domestic Segment' ... 'Revenue | $14,865 M | ...')."""
    d = {}; seg = None
    for l in text.split('\n'):
        s = l.strip()
        if re.match(r'U\.S\. Domestic Segment', s): seg = 'us'
        elif re.match(r'International Segment', s): seg = 'intl'
        elif re.match(r'Supply Chain Solutions', s): seg = 'scs'
        elif re.match(r'\d{4} Outlook|Outlook', s): seg = None
        if not seg or ' | ' not in s: continue
        cs = [c.replace(' M', '').replace('M', '') for c in P.cells(s)]
        vals = [P.num(c) for c in cs[1:]]
        if cs[0] == 'Revenue' and f'rev_{seg}' not in d and vals and vals[0] is not None: d[f'rev_{seg}'] = vals[0]
        if cs[0] == 'Operating profit' and f'op_{seg}' not in d and len(vals) >= 2 and vals[0] is not None:
            d[f'op_{seg}'] = vals[0]; d[f'a_op_{seg}'] = vals[1]
    return d


# ---------------------------------------------------------------- 10-K / 10-Q face statements
def col_index(text, y, q, kind):
    """Column of the current period in a face statement: balance sheets and cash flows put the current period first; the 10-Q income
    statement has three months (current, prior) then year to date (current, prior)."""
    return 0


BS_MAP = [('cash', r'cash and cash equivalents$'), ('ms', r'marketable securities( and short-term investments)?$|short-term investments$'),
          ('ar', r'accounts receivable, net$|accounts receivable$'), ('tca', r'total current assets$'), ('ppe', r'property, plant and equipment, net$'),
          ('rou', r'operating lease right-of-use assets$'), ('gw', r'goodwill$'), ('intang', r'intangible assets, net$'), ('ta', r'total assets$'),
          ('cur_debt', r'current maturities of long-term debt.*$'), ('cur_lease', r'current maturities of operating leases$'), ('ap', r'accounts payable$'),
          ('wages', r'accrued wages and withholdings$'), ('tcl', r'total current liabilities$'),
          ('ltd', r'long-term debt( and finance leases)?$'), ('nc_lease', r'non-current operating leases$'),
          ('pension', r'pension and postretirement benefit obligations$'), ('dtl', r'deferred income tax liabilities$|deferred taxes, credits and other liabilities$'),
          ('apic', r'additional paid-in capital$'), ('re', r'retained earnings$'), ('aoci', r'accumulated other comprehensive (loss|income \(loss\))$'),
          ('eq', r"total equity for controlling interests$"), ('nci', r'noncontrolling interests?$|minority interests$|total equity for non-controlling interests$'),
          ('teq', r"total shareowners' equity$"), ('tle', r"total liabilities and shareowners' equity$")]
CF_MAP = [('ni', r'net income$'), ('da', r'depreciation and amortization$'), ('pen_exp', r'pension and postretirement benefit expense$'),
          ('pen_contrib', r'pension and postretirement benefit contributions$'), ('def_tax', r'deferred (income )?tax(es)?( \(benefit\))?( expense)?( \(benefit\))?.*$'),
          ('sbc', r'stock (compensation|award) (\(benefit\) )?expense( \(benefit\))?$|stock-based compensation expense$'), ('cfo', r'net cash from operating activities$'),
          ('capex', r'capital expenditures$'), ('disp', r'proceeds from disposals? of (businesses, )?property, plant and equipment$'),
          ('ms_buy', r'purchases of marketable securities.*$'), ('ms_sell', r'sales and maturities of marketable securities.*$'),
          ('fin_rec', r'net .*finance receivables$'),
          ('acq', r'(cash (paid|received).* for business acquisitions.*|acquisitions, net of cash acquired)$'),
          ('oth_inv', r'other investing activities$'), ('cfi', r'net cash .*investing activities$'),
          ('st_debt', r'net change in short-term debt$'), ('debt_in', r'proceeds from (long-term )?borrowings$'), ('debt_out', r'repayments of (long-term )?borrowings$'),
          ('bb', r'purchases of common stock$'), ('iss', r'issuances of common stock$'), ('div', r'dividends$'), ('oth_fin', r'other financing activities$'),
          ('cff', r'net cash .*financing activities$'),
          ('fx', r'effect of exchange rate changes on cash.*$'), ('net', r'net (increase|decrease|increase \(decrease\)|\(decrease\) increase|\(increase\) decrease) in cash.*$'),
          ('beg', r'beginning of (period|year)$'), ('end', r'end of (period|year)$')]
IS_MAP = [('rev', r'revenue$'), ('comp', r'compensation and benefits$'), ('rm', r'repairs and maintenance$'), ('da', r'depreciation and amortization$'),
          ('pt', r'purchased transportation$'), ('fuel', r'fuel$'), ('occ', r'other occupancy$'), ('othx', r'other expenses$'),
          ('opex', r'total operating expenses$'), ('op', r'operating profit$'), ('pen_inc', r'other pension income( \(expense\))?$'),
          ('inv_inc', r'investment income.*$'), ('int_exp', r'interest expense$'), ('oth', r'total other income( and)? \(expense\)$'),
          ('ebt', r'income (\(loss\) )?before income taxes$'), ('tax', r'income tax expense( \(benefit\))?$|income taxes$'), ('ni', r'net income( \(loss\))?$'),
          ('eps_b', r'basic earnings( \(loss\))? per share$'), ('eps_d', r'diluted earnings( \(loss\))? per share$')]


def map_rows(rows, mp, col):
    d = {}; raw = []
    for lab, vals in rows:
        n = P.norm(lab)
        if not vals or len(vals) <= col or vals[col] is None: continue
        raw.append([lab[:90], vals[col]])
        for k, pat in mp:
            if k not in d and re.match(pat, n): d[k] = vals[col]; break
    return d, raw


def face(text, q):
    """-> (is_q, is_ytd, bs, cf, raw) from the first face statements in a 10-K / 10-Q."""
    out = {}
    bs_rows, e = P.statement(text, r'CONSOLIDATED BALANCE SHEETS\s*$', r"Total Liabilities and Shareowners. Equity")
    bs, raw_bs = map_rows(bs_rows, BS_MAP, 0)
    for lab, vals in bs_rows:
        m = re.match(r'Class\s([AB]) common stock \(\s*(\d[\d,]*) (and|shares issued)', lab.replace('\xa0', ' '))
        if m: bs[f'sh_{m.group(1).lower()}'] = float(m.group(2).replace(',', ''))
    is_rows, e2 = P.statement(text, r'STATEMENTS? OF CONSOLIDATED INCOME\s*$', r'Diluted Earnings( \(Loss\))? Per Share', e or 0)
    isq, _ = map_rows(is_rows, IS_MAP, 0)
    isy, _ = map_rows(is_rows, IS_MAP, 0 if q in (1, 4) else 2)
    cf_rows, e3 = P.statement(text, r'STATEMENTS? OF CONSOLIDATED CASH FLOWS\s*$', r'End of (period|year)', e2 or 0)
    cf, raw_cf = map_rows(cf_rows, CF_MAP, 0)
    for d in (isq, isy):
        if 'int_exp' in d: d['int_exp'] = -d['int_exp']
    return isq, isy, bs, cf, {'bs': raw_bs, 'cf': raw_cf}


def dps_from(text):
    """Dividends per share declared, from the shareowners' equity roll-forward ('Dividends ($0.62 per share)')."""
    m = re.findall(r'Dividends \(\$\s?(\d+\.\d+) per share', text)
    return [float(x) for x in m]


# ---------------------------------------------------------------- 10-Q MD&A tables (Q3-2026: no Ex. 99.2 on EDGAR)
def mdna_ops(text):
    """Product revenue / ADV / revenue per piece / operating days from the 10-Q MD&A segment tables (three-month column first),
    plus weighted-average shares from the earnings-per-share note."""
    d = {}
    lines = text.split('\n')
    start = max([i for i, l in enumerate(lines) if l.strip() == 'Results of Operations - Segment Review'] or [0])
    seg = None; blk = None
    for l in lines[start:]:
        s = l.strip()
        if s == 'U.S. Domestic Package': seg = 'us'; blk = None
        elif s == 'International Package': seg = 'intl'; blk = None
        elif s in ('Supply Chain Solutions', 'SCS'): seg = 'scs'; blk = None
        elif s.startswith('Consolidated Operating Expenses') or s.startswith('Other Income (Expense)'): break
        if not seg: continue
        lab, vals = P.row(s); n = P.norm(lab)
        if n.startswith('average daily package volume'): blk = 'adv'; continue
        if n.startswith('average revenue per piece'): blk = 'rpp'; continue
        if n.startswith('revenue (in millions)'): blk = 'rev'; continue
        if n.startswith('operating expenses (in millions)'): blk = None; continue
        if ' | ' not in s: continue
        if not vals or vals[0] is None: continue
        if n.startswith('operating days in period'): d['days'] = vals[0]; continue
        if n.startswith('total average daily package volume'): d[f'adv_{seg}'] = vals[0]; continue
        if n.startswith('total average revenue per piece'): d[f'rpp_{seg}'] = vals[0]; continue
        if n == 'total revenue' and blk == 'rev': d.setdefault(f'rev_{seg}', vals[0]); blk = None; continue
        if blk:
            n = 'other' if n == 'other scs' else n
            for key, pat in PROD[seg]:
                if re.fullmatch(pat, n) and f'{blk}_{seg}_{key}' not in d:
                    d[f'{blk}_{seg}_{key}'] = vals[0]; break
    sh = {}
    for l in lines:
        m = re.match(r'Denominator for (basic|diluted) earnings per share \| ([\d,]+)', l.strip())
        if m: sh.setdefault('sh_' + m.group(1)[0], float(m.group(2).replace(',', '')))
    return d, sh


# ---------------------------------------------------------------- per period
def build(y, q):
    """q in 1..4 -> quarter record; q = 0 -> annual record (Q4 release twelve-month columns + 10-K)."""
    qq = q or 4
    rel = release_for(y, qq)
    fo, ft = filing_for(y, qq)
    months = 3 if q else 12
    rec = {'period': (f'Q{q}-{str(y)[2:]}' if q else str(y)), 'fy': y, 'q': q, 'period_end': f'{y}-{QEND[qq]}', 'sources': {}, 'notes': []}
    if rel:
        o, texts, secs = rel
        rec['sources']['release'] = [url(o, d) for d, _ in texts]; rec['sources']['release_date'] = o['date']
        want = (r'(%s|quarter)' % QNAME[qq]) if q else r'year to date|year-to-date'
        fs = [s for s in secs if re.search(r'selected financial', s['title'], re.I) and re.search(want, s['title'], re.I)]
        if not fs and q == 0:
            fs = [s for s in secs if re.search(r'selected financial', s['title'], re.I) and s['months'] == 12]
        osec = [s for s in secs if re.search(r'selected operating', s['title'], re.I) and re.search(want, s['title'], re.I)]
        if q == 1 and not fs:
            fs = [s for s in secs if re.search(r'selected financial', s['title'], re.I)][:1]
            osec = [s for s in secs if re.search(r'selected operating', s['title'], re.I)][:1]
        if fs:
            rec['is'] = fin_data(fs[0]); rec['py'] = {'is': fin_data(fs[0], 1)}
        if osec:
            rec['ops'] = op_data(osec[0]); rec['py']['ops'] = op_data(osec[0], 1)
        ox = [s for s in secs if re.search(r'detail of operating expenses', s['title'], re.I) and re.search(want, s['title'], re.I)]
        if ox: rec['opex'] = opex_detail(ox[0])
        rec['recon'] = recon_items(secs, months)
        def foot_notes(ok):
            out = []
            for s_ in secs:
                if re.search(r'reconciliation of gaap and', s_['title'], re.I) and ok(s_) and 'cost per piece' not in s_['title'].lower():
                    for l in s_['lines']:
                        t = re.sub(r'\s+', ' ', l.strip())
                        if re.match(r'^\(\d\)', t) and len(t) > 25 and t not in out: out.append(t)
            return out
        notes = foot_notes(lambda s_: s_['months'] == months)
        if not notes and not q: notes = foot_notes(lambda s_: True)     # year tables sit under the quarter's schedule header in some releases
        if notes: rec['adj_notes'] = ' '.join(notes)[:1800]
        # free cash flow (year to date)
        for s in secs:
            if re.search(r'reconciliation of free cash flow', s['title'], re.I):
                for l in s['lines']:
                    if ' | ' in l:
                        lab, vals = P.row(l)
                        if re.match(r'free cash flow', P.norm(lab)) and vals and vals[0] is not None:
                            rec.setdefault('ngaap', {}).setdefault('fcf_pub_ytd', vals[0])
                        if re.match(r'proceeds from disposals? of', P.norm(lab)) and vals and vals[0] is not None:
                            rec.setdefault('ngaap', {}).setdefault('fcf_disp_ytd', vals[0])
    if ft:
        rec['sources']['filing'] = url(fo, fo['primary']); rec['sources']['filing_date'] = fo['date']
        isq, isy, bs, cf, raw = face(ft, qq)
        rec['face_is'] = isy if q == 0 else isq
        rec['face_is_ytd'] = isy
        rec['bs'] = bs
        cf['ytd_months'] = 3 * qq
        rec['cf'] = cf
        rec['raw'] = raw
        m = re.search(r'Dividends declared per share \| ([\d.]+)', ft)
        if m: rec['dps_declared_ytd'] = float(m.group(1))
        if 'is' not in rec and rel and q:
            # release without financial schedules (Q3-2026): statement data from the 10-Q, segments and adjusted data from the release
            o, texts, secs = rel
            mo, sh = mdna_ops(ft)
            d = {k: isq[k] for k in ('rev', 'opex', 'op', 'pen_inc', 'inv_inc', 'int_exp', 'oth', 'ebt', 'tax', 'ni', 'eps_b', 'eps_d') if k in isq}
            d.update(sh)
            d.update(narrative_segments(texts[0][1]))
            sr = seg_recon(secs, 3)
            for k, v in sr.items():
                if 'a_op' in v: d[f'a_op_{k}'] = v['a_op']
            R3 = r'reconciliation of gaap and non-gaap adjusted measures$'
            for key, pat in (('a_op', r'non-gaap adjusted operating profit'), ('a_ebt', r'non-gaap adjusted income before income taxes'),
                             ('a_tax', r'non-gaap adjusted income tax expense'), ('a_ni', r'non-gaap adjusted net income'),
                             ('a_eps_d', r'non-gaap adjusted diluted earnings per share')):
                v = grab(secs, R3, 3, pat)
                if v is not None: d[key] = v
            rec['is'] = d; rec['ops'] = mo
            rec['opex'] = {k: isq[k] for k in ('comp', 'rm', 'da', 'pt', 'fuel', 'occ', 'othx', 'opex') if k in isq}
            rec['notes'].append('The 8-K of %s carries no Ex. 99.2 financial schedules: income statement, operating-expense detail, operating data and '
                                'shares are from the Form 10-Q; segment revenue / operating profit and the non-GAAP reconciliations are from the release (Ex. 99.1).' % o['date'])
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    periods = [(y, 0) for y in range(2006, 2026)] + [(y, q) for y in range(2013, 2027) for q in (1, 2, 3, 4) if (y, q) <= (2026, 3)]
    for y, q in periods:
        rec = build(y, q)
        json.dump(rec, open(os.path.join(OUT, rec['period'] + '.json'), 'w'), indent=1)
        i = rec.get('is', {}); b = rec.get('bs', {}); c = rec.get('cf', {})
        print(rec['period'], 'rel' if 'release' in rec['sources'] else '---', 'fil' if 'filing' in rec['sources'] else '---',
              i.get('rev'), i.get('op'), i.get('a_op'), i.get('ni'), i.get('eps_d'), '| ops', len(rec.get('ops', {})), '| bs', b.get('ta'), b.get('tle'),
              '| cf', c.get('cfo'), c.get('end'), '| recon', {k: len(v['items']) for k, v in rec.get('recon', {}).items()})


if __name__ == '__main__':
    main()
