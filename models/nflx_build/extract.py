"""Per-period extraction of the Netflix filings (text versions in $NFLX_SRC/txt, built by fetch.py) into data/<period>.json.

Sources per period (as originally reported):
  - Income statement, balance sheet, cash flow: the period's own Form 10-Q / 10-K face statements (first numeric column =
    current three months for the income statement, year to date for the cash flow, period end for the balance sheet).
    Q4 flows are derived later in normalize.py as fiscal year (10-K) - nine months (Q3 10-Q) and tied to the Q4 letter.
  - Legacy segments (Domestic streaming / International streaming / Domestic DVD, 2011-2019): 10-Q / 10-K segment note.
  - Regions (UCAN / EMEA / LATAM / APAC, 2017+): 10-Q / 10-K revenue and MD&A tables; FY2017-19 and the 2019 quarters from
    the latest filing presenting them (FY2019 10-K; 2020 10-Q prior-year columns); Q4 ARM from the Q4 shareholder letter.
  - Published free cash flow and its components: the period's shareholder letter / earnings release (8-K Item 2.02, Ex. 99.1);
    the column is matched on the period's net cash from operating activities.
Every record lists its source URLs. Rows are kept raw (exact label, value) and mapped to model keys in normalize.py."""
import json, os, re, glob, datetime as dt
import xbrl

S = os.environ.get('NFLX_SRC', '/tmp/nflx_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '1065280'

NUM = re.compile(r'^\(?\s*-?(\d[\d,]*)?(\.\d+)?\s*\)?%?$')
def num(s):
    s = s.strip().replace('$', '').replace('%', '').strip()
    if s in ('—', '–', '-', '— —'): return 0.0
    if not NUM.match(s) or not re.search(r'\d', s): return None
    neg = s.startswith('(') or s.endswith(')')
    v = float(s.strip('() ').replace(',', '').replace(' ', ''))
    return -v if neg else v

def parse_row(line):
    parts = [p.strip() for p in line.split(' | ')]
    lab = re.sub(r'\s*\(\d\)\s*$', '', parts[0]).strip().rstrip('*').strip()
    vals = [num(p) for p in parts[1:]]
    if parts[1:] and all(v is None for v in vals): return lab, []
    return lab, [v for v in vals if v is not None]

def url(o, doc):
    return f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{doc}"

def txt_of(o, doc):
    base = f"{o['date']}_{o['form']}_{o['acc']}_{doc}"
    p = os.path.join(S, 'txt', base.rsplit('.', 1)[0] + '.txt')
    return open(p).read().split('\n') if os.path.exists(p) else None

# ---------------------------------------------------------------- statements
def block(lines, first, last, need, skip_last=0, minv=1000, prev=None):
    """rows of the first table that starts at a row matching `first` (with a value >= minv in absolute terms, so percentage
    tables are skipped), ends at a row matching `last` (after `skip_last` earlier matches) and contains a row for every
    pattern in `need` (so selected-data and MD&A tables are skipped)."""
    for i, ln in enumerate(lines):
        if ' | ' not in ln: continue
        lab, vals = parse_row(ln.strip())
        if not re.match(first, lab, re.I): continue
        if prev and not any(re.search(prev, lines[k], re.I) for k in range(max(0, i - 4), i)): continue
        if 'Revenues' in first and (not vals or abs(vals[0]) < minv): continue
        rows, n, done = [], 0, False
        for j in range(i, min(i + 120, len(lines))):
            ln2 = lines[j].strip()
            if not ln2: continue
            lab, vals = parse_row(ln2) if ' | ' in ln2 else (ln2, [])
            rows.append([lab, vals[0] if vals else None, vals])
            if re.match(last, ln2, re.I) and vals:
                if n >= skip_last: done = True; break
                n += 1
        if done and all(any(re.match(p, r[0], re.I) and r[1] is not None for r in rows) for p in need):
            return rows
    return None

def statements(lines):
    is_ = block(lines, r'^(Total )?Revenues$', r'^Diluted', [r'^Operating income', r'^\(?(Provision|Benefit|Income tax)', r'^Net income'], skip_last=1)
    bs = block(lines, r'^Cash and cash equivalents$', r'^Total liabilities and (stockholders|shareholders)', [r'^Total current assets', r'^Total assets'])
    cf = block(lines, r'^Net (income|loss)( \(loss\)| \(income\))?$', r'^Cash(, cash equivalents)?(,| and)? .*end of (the )?(period|year)',
               [r'^Net cash (provided by|used in|\(used in\)).*operating', r'^Net cash.*investing', r'^Net cash.*financing'], prev=r'operating activities')
    return is_, bs, cf

# ---------------------------------------------------------------- segments (2011-2019) and regions (2017+)
def legacy_segments(lines):
    """segment tables (Domestic streaming / International streaming / Domestic DVD) -> {'<kind>-<year>': {row: {segment: value}}},
    kind = 3 / 6 / 9 (months) or Y (year), keyed by the nearest preceding 'As of/ Three months ended ... 2013' style caption."""
    hdr_re = r'Domestic Streaming \| International Streaming \| Domestic DVD'
    out = {}
    for i, ln in enumerate(lines):
        if not re.search(hdr_re, ln, re.I): continue
        cap = next((lines[k] for k in range(i - 1, max(0, i - 4), -1) if re.search(r'(three|six|nine) months ended|year ended', lines[k], re.I)), None)
        if not cap: continue
        m = re.search(r'(three|six|nine) months ended|year ended', cap, re.I)
        kind = {'three': '3', 'six': '6', 'nine': '9'}.get((m.group(1) or '').lower(), 'Y') if m.group(1) else 'Y'
        yr = re.findall(r'(20\d\d)', cap)
        if not yr: continue
        cols = [c.strip() for c in ln.split(' | ')]
        tab = {}
        for j in range(i + 1, i + 14):
            if j >= len(lines): break
            lab, vals = parse_row(lines[j]) if ' | ' in lines[j] else (lines[j], [])
            if re.match(r'^(Total memberships|Paid memberships|Revenues|Cost of revenues|Marketing|Contribution)', lab, re.I) and vals:
                tab[lab] = {cols[k]: vals[k] for k in range(min(len(cols), len(vals)))}
        if any(k.startswith('Revenues') for k in tab): out.setdefault(f'{kind}-{yr[-1]}', tab)
    return out

REG = [('UCAN', r'United States and Canada|^UCAN'), ('EMEA', r'Europe, Middle East|^EMEA'), ('LATAM', r'Latin America|^LATAM'), ('APAC', r'Asia-Pacific|^APAC')]
def regions(lines, col=0):
    """regional tables (revenue note / MD&A): per region the first table after its heading -> revenues, paid net adds, paid memberships,
    average paying memberships, ARM, taking column `col` (0 = current period, 1 = prior-year comparative)."""
    out = {}
    for code, pat in REG:
        for i, ln in enumerate(lines):
            if not re.match(pat, ln.strip()) or ' | ' in ln: continue
            rec = {}
            for j in range(i + 1, min(i + 12, len(lines))):
                if ' | ' not in lines[j]: continue
                lab, vals = parse_row(lines[j])
                if not vals or len(vals) <= col: continue
                l = lab.lower()
                if l.startswith('revenues') or l.startswith('streaming revenues'): rec.setdefault('rev', vals[col])
                elif l.startswith('paid net membership'): rec.setdefault('netadds', vals[col])
                elif l.startswith('paid memberships at end'): rec.setdefault('paid', vals[col])
                elif l.startswith('average paying') or l.startswith('average number of paying'): rec.setdefault('avgpaid', vals[col])
                elif l.startswith('average monthly revenue'): rec.setdefault('arm', vals[col])
            if 'rev' in rec:
                out.setdefault(code, {}).update({k: v for k, v in rec.items() if k not in out.get(code, {})})
                if all(k in out[code] for k in ('rev', 'paid', 'arm')) or len(out[code]) >= 3 and 'arm' in out[code]: break
    return out

def region_revenue_table(lines, col=0):
    """2025+ revenue-by-region table ('United States and Canada (UCAN) | x | y ...' rows)."""
    out = {}
    for ln in lines:
        if ' | ' not in ln: continue
        lab, vals = parse_row(ln)
        for code, pat in REG:
            if re.match(pat, lab) and len(vals) >= 4 and code not in out and '(' in lab:
                out[code] = vals[col]
    return out

def letter_regional(lines):
    """Q4 shareholder-letter 'Regional Breakdown' (in millions; five quarter columns, latest last) -> {region: {arm, paid}} for the latest quarter."""
    out = {}
    for i, ln in enumerate(lines):
        m = re.match(r'^(UCAN|EMEA|LATAM|APAC)( Streaming)?:?\s*$', ln.strip())
        if not m: continue
        code = m.group(1)
        for j in range(i + 1, min(i + 8, len(lines))):
            if ' | ' not in lines[j]: continue
            lab, vals = parse_row(lines[j])
            if not vals: continue
            if re.match(r'^(Average Revenue per Membership|ARPU|Average monthly revenue)', lab, re.I): out.setdefault(code, {}).setdefault('arm', vals[-1])
            if re.match(r'^Paid Memberships', lab, re.I): out.setdefault(code, {}).setdefault('paid_m', vals[-1])
    return out

# ---------------------------------------------------------------- published free cash flow (letters / releases)
def fcf_tables(lines):
    """every FCF reconciliation in a release -> list of {label: [values]}."""
    out = []
    for i, ln in enumerate(lines):
        if not re.search(r'free cash flow reconciliation|reconciliation of free cash flow', ln, re.I): continue
        tab = {}
        for j in range(i + 1, min(i + 16, len(lines))):
            if ' | ' not in lines[j]: continue
            lab, vals = parse_row(lines[j])
            if not vals: continue
            tab[lab] = vals
            if re.match(r'^(Non-GAAP )?free cash flow', lab, re.I): break
        if tab: out.append(tab)
    return out

def ngaap_tables(lines, title):
    """non-GAAP reconciliations (Adjusted EBITDA, non-GAAP net income) -> list of {label: [values]} (values by column)."""
    out = []
    for i, ln in enumerate(lines):
        if not re.search(title, ln, re.I): continue
        tab = {}
        for j in range(i + 1, min(i + 14, len(lines))):
            if ' | ' not in lines[j]: continue
            lab, vals = parse_row(lines[j])
            if not vals: continue
            if lab in tab: break
            tab[lab] = vals
            if re.match(r'^Adjusted EBITDA$', lab, re.I): break
        if tab: out.append(tab)
    return out

def pick_fcf(tables, cfo):
    """the column whose net cash from operating activities equals the period's CFO (thousands, ±1)."""
    for tab in tables:
        cl = next((v for k, v in tab.items() if re.match(r'^Net cash provided by', k, re.I)), None)
        fl = next((v for k, v in tab.items() if re.match(r'^(Non-GAAP )?free cash flow', k, re.I)), None)
        if not cl or not fl: continue
        for k, c in enumerate(cl):
            if abs(c - cfo) <= 1.5 and k < len(fl):
                comps = {lab: vals[k] for lab, vals in tab.items() if k < len(vals)}
                return {'fcf': fl[k], 'items': comps, 'col': k}
    return None

# ---------------------------------------------------------------- filings
def load_filings():
    F = json.load(open(os.path.join(S, 'filings.json')))
    per = {}
    rel = []
    for o in F:
        if o['form'] in ('10-K', '10-Q'):
            per[o['report']] = o
        elif o['form'] == '8-K' and '2.02' in o['items']:
            rel.append(o)
    return per, rel

def qend(y, q): return dt.date(y, 3 * q, 31 if q in (1, 4) else 30).isoformat()

def release_for(rel, end):
    """earnings release / shareholder letter for the quarter ended `end`: first 2.02 8-K filed 1-75 days after the quarter end."""
    e = dt.date.fromisoformat(end)
    best = None
    for o in rel:                       # latest Item 2.02 filing within 60 days (skips e.g. the 3-Jan-2019 reclassification 8-K)
        d = dt.date.fromisoformat(o['date'])
        if 1 <= (d - e).days <= 60: best = o
    if best is None: return None, []
    return best, [x for x in best['files'] if x != best['primary']] or [best['primary']]

def release_lines(o, docs):
    L = []
    for d in docs:
        t = txt_of(o, d)
        if t: L += t
    return L

def run():
    per, rel = load_filings()
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for end, o in sorted(per.items()):
        e = dt.date.fromisoformat(end)
        y, q = e.year, (e.month - 1) // 3 + 1
        if y < 2006 or (o['form'] == '10-Q' and y < 2013): continue      # quarterly history starts Q1/13
        key = str(y) if o['form'] == '10-K' else f'Q{q}-{str(y)[2:]}'
        lines = txt_of(o, o['primary'])
        is_, bs, cf = statements(lines)
        rec = {'period': key, 'period_end': end, 'form': o['form'], 'filed': o['date'],
               'sources': {'filing': url(o, o['primary'])}, 'is_rows': is_, 'bs_rows': bs, 'cf_rows': cf, 'notes': []}
        if cf is None: rec['notes'].append('cash-flow statement not found')
        # legacy segments
        if 2011 <= y <= 2019:
            rec['seg_tables'] = legacy_segments(lines)
        # regions
        if y >= 2019 or (o['form'] == '10-K' and y >= 2019):
            r = regions(lines, 0)
            if r: rec['reg'] = r
            if y >= 2020 and o['form'] == '10-Q':
                rec['reg_py'] = regions(lines, 1)        # prior-year quarter (2019 quarters for the 2020 10-Qs)
                if q == 3:
                    rec['reg_9m'] = regions(lines, 2); rec['reg_9m_py'] = regions(lines, 3)
            if y >= 2025:
                rr = region_revenue_table(lines, 0)
                if rr:
                    for k, v in rr.items(): rec.setdefault('reg', {}).setdefault(k, {})['rev'] = v
                if q == 3 and o['form'] == '10-Q':
                    for k, v in region_revenue_table(lines, 2).items(): rec.setdefault('reg_9m', {}).setdefault(k, {})['rev'] = v
            if o['form'] == '10-K' and y == 2019:
                rec['reg_2018'] = regions(lines, 1); rec['reg_2017'] = regions(lines, 2)
        # release: published FCF, regional ARM for Q4
        ro, docs = release_for(rel, end)
        if ro:
            rl = release_lines(ro, docs)
            rec['sources']['release'] = [url(ro, d) for d in docs]
            rec['fcf_tables'] = fcf_tables(rl)
            rec['ebitda_tables'] = ngaap_tables(rl, r'Adjusted EBITDA reconciliation')
            rec['ngni_tables'] = ngaap_tables(rl, r'Non-GAAP net income reconciliation')
            if q == 4:
                rec['letter_reg'] = letter_regional(rl)
                rec['release_is'] = statements(rl)[0]       # Q4 three-month column (EPS, shares), matched on revenue in normalize.py
            rec['_release_text_file'] = f"{ro['date']}_{ro['form']}_{ro['acc']}"
        index[key] = rec
    for key, rec in index.items():
        json.dump(rec, open(os.path.join(OUT, f'{key}.json'), 'w'), indent=1)
    print(len(index), 'periods written')

if __name__ == '__main__':
    run()
