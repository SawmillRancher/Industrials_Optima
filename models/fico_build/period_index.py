"""Map each model period (FY2006-FY2025 annual; Q1-13 ... Q3-26 quarterly) to its source documents in $FICO_SRC/txt:
the earnings release (8-K Item 2.02, Ex. 99.1) and the periodic report (10-Q, or 10-K for annual / Q4). Writes
$FICO_SRC/period_index.json. Fiscal year N = October N-1 to September N."""
import json, os, glob, re
S = os.environ.get('FICO_SRC', '/tmp/fico_src')
F = json.load(open(os.path.join(S, 'filings.json')))

def txt(o, doc):
    p = os.path.join(S, 'txt', f"{o['date']}_{o['form']}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
    return p if os.path.exists(p) else None

def html(o, doc):
    p = os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{doc}")
    return p if os.path.exists(p) else None

def url(o, doc): return f"https://www.sec.gov/Archives/edgar/data/814547/{o['acc'].replace('-', '')}/{doc}"

def fyq_of_end(end):
    y, m = int(end[:4]), int(end[5:7])
    return (y + (1 if m >= 10 else 0)), {12: 1, 3: 2, 6: 3, 9: 4}[m]

def run():
    idx = {}
    for o in F:
        if o['form'] in ('10-K', '10-Q') and o['report']:
            fy, q = fyq_of_end(o['report'])
            k = str(fy) if o['form'] == '10-K' else f'Q{q}-{str(fy)[2:]}'
            idx.setdefault(k, {})['filing'] = txt(o, o['primary']); idx[k]['filing_url'] = url(o, o['primary']); idx[k]['filing_date'] = o['date']; idx[k]['filing_html'] = html(o, o['primary'])
        if o['form'] == '8-K' and '2.02' in o['items']:
            ex = [x for x in o['files'] if x != o['primary'] and re.search(r'exv?[-_]?99|99[-_]?1|exhibit99', x.lower())] or [o['primary']]
            d = o['date']; y, m = int(d[:4]), int(d[5:7])
            if m in (1, 2): fy, q = y, 1
            elif m in (4, 5): fy, q = y, 2
            elif m in (7, 8): fy, q = y, 3
            elif m in (10, 11, 12): fy, q = y, 4
            else: continue
            k = f'Q{q}-{str(fy)[2:]}'
            # preliminary announcements (16-Apr-2007, 14-Jan-2008, 15-Oct-2013) precede the full release: the latest 2.02 8-K wins
            idx.setdefault(k, {})['release'] = txt(o, ex[0]); idx[k]['release_url'] = url(o, ex[0]); idx[k]['release_date'] = d; idx[k]['release_html'] = html(o, ex[0])
            if q == 4:
                idx.setdefault(str(fy), {})['release'] = idx[k]['release']; idx[str(fy)]['release_url'] = idx[k]['release_url']; idx[str(fy)]['release_date'] = d; idx[str(fy)]['release_html'] = idx[k]['release_html']
    json.dump(idx, open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
    return idx

if __name__ == '__main__':
    idx = run()
    for k in sorted(idx, key=lambda k: (int('20' + k[-2:]) if '-' in k else int(k), 0 if '-' in k else 1, k)):
        v = idx[k]; print(k, v.get('release_date'), bool(v.get('release')), v.get('filing_date'), bool(v.get('filing')))
