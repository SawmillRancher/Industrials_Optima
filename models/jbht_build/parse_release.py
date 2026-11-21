"""Parse a J.B. Hunt earnings release (8-K Item 2.02, Ex. 99.1 HTML) into typed sections.

Every release since 2006 prints the same schedules: condensed statements of earnings (three months; plus six / nine / twelve
months), financial information by segment (revenue and operating income), operating statistics by segment, condensed balance
sheets and supplemental data (shares outstanding, book value, and in later years year-to-date cash-flow items).

parse(html) -> list of sections {'type': 'is'|'seg'|'stat'|'bs'|'sup', 'months': 3|6|9|12|0, 'rows': [(group, label, [numbers])]}
  group = the last sub-heading without numbers (e.g. 'Revenue' / 'Operating income' in the segment table; the segment name in
  the statistics table).
Column convention (cur(), py()): statements and segment tables print Amount | % | Amount | % (4 numbers -> [0], [2]);
statistics, balance sheets and supplemental data print current | prior (2 numbers -> [0], [1]).
Values: '(1,234' / '(1,234)' -> -1234; '-', '—', '–' -> 0.0. Amounts stay in the release units (thousands; per share in $).
"""
import re
from bs4 import BeautifulSoup

def pnum(tok):
    t = tok.strip().replace('$', '').replace('%', '').replace('​', '').replace(' ', '').strip()
    if t in ('—', '–', '-', '―', '--'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '')
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def _clean(s):
    s = re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('\u200b', ' ')).strip()
    return re.sub(r'([a-z]{3,}) ([a-z])$', r'\1\2', s)        # filing artifact: last letter split off ('revenue s', 'transportatio n')

def lines(html):
    """document order: one entry per table row ([cells]) or text block ([text])."""
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style']): t.decompose()
    for tr in s.find_all('tr'):
        cells = [_clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td', 'th'])]
        cells = [c for c in cells if c not in ('', '$', ')', '%', ')%', '%)')]
        tr.replace_with('\x01' + '\x02'.join(cells) + '\n')
    out = []
    for ln in s.get_text('\n').split('\n'):
        if ln.startswith('\x01'):
            cells = [c for c in ln[1:].split('\x02') if c]
            if cells: out.append(cells)
        elif _clean(ln):
            out.append([_clean(ln)])
    return out

# headings are matched with all whitespace removed (some filings split words: 'Balance Sheet s', 'Supplemental Dat a', 'December 3 1')
HEAD = [('is', r'statements?ofearnings'), ('seg', r'financialinformationbysegment'), ('stat', r'operatingstatisticsbysegment'),
        ('bs', r'condensedconsolidatedbalancesheets?'), ('sup', r'^supplemental(data)?(\(unaudited\))?$'), ('cf', r'statements?ofcashflows')]
MONTHS = {'three': 3, 'six': 6, 'nine': 9, 'twelve': 12}

def parse(html):
    secs, cur = [], None
    for cells in lines(html):
        joined = ' '.join(cells); low = joined.lower(); tight = re.sub(r'\s', '', low)
        ty = next((k for k, p in HEAD if re.search(p, tight)), None) if len(joined) < 170 else None
        if ty:
            cur = {'type': ty, 'months': 0, 'rows': [], 'group': ''}; secs.append(cur); continue
        m = re.search(r'(three|six|nine|twelve)monthsended', tight)
        if m and len(joined) < 80 and cur is None:          # statement of earnings without its heading row
            cur = {'type': 'is', 'months': 0, 'rows': [], 'group': ''}; secs.append(cur)
        if cur is None: continue
        if m and len(joined) < 80:
            mo = MONTHS[m.group(1)]
            if cur['rows']:                      # a second period block inside the same schedule
                cur = {'type': cur['type'], 'months': mo, 'rows': [], 'group': ''}; secs.append(cur)
            else: cur['months'] = mo
            continue
        nums = [pnum(c) for c in cells[1:]]
        if len(cells) >= 2 and all(n is not None for n in nums) and pnum(cells[0]) is None:
            if all(n == int(n) and 1990 <= n <= 2035 for n in nums) and ',' not in ''.join(cells[1:]): continue      # year header
            cur['rows'].append((cur['group'], cells[0], nums))
        elif len(cells) >= 2 and all(pnum(c) is not None for c in cells) and cur['type'] == 'bs' and cur['rows']:
            cur['rows'].append((cur['group'], '__total__', [pnum(c) for c in cells]))           # unlabeled balance-sheet totals
        elif len(cells) == 1 and pnum(cells[0]) is None and len(joined) < 120:
            if re.match(r'^[\*\(]', joined) or re.fullmatch(r'\d+', joined): continue
            cur['group'] = joined
    return _retype([s for s in secs if s['rows']])

def _retype(secs):
    """Some releases (FY2006, FY2008 ...) omit the schedule headings: split and type the sections by their contents."""
    out = []
    for s in secs:
        parts, curp = [], None
        for row in s['rows']:
            lab = row[1].lower()
            start = None
            if re.match(r'cash and (cash )?equivalents', lab) and s['type'] != 'bs': start = 'bs'
            elif lab.startswith('actual shares outstanding') and s['type'] != 'sup': start = 'sup'
            if start or curp is None:
                curp = {'type': start or s['type'], 'months': 0 if start else s['months'], 'rows': []}; parts.append(curp)
            curp['rows'].append(row)
        for p in parts:
            labs = ' || '.join(r[1].lower() for r in p['rows'])
            if p['type'] in ('is', 'seg', 'stat'):
                if 'total operating revenues' in labs: p['type'] = 'is'
                elif 'intersegment eliminations' in labs: p['type'] = 'seg'
                elif 'loads' in labs: p['type'] = 'stat'
            out.append(p)
    return out

def cur(nums):
    return nums[0] if nums else None
def py(nums):
    if len(nums) == 2: return nums[1]
    if len(nums) == 4: return nums[2]
    if len(nums) == 3: return None
    return None

def find(secs, ty, months, label_re, group_re=None, nth=0, exclude=None):
    """-> numbers of the nth row matching label_re (and group_re) in sections of type ty / months."""
    k = 0
    for s in secs:
        if s['type'] != ty or (months is not None and s['months'] != months): continue
        for g, lab, nums in s['rows']:
            if re.search(label_re, lab, re.I) and (group_re is None or re.search(group_re, g, re.I)) and not (exclude and re.search(exclude, lab, re.I)):
                if k == nth: return nums
                k += 1
    return None

if __name__ == '__main__':
    import sys
    for s in parse(open(sys.argv[1], 'rb').read()):
        print('==', s['type'], s['months'])
        for r in s['rows']: print('   ', r)
