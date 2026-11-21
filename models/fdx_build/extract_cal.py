"""Calendar-basis extraction (years ended 31 December; FedEx Freight in discontinued operations; Express U.S. Domestic and Express
International segments) from:
  - 8-K 21-Jul-2026 Ex. 99.1 'Supplemental Historical Financial Information': calendar 2024 and 2025, years and quarters
    (income statements, segment statements, operating statistics, capital expenditures, balance sheets at 31-Dec, non-GAAP tables);
  - 8-K 28-Oct-2026 Ex. 99.1 (recast): calendar quarters ended 31-Mar-2026 and 30-Jun-2026;
  - 8-K 28-Oct-2026 Ex. 99.1 (earnings release): quarter and nine months ended 30-Sep-2026 (and 2025), balance sheet at 30-Sep-2026,
    nine-month cash flow (not recast for discontinued operations), calendar 2026 outlook.
Writes data/CQ<n>-<yy>.json, data/CY<yyyy>.json and data/C9M-<yy>.json with the same row format as extract.py."""
import json, os, re
import parse_release as pr
import extract as ex

QN = {'FIRST': 1, 'SECOND': 2, 'THIRD': 3, 'FOURTH': 4}
SECS = ('is', 'usd', 'intl', 'bs', 'capex')

def find(date, pat):
    for o in ex.FIL:
        if o['date'] == date and o['form'] == '8-K':
            for w in o['files']:
                if re.search(pat, w): return o, w
    raise KeyError((date, pat))

def columns(e):
    """yield (entry, [period keys of its value cells]) for the recast exhibits, whose tables are headed by a year line and a
    'FIRST QUARTER | SECOND QUARTER ...' row (quarters) or a '2025 | 2024' row (years / year ends)."""
    cols = None
    for x in e:
        lab = x['label'].upper()
        if lab.startswith('FIRST QUARTER'):
            yr = [c for c in x['ctx'] if re.fullmatch(r'20\d\d', c.strip())]
            y = yr[-1].strip()[2:]
            n = 1 + len(x['cells'])
            cols = [f'CQ{i}-{y}' for i in range(1, n + 1)]; continue
        if x['label'] == '' and len(x['vals']) == 2 and all(v in (2024.0, 2025.0, 2026.0) for v in x['vals']):
            cols = [f'CY{int(v)}' for v in x['vals']]; continue
        if cols and x['label'] and any(v is not None for v in x['vals']):
            yield x, cols

def recon(e, rec_of):
    cur = None
    for b in pr_blocks(e):
        h = b['head'].upper()
        m = re.search(r'(FIRST|SECOND|THIRD|FOURTH) QUARTER CALENDAR (20\d\d)', h)
        if m: cur = f'CQ{QN[m.group(1)]}-{m.group(2)[2:]}'
        m = re.search(r'FULL YEAR CALENDAR (20\d\d)', h)
        if m: cur = f'CY{m.group(1)}'
        m = re.search(r'THREE MONTHS ENDED SEPTEMBER 30, (20\d\d)', h)
        if m: cur = f'CQ3-{m.group(1)[2:]}'
        if cur is None or cur not in rec_of: continue
        ent = 'usd' if 'U.S. DOMESTIC' in h else 'intl' if 'INTERNATIONAL SEGMENT' in h else 'corp'
        rec_of[cur].setdefault('recon', []).append({'entity': ent, 'head': b['head'], 'rows': b['rows']})

def pr_blocks(e):
    out, cur = [], None
    for x in e:
        lab = x['label'].lower()
        isg = re.match(r'^(gaap|non-gaap) measure', lab)
        if isg and cur is None:
            cur = {'head': ' / '.join(x['ctx']), 'rows': []}; out.append(cur)
        if cur is not None:
            cur['rows'].append([x['label'], x['vals']])
            if isg and len(cur['rows']) > 1: cur = None
    return out

def run():
    recs = {}
    def rec(k, src):
        r = recs.setdefault(k, {'period': k, 'basis': 'calendar (year ended 31 December; FedEx Freight in discontinued operations; '
                                'Express U.S. Domestic / Express International segments)', 'sources': [], 'notes': []})
        if src not in r['sources']: r['sources'].append(src)
        return r
    for date, pat in (('2026-07-21', 'recast'), ('2026-10-28', 'recast')):
        o, w = find(date, pat); src = ex.url(o, w)
        e = pr.parse(open(ex.txt(o, w)).read())
        for x, cols in columns(e):
            if x['sec'] not in SECS: continue
            g = x['ctx'][-1] if x['ctx'] else ''
            for k, v in zip(cols, x['vals']):
                if v is None: continue
                rec(k, src).setdefault(x['sec'], []).append([g, x['label'], v])
        for k in list(recs): rec(k, src)
        recon(e, recs)
    # third-quarter release
    o, w = find('2026-10-28', 'earningsrelease'); src = ex.url(o, w)
    e = pr.parse(open(ex.txt(o, w)).read())
    q3, n9, p9 = rec('CQ3-26', src), rec('C9M-26', src), rec('C9M-25', src)
    for s in ('is', 'usd', 'intl'):
        for g, l, a, b, c, d in ex.rows(e, s, False):
            if a is not None: q3.setdefault(s, []).append([g, l, a])
            if c is not None: n9.setdefault(s, []).append([g, l, c])
            if d is not None: p9.setdefault(s, []).append([g, l, d])
            if b is not None: q3.setdefault('py', {}).setdefault(s, []).append([g, l, b])
    q3['bs'] = [[g, l, a] for g, l, a, b in ex.rows(e, 'bs', True, two=True) if a is not None]
    for g, l, a, b in ex.rows(e, 'cf', True, two=True):
        if a is not None: n9.setdefault('cf', []).append([g, l, a])
        if b is not None: p9.setdefault('cf', []).append([g, l, b])
    n9['cf_ytd_months'] = p9['cf_ytd_months'] = 9
    n9['notes'].append('Nine-month cash flow statement as presented: not recast for discontinued operations (includes FedEx Freight to 31-May-2026).')
    p9['notes'].append('Prior-year nine-month column of the 28-Oct-2026 release; cash flow not recast for discontinued operations.')
    recon(e, recs)
    for k, r in recs.items(): ex.save(k, r)
    print('calendar records', sorted(recs))

if __name__ == '__main__':
    run()
