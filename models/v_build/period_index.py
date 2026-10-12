"""Period index ($V_SRC/period_index.json): fiscal period key -> earnings release (8-K Item 2.02 Ex. 99.1), 10-Q / 10-K, and the
same documents one year later (comparatives). Also writes the hidden text layer of the image-based releases (Q1 FY2018 - Q2 FY2021,
Workiva slide exhibits whose tables are images with a white 1-pt text layer) to $V_SRC/txt_hidden/<release>.txt.
Fiscal year ends 30 September: FY2026 = Oct-2025 - Sep-2026; Q1 = Oct-Dec."""
import json, os, re, html, datetime as dt
S = os.environ.get('V_SRC', '/tmp/v_src')
F = json.load(open(os.path.join(S, 'filings.json')))
CIK = '1403161'

def fyq(d):
    d = dt.date.fromisoformat(d)
    fy = d.year + (1 if d.month >= 10 else 0)
    q = {12: 1, 1: 1, 3: 2, 4: 2, 6: 3, 7: 3, 9: 4, 10: 4}[d.month]
    return fy, q

def url(o, doc): return f"https://www.sec.gov/Archives/edgar/data/{CIK}/{o['acc'].replace('-', '')}/{doc}"

def release_doc(o):
    c = [x for x in o['files'] if x != o['primary'] and not re.search(r'deck|pres(?!srelease)|ex992|ex993|dex99[23]', x.lower())]
    c = [x for x in c if re.search(r'99|release', x.lower())]
    return c[0] if c else None

def hidden_text(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    parts = re.findall(r'<FONT size="1" style="font-size:1pt;color:white">(.*?)</FONT>', s, re.S | re.I)
    return '\n\n=== PAGE ===\n'.join(html.unescape(re.sub(r'<[^>]+>', ' ', p)) for p in parts)

idx = {}
for o in F:
    if o['form'] in ('10-K', '10-Q') and o['report']:
        fy, q = fyq(o['report'])
        key = str(fy) if o['form'] == '10-K' else f'Q{q}-{str(fy)[2:]}'
        idx.setdefault(key, {})['filing'] = url(o, o['primary'])
        idx[key]['filing_txt'] = f"{o['date']}_{o['form']}_{o['acc']}_{o['primary'].rsplit('.', 1)[0]}.txt"
        idx[key]['filing_date'] = o['date']
    if o['form'] == '8-K' and '2.02' in o['items']:
        doc = release_doc(o)
        if not doc: continue
        d = dt.date.fromisoformat(o['date'])
        # release for the quarter ended in the month before the filing month (Jan->Dec Q1, Apr->Mar Q2, Jul->Jun Q3, Oct/Nov->Sep Q4)
        pe = {1: (12, -1), 2: (12, -1), 4: (3, 0), 5: (3, 0), 7: (6, 0), 8: (6, 0), 10: (9, 0), 11: (9, 0)}[d.month]
        fy, q = fyq(f'{d.year + pe[1]}-{pe[0]:02d}-28')
        rec = dict(release=url(o, doc), release_date=o['date'], release_txt=f"{o['date']}_8-K_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
        hp = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
        if os.path.exists(hp):
            t = hidden_text(hp)
            if len(t) > 2000:
                hn = f"{o['date']}_{doc.rsplit('.', 1)[0]}_hidden.txt"
                open(os.path.join(S, 'txt_hidden', hn), 'w').write(t); rec['release_hidden_txt'] = hn
        k = f'Q{q}-{str(fy)[2:]}'
        idx.setdefault(k, {}).update(rec)
        if q == 4: idx.setdefault(str(fy), {}).update(rec)
for k, v in idx.items():
    if k.startswith('Q'):
        nk = f'Q{k[1]}-{int(k[3:]) + 1:02d}'
    else:
        nk = str(int(k) + 1)
    if nk in idx:
        v['next_release'] = idx[nk].get('release'); v['next_filing'] = idx[nk].get('filing')
json.dump(dict(sorted(idx.items())), open(os.path.join(S, 'period_index.json'), 'w'), indent=1)
print(len(idx), 'periods')
