"""Google / Alphabet earnings releases (Form 8-K Item 2.02, Ex. 99.1) -> per-quarter release data:
  * Q4 three-month diluted EPS (and basic), net income and revenues (cross-check of the 10-K - 9M derivation);
  * free cash flow (company definition: net cash provided by operating activities less purchases of property and equipment);
  * total TAC and number of employees (period end);
  * Google Inc. non-GAAP results (published to the Q4-2014 release): non-GAAP operating income and net income / EPS
    (exclude stock-based compensation net of tax, discontinued operations and, as applicable, other special items).
Values as published (USD millions; per-share pre-split as filed; Google-era releases in thousands are converted)."""
import json, os, re, glob, datetime as dt
S = os.environ.get('GOOG_SRC', '/tmp/goog_src')

def nums(line):
    out = []
    for c in line.split(' | ')[1:]:
        c = c.strip().replace('$', '').strip()
        if c in ('—', '-', '— %'): out.append(0.0); continue
        m = re.fullmatch(r'\(?([\d,]+(?:\.\d+)?)\)?', c)
        if m: out.append((-1 if c.startswith('(') else 1) * float(m.group(1).replace(',', '')))
    return out

def quarter_of(filed):
    d = dt.date.fromisoformat(filed)
    m = (d.month - 1) // 3 * 3          # releases come out within ~6 weeks of the quarter end
    if m == 0: return d.year - 1, 4
    return d.year, m // 3

def releases():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    out = []
    for o in fl:
        if o['form'] != '8-K' or '2.02' not in o['items']: continue
        ex = [x for x in o['files'] if re.search(r'ex-?99|exhibit99|ex99|dex99|exhibit991', x.lower())]
        if not ex: continue
        p = glob.glob(os.path.join(S, 'txt', f"{o['date']}_8-K_{o['acc']}_{ex[0].rsplit('.', 1)[0]}.txt"))
        if not p: continue
        y, q = quarter_of(o['date'])
        out.append(dict(y=y, q=q, file=p[0], url=f"https://www.sec.gov/Archives/edgar/data/{o['cik']}/{o['acc'].replace('-', '')}/{ex[0]}", filed=o['date']))
    return out

def first_row(lines, rx, n=None):
    for l in lines:
        lab = l.split(' | ')[0].strip()
        if re.search(rx, lab):
            v = nums(l)
            if n is None or len(v) == n: return v
    return None

def parse(rel):
    t = open(rel['file']).read().split('\n')
    low = [l.lower() for l in t]
    k1000 = any('in thousands, except per share' in l or 'in thousands)' in l for l in low) and not any('in millions' in l for l in low)
    sc = 1e-3 if k1000 else 1.0
    r = {'url': rel['url'], 'filed': rel['filed']}
    v = first_row(t, r'^Revenues$', 4)
    if v: r['rev_q'] = v[1] * sc; r['rev_fy'] = v[3] * sc
    v = first_row(t, r'^Net income$', 4)
    if v: r['ni_q'] = v[1] * sc
    v = first_row(t, r'^(Diluted net income per share|Diluted earnings per share|Net income \(loss\) per share - diluted|Net income per share - diluted)', 4)
    if v: r['eps_d_q'] = v[1]
    v = first_row(t, r'^(Basic net income per share|Basic earnings per share|Net income \(loss\) per share - basic|Net income per share - basic)', 4)
    if v: r['eps_b_q'] = v[1]
    for l in t:
        if l.startswith('Free cash flow |'):
            v = nums(l)
            if v: r['fcf_q'] = (v[-2] if len(v) == 5 else v[-1]) * sc; break     # 2025+: four quarters + trailing twelve months
    v = first_row(t, r'^Total TAC$')
    if v: r['tac_q'] = v[1] * sc if len(v) >= 2 else v[0] * sc
    v = first_row(t, r'^Number of employees')
    if v: r['employees'] = v[1] if len(v) >= 2 else v[0]
    # Google Inc. non-GAAP reconciliation (current quarter = the second group of columns)
    for i, l in enumerate(t):
        if l.startswith('Income from operations |') and i > 0 and any('Non-GAAP' in x for x in t[max(0, i - 6):i]):
            v = nums(l)
            if len(v) >= 10: r['ng_oi_q'] = v[8] * sc; r['ng_sbc_q'] = v[7] * sc
        if l.startswith('Net income |') and any('Non-GAAP' in x or 'non-GAAP' in x for x in t[max(0, i - 14):i]) and 'ng_oi_q' in r and 'ng_ni_q' not in r:
            v = nums(l)
            if len(v) >= 6: r['ng_ni_q'] = v[-1] * sc; r['ni_q_ng_table'] = v[-3] * sc
        if l.startswith('Net income per share - diluted |') and 'ng_oi_q' in r and 'ng_eps_q' not in r:
            v = nums(l)
            if len(v) == 4: r['ng_eps_q'] = v[3]; r['eps_d_q_ng_table'] = v[2]
    return r

def run():
    return {f"Q{r['q']}-{str(r['y'])[2:]}": parse(r) for r in releases() if r['y'] >= 2012}

if __name__ == '__main__':
    for k, v in run().items(): print(k, {a: b for a, b in v.items() if a not in ('url', 'filed')})
