"""Union Pacific earnings-release parser (Form 8-K Item 2.02, Ex. 99.1; text from h2t.py).

Handles every release format since January 2006:
  2006-08  "STATEMENTS OF CONSOLIDATED INCOME" / "REVENUE DETAIL" (commodity revenue in $000, carloads in units), six legacy opex lines
  2008-    "Condensed Consolidated Statements of Income" with freight / other revenues and the current six expense lines
  2006-17  six business groups (Agricultural, Automotive, Chemicals, Energy / Coal, Industrial Products, Intermodal)
  2018     four groups (Agricultural Products, Energy, Industrial, Premium); 2019+ three groups (Bulk, Industrial, Premium),
           with ten commodity sub-lines from the Q1-2020 release
  2018+    "Financial Performance" non-GAAP tables (adjusted operating income / ratio / EPS), both orientations
A row is parsed into its label and numeric cells; "(4" means -4 (the ")" cell was dropped by h2t), "—" / "-" / "---" mean 0,
"F" / "U" / "N/A" are kept as None placeholders so column positions survive.
"""
import re

DASH = {'—', '-', '–', '---', '--', '— '}
SKIP_CELLS = {'pts', 'pt', ')pts', ') pt', ')pt', ') pts', '%', ')', ')%', 'bps', 'x'}

def num(c):
    c = c.strip().replace('​', '').replace('﻿', '')
    if c in DASH: return 0.0
    if c in ('F', 'U', 'N/A', 'NM', 'n/a', 'NA', '*'): return None
    s = c.replace('$', '').replace(',', '').replace('%', '').replace('pts', '').replace('pt', '').replace('x', '').strip()
    neg = s.startswith('(')
    s = s.strip('()').strip()
    if s in ('', '.'): return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v

def cells(line):
    parts = [p.strip() for p in line.split('|')]
    label = parts[0].replace('﻿', '').strip()
    vals = []
    for p in parts[1:]:
        q = p.replace('﻿', '').strip()
        if q in SKIP_CELLS or q == '': continue
        vals.append(num(q))
    return label, vals

def fix7(vals, hdr):
    """a stray '-' cell between the year-to-date columns (Q3-2020 freight total) gives 7 values in a 4-year table"""
    if hdr and sum(1 for v in hdr if v and 1990 < v < 2100) == 4 and len(vals) == 7 and vals[4] in (0.0, None):
        return vals[:4] + vals[5:]
    return vals

def norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9&/ ]+', ' ', s.lower().replace('’', "'"))).strip()

def join_lines(lines):
    """re-join labels that h2t split over two lines ("Total operating" / "revenues | 5,343 | ...")"""
    out = []
    for l in lines:
        prev = out[-1].strip() if out else ''
        tail = prev.lower().split()[-1] if prev else ''
        if (out and '|' in l and '|' not in prev and 0 < len(prev) < 60 and not prev.endswith(('.', ':'))
                and (re.match(r'^[a-z]', l.strip()) or tail in ('of', 'and', 'the', 'in', 'by', 'operating', 'for', 'from', 'to', 'net', 'at', 'or'))):
            out[-1] = out[-1].rstrip() + ' ' + l.lstrip(); continue
        out.append(l)
    return out

class Release:
    def __init__(self, text):
        self.lines = join_lines([l.rstrip() for l in text.split('\n')])
        self.n = len(self.lines)
        self.titles = self._titles()

    def _titles(self):
        out = []
        for i, l in enumerate(self.lines):
            t = norm(l)
            if 'statements of' in t and 'income' in t and 'comprehensive' not in t: out.append((i, 'is'))
            elif 'revenue detail' in t or 'freight revenues statistics' in t or 'freight revenue statistics' in t: out.append((i, 'frt'))
            elif ('financial position' in t or 'balance sheets' in t) and len(t) < 70 and '|' not in l: out.append((i, 'bs'))
            elif 'cash flows' in t and len(t) < 70 and '|' not in l: out.append((i, 'cf'))
            elif ('operating and financial statistics' in t or 'operating and performance statistics' in t
                  or 'operating/performance statistics' in t): out.append((i, 'ops'))
            elif 'non gaap measures reconciliation' in t or 'non gaap financial measures' in t: out.append((i, 'ng'))
            elif t.startswith('financial performance'): out.append((i, 'fp'))
        ded = []
        for i, k in out:
            if ded and ded[-1][1] == k and i - ded[-1][0] <= 8: continue      # sub-header repeating the table kind
            ded.append((i, k))
        return ded

    def block(self, kind, which=0, maxlen=140):
        """lines of the which-th table of this kind, up to the next table title"""
        idx = [i for i, k in self.titles if k == kind]
        if len(idx) <= which: return []
        s = idx[which]
        nxt = [i for i, k in self.titles if i > s and k != 'fp' or (i > s and k == 'fp' and kind == 'fp')]
        e = min(nxt) if nxt else min(self.n, s + maxlen)
        return self.lines[s:min(e, s + maxlen)]

    # ------------------------------------------------------------------ income statement
    IS_MAP = [
        (r'^freight revenues?$', 'frt'), (r'^other revenues?$|^other$', 'oth_rev'),
        (r'^total operating revenues?$|^operating revenues?$', 'rev'),
        (r'^compensation and benefits$|^salaries wages and employee benefits$', 'comp'),
        (r'^fuel$|^fuel and utilities$', 'fuel'), (r'^purchased services and materials$|^purchased services and other$', 'psm'),
        (r'^depreciation$', 'dep'), (r'^equipment and other rents$', 'rents'), (r'^materials and supplies$', 'mats'),
        (r'^other$', 'oth_exp'), (r'^total operating expenses$', 'opex'), (r'^operating income$', 'oi'),
        (r'^other income', 'oth_inc'), (r'^interest expense$', 'int'),
        (r'^income before income taxes$', 'ebt'), (r'^income tax', 'tax'), (r'^net income$', 'ni'),
        (r'^earnings per share basic$|^basic earnings per share$', 'eps_b'), (r'^earnings per share diluted$|^diluted earnings per share$', 'eps_d'),
        (r'^weighted average number of shares basic$|^weighted average shares basic.*', 'sh_b'),
        (r'^weighted average number of shares diluted$|^weighted average shares diluted.*', 'sh_d'),
        (r'^dividends declared per share$', 'dps'), (r'^operating ratio$', 'or'), (r'^effective tax rate$', 'etr'),
    ]

    def parse_is(self, which=0):
        """returns dict key -> [values...] for the first (current vs prior) income statement table, plus the header year row."""
        out, hdr, sect = {}, None, None
        for l in self.block('is', which):
            if '|' not in l:
                t = norm(l)
                if t.startswith('operating revenues'): sect = 'rev'
                elif t.startswith('operating expenses'): sect = 'exp'
                continue
            label, vals = cells(l)
            t = norm(label)
            if hdr is None and re.search(r'20\d\d', label + ' ' + l) and all(v is None or 1990 < v < 2100 for v in vals) and len(vals) >= 2:
                hdr = vals; continue
            if t.startswith('operating revenues') and not vals: sect = 'rev'; continue
            if t.startswith('operating expenses'): sect = 'exp'; continue
            if not vals: continue
            vals = fix7(vals, hdr)
            for pat, key in self.IS_MAP:
                if re.match(pat, t):
                    if key == 'oth_rev' and sect == 'exp': key = 'oth_exp'
                    if key == 'oth_exp' and sect == 'rev': key = 'oth_rev'
                    if key in out: break
                    out[key] = vals; break
        out['_hdr'] = hdr
        return out

    # ------------------------------------------------------------------ freight statistics
    def parse_freight(self, which=0):
        """returns {'rev': {label: vals}, 'cars': {...}, 'arpc': {...}, 'units': {...}}"""
        out = {'rev': {}, 'cars': {}, 'arpc': {}, 'units': {'rev': 1.0, 'cars': 1.0}}
        sub, hdr = None, None
        for l in self.block('frt', which, 80):
            t = norm(l)
            label, vals = cells(l)
            tl = norm(label)
            if tl.startswith('freight revenues') or tl.startswith('commodity revenue'):
                sub = 'rev'; out['units']['rev'] = 0.001 if '000' in label else 1.0; continue
            if tl.startswith('revenue carloads'):
                sub = 'cars'; out['units']['cars'] = 1.0 if 'thousand' in tl else 0.001; continue
            if tl.startswith('average revenue per car'):
                sub = 'arpc'; continue
            if sub is None or not vals: continue
            if re.search(r'20\d\d', label) or tl.startswith('for the periods') or tl.startswith('millions') or tl.startswith('for the period'): continue
            if all(v is None or 1990 < v < 2100 for v in vals): hdr = vals; continue
            label = re.sub(r'\s*\[a\]|\*', '', label).strip()
            out[sub][label] = fix7(vals, hdr)
        return out

    # ------------------------------------------------------------------ balance sheet / cash flow / stats (2-column tables)
    def parse_two_col(self, kind, which=0, maxlen=80):
        out, order = {}, []
        for l in self.block(kind, which, maxlen):
            if '|' not in l: continue
            label, vals = cells(l)
            if not vals or re.search(r'20\d\d', label) and all(v is None or 1990 < v < 2100 for v in vals): continue
            label = label.replace('*', '').strip()
            if label in out:        # repeated label (e.g. "Other" in several sections): suffix
                k = 2
                while f'{label} #{k}' in out: k += 1
                label = f'{label} #{k}'
            out[label] = vals; order.append(label)
        return out

    # ------------------------------------------------------------------ non-GAAP "Financial Performance" tables
    def parse_fp(self):
        """Adjusted results tables. Returns list of dicts: {'period_hdr', 'orientation', 'measures': {measure: {'gaap', 'adj', items:{label: delta}}}}"""
        res = []
        idx = [i for i, k in self.titles if k == 'fp']
        for s in idx:
            lines = self.lines[s:s + 30]
            hdr_cols, rows = None, []
            for l in lines[1:]:
                if '|' not in l:
                    if rows and (norm(l).startswith('union pacific') or norm(l).startswith('millions')): break
                    continue
                label, vals = cells(l)
                raw = [p.strip() for p in l.split('|')]
                if hdr_cols is None and any('result' in p.lower() for p in raw[1:]) or (hdr_cols is None and 'Operating Income' in l and 'Net Income' in l):
                    hdr_cols = raw; continue
                if hdr_cols is None and 'reported results' in norm(label):
                    hdr_cols = ['measures?']    # 2018 orientation: rows = GAAP / items / adjusted; columns = measures (header seen just before)
                rows.append((label, vals, raw))
                if norm(label).startswith('adjusted results') and hdr_cols: break
            res.append({'hdr': hdr_cols, 'rows': rows, 'title': lines[0], 'context': ' '.join(lines[1:3])})
        return res
