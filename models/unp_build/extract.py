"""Per-period extraction for Union Pacific: one JSON per quarter (Q1-06 .. Q3-26) and per fiscal year (2005 .. 2025) in data/,
from the Form 8-K Item 2.02 earnings releases (Ex. 99.1), as originally reported, plus 10-K / 10-Q text items (fuel surcharge
revenues, debt maturities). Run make_index.py and fetch.py first ($UNP_SRC). See EXTRACTION_SCHEMA.md for the record layout.

Column conventions of the releases: a quarterly release table has [quarter, prior-year quarter, % change, year-to-date,
prior-year year-to-date, % change]; a Q1 release has [quarter, prior-year quarter, % change]; balance sheets have
[period end, prior December 31]; cash flows are year-to-date [current, prior year]. The Q4 release gives the fourth quarter and
the full year. Costs are stored positive; other income is signed (income +); cash flow as presented.
"""
import json, os, re, glob, datetime as dt
from parse_release import Release, norm, cells

S = os.environ.get('UNP_SRC', '/tmp/unp_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
os.makedirs(OUT, exist_ok=True)
CIK = '100885'
URL = lambda acc, doc: f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc.replace('-', '')}/{doc}"

def releases():
    F = json.load(open(os.path.join(S, 'filings.json')))
    out = []
    for o in F:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        ex = [x for x in o['files'] if x != o['primary'] and not x.endswith('.txt') and not re.search(r'ex(10|2|3|4)', x.lower())]
        if not ex: continue
        t = f"{S}/txt/{o['date']}_8-K_{o['acc']}_{ex[0].rsplit('.', 1)[0]}.txt"
        if not os.path.exists(t) or os.path.getsize(t) < 8000: continue
        d = dt.date.fromisoformat(o['date'])
        # release month -> quarter reported: Jan -> Q4 of prior year, Apr -> Q1, Jul -> Q2, Oct -> Q3
        q = {1: 4, 2: 4, 4: 1, 5: 1, 7: 2, 8: 2, 10: 3, 11: 3}[d.month]
        y = d.year - 1 if q == 4 else d.year
        out.append(dict(y=y, q=q, path=t, url=URL(o['acc'], ex[0]), date=o['date'], acc=o['acc']))
    return out

def pick(vals, which, hdr=None):
    """which: 'cur' | 'py' | 'ytd' | 'ytd_py' from a release row"""
    if vals is None: return None
    n = len(vals)
    if which == 'cur': return vals[0] if n else None
    if which == 'py': return vals[1] if n > 1 else None
    if n >= 6: return vals[3] if which == 'ytd' else vals[4]
    if n == 4: return vals[2] if which == 'ytd' else vals[3]        # tables without % columns
    if n <= 3: return vals[0] if which == 'ytd' else (vals[1] if n > 1 else None)   # Q1: year-to-date = quarter
    return None

NEG = {'int', 'tax'}                 # shown in parentheses in the releases; stored positive
def is_record(i, which):
    o = {}
    for k, v in i.items():
        if k.startswith('_'): continue
        x = pick(v, which, i.get('_hdr'))
        if x is None: continue
        if k in NEG: x = -x
        o[k] = x
    if 'rev' not in o and 'frt' in o and 'oth_rev' in o: o['rev'] = o['frt'] + o['oth_rev']; o['_rev_derived'] = True
    if 'frt' not in o and 'rev' in o: o['frt_na'] = True
    if 'or' in o and o['or'] > 1.5: pass
    return o

GROUP_KEYS = {   # label (normalised) -> model key; legacy and current structures
    'agricultural': 'ag', 'agricultural products': 'ag', 'automotive': 'auto', 'chemicals': 'chem', 'energy': 'energy', 'coal': 'energy',
    'industrial products': 'indprod', 'intermodal': 'intermodal', 'industrial': 'industrial', 'premium': 'premium', 'bulk': 'bulk',
    'grain & grain products': 'grain', 'fertilizer': 'fert', 'food & refrigerated': 'food', 'coal & renewables': 'coalren',
    'industrial chemicals & plastics': 'chemplas', 'metals & minerals': 'metals', 'forest products': 'forest',
    'energy & specialized markets': 'energyspec', 'total': 'total', 'average': 'total',
}

def seg_record(f, which):
    o = {}
    for sub, unit in (('rev', f['units']['rev']), ('cars', f['units']['cars']), ('arpc', 1.0)):
        for label, vals in f[sub].items():
            k = GROUP_KEYS.get(norm(label))
            if k is None: continue
            v = pick(vals, which)
            if v is None: continue
            o.setdefault(k, {})[sub] = round(v * unit, 3) if unit != 1.0 else v
            o[k]['label'] = label
    return o

BS_MAP = [(r'^cash and (cash equivalents|temporary investments)', 'cash'), (r'^short term investments', 'sti'), (r'^other current assets', 'oca'),
          (r'^(total )?investments', 'inv'), (r'^(net properties|properties net|properties)', 'ppe'), (r'^operating lease assets', 'rou'), (r'^other assets', 'oa'), (r'^total assets', 'ta'),
          (r'^(debt due within one year|current portion of long term debt)', 'std'), (r'^other current liabilities', 'ocl'),
          (r'^(debt due after one year|long term debt)', 'ltd'), (r'^operating lease liabilities', 'olease'), (r'^deferred income taxes', 'dtl'), (r'^other long term liabilities', 'oltl'),
          (r'^total liabilities$', 'tl'), (r'^(total )?(common )?shareholders equity', 'eq'), (r'^total liabilities and', 'tle'), (r'^total$', 'total')]

def bs_record(R):
    rows = R.parse_two_col('bs', 0, 60)
    o, totals = {}, []
    for label, vals in rows.items():
        t = norm(label.split(' #')[0])
        for pat, key in BS_MAP:
            if re.match(pat, t):
                v = vals[0] if vals else None
                if v is None: break
                if key == 'total': totals.append(v); break
                if key not in o: o[key] = v
                break
    if 'ta' not in o and totals: o['ta'] = totals[0]
    if 'tle' not in o and len(totals) > 1: o['tle'] = totals[1]
    return o, rows

CF_MAP = {'op': [(r'^net income', 'ni'), (r'^depreciation', 'dep'), (r'^deferred( and other)? income taxes|^noncurrent income taxes', 'dtax'), (r'^other', 'oth'),
                 (r'^cash .*operating activities', 'cfo')],
          'inv': [(r'^capital investments', 'capex'), (r'^purchases of short term investments', 'sti_buy'), (r'^maturities of short term investments', 'sti_mat'),
                  (r'^other', 'oth'), (r'^cash .*investing activities', 'cfi')],
          'fin': [(r'^(common shares repurchased|share repurchase programs)', 'bb'), (r'^dividends paid', 'div'), (r'^debt issued', 'debt_iss'),
                  (r'^debt repaid', 'debt_rep'), (r'^debt exchange', 'debt_exch'), (r'^(other|financings and other)', 'oth'), (r'^cash .*financing activities', 'cff')],
          'end': [(r'^net change in cash', 'net'), (r'.*beginning of (year|period)', 'beg'), (r'.*end of (period|year)', 'end')],
          'fcf': [(r'^free cash flow', 'fcf')]}

def cf_record(R):
    o, sect = {}, None
    for l in R.block('cf', 0, 70):
        if '|' not in l:
            t = norm(l)
            if t.startswith('operating activities'): sect = 'op'
            elif t.startswith('investing activities'): sect = 'inv'
            elif t.startswith('financing activities'): sect = 'fin'
            elif t.startswith('free cash flow'): sect = 'fcf'
            elif t.startswith('cash and cash equivalents') and sect == 'end': pass
            continue
        label, vals = cells(l)
        t = norm(label)
        if not vals or (re.search(r'20\d\d', label) and all(v is None or 1990 < v < 2100 for v in vals)): continue
        if t.startswith('net change in cash'): sect = 'end'
        if sect is None: continue
        for pat, key in CF_MAP.get(sect, []) + (CF_MAP['end'] if sect in ('fin', 'end') else []):
            if re.match(pat, t):
                kk = key if key in ('ni', 'dep', 'dtax', 'cfo', 'capex', 'cfi', 'bb', 'div', 'debt_iss', 'debt_rep', 'debt_exch', 'cff', 'net', 'beg', 'end', 'fcf',
                                    'sti_buy', 'sti_mat') else f'{key}_{sect}'
                if kk in o and kk != 'fcf': break
                if kk == 'fcf' and sect != 'fcf': break
                o[kk] = vals[0]; o[kk + '_py'] = vals[1] if len(vals) > 1 else None
                if sect == 'fin' and key == 'cff': sect = 'end'
                break
    return o

OPS_MAP = [(r'^gross ton miles', 'gtm'), (r'^(total )?employees average|^average employees', 'emp'), (r'^average fuel price per gallon', 'fuel_px'),
           (r'^fuel consumed in gallons', 'gallons'), (r'^fuel consumption rate', 'fuel_rate'), (r'^average train speed', 'speed'),
           (r'^average terminal dwell', 'dwell'), (r'^average rail car inventory', 'car_inv'), (r'^freight car velocity', 'velocity'),
           (r'^train length', 'train_len'), (r'^workforce productivity', 'wf_prod'), (r'^locomotive productivity', 'loco_prod'),
           (r'^revenue carloads thousands', 'carloads'), (r'^revenue ton miles billions', 'rtm_bn'),
           (r'^weighted average shares basic', 'sh_b'), (r'^weighted average shares diluted', 'sh_d'), (r'^gtms.*per (average )?employee', 'gtm_emp'),
           (r'^customer satisfaction', 'csi'), (r'^intermodal service performance', 'spi_im'), (r'^manifest service performance', 'spi_man'),
           (r'^operating ratio', 'or'), (r'^effective tax rate', 'etr')]

def ops_record(R, which):
    o, rtm_sub = {}, False
    for l in R.block('ops', 0, 90):
        if '|' not in l:
            if norm(l).startswith('revenue ton miles'): rtm_sub = True
            continue
        label, vals = cells(l)
        t = norm(label)
        if not vals:
            if t.startswith('revenue ton miles'): rtm_sub = True
            continue
        if re.search(r'20\d\d', label) and all(v is None or 1990 < v < 2100 for v in vals): continue
        if rtm_sub and t in ('total',):
            v = pick(vals, which)
            if v is not None: o['rtm'] = v
            continue
        for pat, key in OPS_MAP:
            if re.match(pat, t):
                v = pick(vals, which)
                if v is None or key in o: break
                if key == 'gtm' and 'billion' in t: v *= 1000
                if key == 'rtm_bn': key, v = 'rtm', v * 1000
                o[key] = v; break
    return o

def fp_records(R):
    """normalise the 'Financial Performance' (adjusted results) tables. A table starts at a header row: either the column header
    'Reported results (GAAP) | item ... | Adjusted results (non-GAAP)' (rows = measures; 2020+), or a measures header
    'Operating Income | Income Taxes | Net Income | Diluted EPS | Operating Ratio' followed by rows 'Reported results (GAAP)' /
    items / 'Adjusted results (non-GAAP)' (2017-18). Returns [{'context', 'orientation', 'measures': {m: {'gaap','adj'}}, 'items': [{label, m: delta}]}]."""
    MEAS = {'operating income': 'oi', 'operating expenses': 'opex', 'operating expense': 'opex', 'income taxes': 'tax', 'income tax expense': 'tax',
            'income tax expense a': 'tax', 'net income': 'ni', 'diluted eps': 'eps', 'earnings per share diluted': 'eps', 'operating ratio': 'or',
            'other income net': 'oth_inc', 'other income': 'oth_inc'}
    out = []
    idx = [i for i, k in R.titles if k == 'fp']
    for s0 in idx:
        rec, mcols, colnames, ctx = None, None, None, []
        for j in range(s0, min(R.n, s0 + 45)):
            l = R.lines[j]
            if '|' not in l:
                t = norm(l)
                if j > s0 and (t.startswith('union pacific corporation') or t.startswith('non gaap measures')) and rec: break
                if l.strip() and not l.strip().startswith('*') and not l.strip().startswith('['): ctx.append(l.strip()[:120])
                continue
            raw = [c.strip() for c in l.split('|')]
            label, vals = cells(l)
            t = norm(label)
            heads = [norm(c) for c in raw[1:]]
            if any(h.startswith('reported results') for h in heads):          # rows = measures
                if rec and rec['measures']: out.append(rec)
                colnames = [c for c in raw[1:] if norm(c) not in ('pts', '')]
                rec = {'context': ' | '.join([raw[0]] + ctx[-2:])[:240], 'orientation': 'rows=measures', 'measures': {}, 'items': []}
                mcols = None; continue
            if any(h in ('operating income', 'net income', 'diluted eps') for h in heads) and len(heads) >= 3:   # columns = measures
                if rec and rec['measures']: out.append(rec)
                mcols = [MEAS.get(h, h) for h in heads]
                rec = {'context': ' | '.join([raw[0]] + ctx[-2:])[:240], 'orientation': 'cols=measures', 'measures': {}, 'items': []}
                colnames = None; continue
            if rec is None: continue
            if rec['orientation'] == 'rows=measures':
                if t.startswith('for the ') or re.match(r'^(20\d\d|millions)', t):
                    rec['context'] = (label + ' | ' + rec['context'])[:240]
                    if not rec['measures']: pass
                    continue
                m = MEAS.get(t)
                if m is None or len(vals) < 2: continue
                if m in rec['measures']:          # a second period's table without its own header row (e.g. "2016 Reported Results")
                    out.append(rec); rec = {'context': rec['context'] + ' (next)', 'orientation': 'rows=measures', 'measures': {}, 'items': []}
                rec['measures'][m] = {'gaap': vals[0], 'adj': vals[-1]}
                for k, iv in enumerate(vals[1:-1]):
                    nm = colnames[1 + k] if colnames and 1 + k < len(colnames) - 1 else f'item{k + 1}'
                    while len(rec['items']) <= k: rec['items'].append({'label': nm})
                    rec['items'][k][m] = iv
            else:
                if 'reported results' in t or 'adjusted results' in t:
                    key = 'adj' if t.startswith('adjusted') else 'gaap'
                    if re.match(r'^20\d\d', t): key = 'py_' + key
                    for m, v in zip(mcols, vals):
                        if m in MEAS.values(): rec['measures'].setdefault(m, {})[key] = v
                elif vals and not t.startswith('factors affecting') and not t.startswith('change vs'):
                    it = {'label': label}
                    for m, v in zip(mcols, vals):
                        if m in MEAS.values(): it[m] = v
                    rec['items'].append(it)
        if rec and rec['measures']: out.append(rec)
    return out

def ng_records(R):
    """adjusted debt / EBITDA (trailing twelve months), ROIC, debt to capital — first value column of the first such table"""
    o = {}
    for l in R.lines:
        if '|' not in l: continue
        label, vals = cells(l)
        t = norm(label)
        if not vals: continue
        for pat, key in ((r'^adjusted ebitda', 'adj_ebitda_ttm'), (r'^ebitda$', 'ebitda_ttm'), (r'^adjusted debt( \(b\))?$|^adjusted debt \(a\)$', 'adj_debt'),
                         (r'^operating lease liabilities$|^net present value of operating leases', 'lease_liab'),
                         (r'^interest on operating lease liabilities', 'lease_int_ttm'), (r'^return on invested capital as adjusted', 'roic_pub'),
                         (r'^adjusted debt / adjusted ebitda|^adjusted debt to adjusted ebitda', 'adj_lev_pub'), (r'^debt to capital', 'debt_cap_pub'),
                         (r'^adjusted debt to capital', 'adj_debt_cap_pub'), (r'^unfunded pension and opeb|^after tax unfunded pension', 'pension_adj'),
                         (r'^debt( \(a\))?$', 'debt_pub')):
            if re.match(pat, t) and key not in o:
                o[key] = vals[0]; break
    return o

def extract_release(r):
    R = Release(open(r['path']).read())
    i = R.parse_is(); f = R.parse_freight()
    q4 = r['q'] == 4
    rec = {'period': f"Q{r['q']}-{str(r['y'])[2:]}", 'period_end': f"{r['y']}-{[3, 6, 9, 12][r['q'] - 1]:02d}-{[31, 30, 30, 31][r['q'] - 1]}",
           'sources': {'release': r['url'], 'release_date': r['date']},
           'is': is_record(i, 'cur'), 'is_ytd': is_record(i, 'ytd'), 'seg': seg_record(f, 'cur'), 'seg_py': seg_record(f, 'py'),
           'py': {'is': is_record(i, 'py')}, 'ops': ops_record(R, 'cur'), 'ops_py': ops_record(R, 'py'),
           'ngaap': {'fp': fp_records(R), **ng_records(R)}, 'notes': []}
    bs, bsrows = bs_record(R); rec['bs'] = bs; rec['bs_raw'] = {k: v for k, v in bsrows.items()}
    cf = cf_record(R); cf['ytd_months'] = 3 * r['q']; rec['cf'] = cf
    rec['is_hdr'] = i.get('_hdr')
    ann = None
    if q4:
        ann = {'period': str(r['y']), 'period_end': f"{r['y']}-12-31", 'sources': {'release': r['url'], 'release_date': r['date']},
               'is': is_record(i, 'ytd'), 'py': {'is': is_record(i, 'ytd_py')}, 'seg': seg_record(f, 'ytd'), 'seg_py': seg_record(f, 'ytd_py'),
               'ops': ops_record(R, 'ytd'), 'ops_py': ops_record(R, 'ytd_py'), 'bs': bs, 'cf': cf, 'ngaap': {'fp': fp_records(R), **ng_records(R)}, 'notes': []}
    return rec, ann

# ---------------------------------------------------------------- 10-K / 10-Q text items
def filing_texts():
    F = json.load(open(os.path.join(S, 'filings.json')))
    out = {}
    for o in F:
        if o['form'] not in ('10-K', '10-Q'): continue
        t = f"{S}/txt/{o['date']}_{o['form']}_{o['acc']}_{o['primary'].rsplit('.', 1)[0]}.txt"
        if os.path.exists(t): out[(o['form'], o['report'])] = (t, URL(o['acc'], o['primary']))
    return out

def money(s):
    v = float(s.replace(',', '').replace('$', '').strip().split()[0]); return v

def fuel_surcharge(text):
    """annual (10-K: 'fuel surcharge revenue of $X million, $Y million ... for 2008, 2007 ...') and quarterly (10-Q MD&A) fuel surcharge revenues"""
    out = {}
    t = re.sub(r'\s+', ' ', text)
    m = re.search(r'fuel surcharge revenues? of \$([\d,.]+) (million|billion)(?:, \$([\d,.]+) (million|billion))?(?:, \$([\d,.]+) (million|billion))?(?:, and \$([\d,.]+) (million|billion))?[^.]*? for (20\d\d)', t)
    m2 = re.search(r'fuel surcharge programs generated freight revenues of \$([\d,.]+) (million|billion) and \$([\d,.]+) (million|billion) in (20\d\d) and (20\d\d)', t)
    m3 = re.search(r'[Ff]uel surcharge (?:program )?revenues? (?:of|totaled|was|were) \$([\d,.]+) (million|billion)[^.]{0,60} (20\d\d)', t)
    m4 = re.search(r'[Ff]reight revenues from fuel surcharge programs (?:increased|decreased) to \$([\d,.]+) (million|billion) in the (first|second|third|fourth) quarter of (20\d\d) compared to \$([\d,.]+) (million|billion)', t)
    def amt(a, u): return money(a) * (1000 if u == 'billion' else 1)
    if m2: out[int(m2.group(5))] = amt(m2.group(1), m2.group(2)); out[int(m2.group(6))] = amt(m2.group(3), m2.group(4)); out['src'] = m2.group(0)[:200]
    elif m:
        yrs = re.findall(r'20\d\d', t[m.start():m.end() + 60])
        vals = [(m.group(k), m.group(k + 1)) for k in (1, 3, 5, 7) if m.group(k)]
        for (a, u), y in zip(vals, yrs): out[int(y)] = amt(a, u)
        out['src'] = t[m.start():m.end() + 60][:260]
    if m4:
        out['q'] = amt(m4.group(1), m4.group(2)); out['q_py'] = amt(m4.group(5), m4.group(6)); out['q_src'] = m4.group(0)[:200]
    return out

def main():
    rels = releases()
    recs, anns = {}, {}
    for r in rels:
        rec, ann = extract_release(r)
        recs[rec['period']] = rec
        if ann: anns[ann['period']] = ann
    ft = filing_texts()
    fs_annual = {}
    for (form, rep), (t, url) in sorted(ft.items()):
        text = open(t).read()
        fs = fuel_surcharge(text)
        y = int(rep[:4]); mth = int(rep[5:7])
        if form == '10-K':
            for k, v in fs.items():
                if isinstance(k, int): fs_annual.setdefault(k, (v, url, fs.get('src')))
            if str(y) in anns: anns[str(y)]['sources']['10-K'] = url
        else:
            q = {3: 1, 6: 2, 9: 3}[mth]; key = f'Q{q}-{str(y)[2:]}'
            if key in recs:
                recs[key]['sources']['10-Q'] = url
                if 'q' in fs: recs[key]['extra'] = {'fuel_surcharge_rev': fs['q'], 'fuel_surcharge_rev_py': fs['q_py'], 'fuel_surcharge_src': fs['q_src']}
    for y, (v, url, src) in fs_annual.items():
        if str(y) in anns: anns[str(y)].setdefault('extra', {}).update({'fuel_surcharge_rev': v, 'fuel_surcharge_src': src, 'fuel_surcharge_url': url})
    for k, v in list(recs.items()) + list(anns.items()):
        json.dump(v, open(os.path.join(OUT, k + '.json'), 'w'), indent=1)
    print(len(recs), 'quarters', len(anns), 'years')

if __name__ == '__main__':
    main()
