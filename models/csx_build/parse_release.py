"""Parse a CSX earnings release / Quarterly Financial Report (8-K Item 2.02, Ex. 99.1 / 99.2 HTML) into typed tables.

Every release since Q4 2006 prints the same family of schedules (consolidated income statement, condensed balance sheet,
condensed cash-flow statement (year to date), volume / revenue / revenue-per-unit by market, fuel expense, employee counts,
coal tonnage, operating statistics, and - when there are special items - a "comparable" / "adjusted" reconciliation), but
titles, layouts and column order vary by era:
  2006-07  Ex. 99.2 with ")" in separate cells (dropped), section captions in a leading cell ("Assets | Cash ...")
  2008-19  Ex. 99.2 "qfr" with line breaks inside cells (collapsed here)
  2020-26  inline-XBRL style HTML, "Fav / (Unfav) | % Change" columns, "NM" tokens
Tables are identified by their contents and returned as {'type', 'hdr', 'rows': [(label, [values or None])]} where values keep
their column position (non-numeric tokens such as "NM" become None, "—" / "-" become 0.0). Amounts stay in the release units
(USD millions; volumes in thousands of units; per share in $; revenue per unit in $).
"""
import re
from bs4 import BeautifulSoup

DASH = {'—', '–', '-', '―', '--', '— —', '—-'}

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace('\xa0', ' ').strip()
    t = re.sub(r'\s+', '', t)
    if t in DASH: return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('​', ' ')).strip()

NUMTOK = re.compile(r'^\(?\$?\s*-?[\d,]*\.?\d+\)?%?$|^[—–\-]+%?$|^NM$|^N/?M$|^n/?m$|^\(?[\d,]*\.?\d+\)%?$', re.I)

def html_tables(html):
    """-> list of raw tables: [{'hdr': [header text rows], 'rows': [(label, [values])]}]"""
    soup = BeautifulSoup(html, 'lxml')
    for t in soup(['script', 'style']): t.decompose()
    out = []
    for t in soup.find_all('table'):
        if t.find('table'): continue                      # nested layout tables: take the innermost only
        cur = {'hdr': [], 'rows': []}
        for tr in t.find_all('tr'):
            cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
            cells = [c for c in cells if c not in ('', '$', ')', '%', ')%', '(', '$ (')]
            if not cells: continue
            # split into leading label cells and value tokens (everything from the first numeric-looking cell on)
            i = 0
            while i < len(cells) and not (NUMTOK.match(cells[i].replace(' ', '')) and not re.fullmatch(r'(19|20)\d\d', cells[i])): i += 1
            labs, toks = cells[:i], cells[i:]
            if labs and toks and all(re.fullmatch(r'(19|20)\d\d', x) for x in cells[i:] if re.fullmatch(r'\d{4}', x)) and \
               all(re.fullmatch(r'(19|20)\d\d|%?\s*change|improvement|\(decline\)|\$', x, re.I) for x in toks):
                labs, toks = cells, []           # a year / header row with a leading caption
            toks = [x for x in toks if not re.fullmatch(r'[%$]|\)%|\(', x)]
            isyear = toks and all(re.fullmatch(r'(19|20)\d\d', x) for x in toks)
            if toks and labs and not isyear:
                cur['rows'].append((' '.join(labs), [pnum(x) for x in toks]))
            elif toks and not labs and not isyear and cur['rows']:
                cur['rows'].append(('', [pnum(x) for x in toks]))
            else:
                line = ' | '.join(cells)
                if cur['rows']: cur['rows'].append((line, []))
                else: cur['hdr'].append(line)
        if cur['rows']: out.append(cur)
    return out

def ttype(t):
    labs = ' || '.join(l.lower() for l, _ in t['rows'])
    hdr = ' '.join(t['hdr']).lower()
    if 'free cash flow' in labs: return 'fcf'
    if 'labor and fringe' in labs and re.search(r'(^|\|\| )(surface (transportation )?)?revenue', labs) and 'net earnings' in labs and 'volume' not in hdr:
        if 'rail' in hdr and 'intermodal' in hdr: return 'seg'
        return 'is'
    if 'labor and fringe' in labs and re.search(r'(^|\|\| )revenue', labs) and 'rail' in hdr: return 'seg'
    if 'total assets' in labs: return 'bs'
    if 'net cash provided by operating activities' in labs and ('property additions' in labs or 'investing' in labs): return 'cf'
    if ('total merchandise' in labs or 'chemicals' in labs) and ('intermodal' in labs or 'coal' in labs) and re.search(r'(^|\|\| )total( \|\|)?', labs) and 'ton' not in hdr: return 'vol'
    if 'price per gallon' in labs or 'locomotive fuel' in labs: return 'fuel'
    if 'fuel surcharge revenue' in labs: return 'fsc'
    if re.search(r'gaap operating results|comparable|adjusted operating (income|results)|restructuring charge|debt repurchase expense after tax|income tax benefit', labs) and 'labor and fringe' not in labs: return 'adj'
    if re.search(r'(^|\|\| )(total )?coal( tonnage)?', labs) and ('domestic' in labs or 'utility' in labs) and 'revenue' not in labs: return 'coal'
    if 'gross ton-miles' in labs or 'revenue ton-miles' in labs or 'train velocity' in labs: return 'stats'
    if re.search(r'(^|\|\| )rail( \(a\))?( \|\|)', labs) and re.search(r'(^|\|\| )total( \|\|)', labs) and ('trucking' in labs or 'corporate' in labs or 'intermodal' in labs) and 'revenue' not in labs: return 'emp'
    if 'economic profit' in labs or 'gross cash earnings' in labs: return 'ep'
    if 'interest income' in labs and 'real estate' in labs: return 'othinc'
    return None

def parse(html):
    res = []
    for t in html_tables(html):
        ty = ttype(t)
        if ty: res.append(dict(t, type=ty))
    return res

def years_in(t):
    """years listed in the header rows (and in a leading year-only row), in order."""
    h = ' '.join(t['hdr'])
    return [int(y) for y in re.findall(r'(?<!\d)((?:19|20)\d\d)(?!\d)', h)]

def row(t, label_re, nth=0, exclude=None):
    hits = 0
    for lab, vals in t['rows']:
        if not vals: continue
        if re.search(label_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
            if hits == nth: return lab, vals
            hits += 1
    return None, None

if __name__ == '__main__':
    import sys, json
    for t in parse(open(sys.argv[1], 'rb').read()):
        print('=====', t['type'], years_in(t), t['hdr'][:4])
        for l, v in t['rows'][:60]:
            print('  ', l[:60], v)
