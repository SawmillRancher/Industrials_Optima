"""HTML table parser for Fair Isaac's EDGAR documents (10-K / 10-Q / 8-K Ex. 99.1).

tables(path) -> list of {'ctx': text before the table (titles), 'rows': [[label, [v0, v1, ...]], ...], 'ncol': n}
Each numeric cell is assigned to a value column by the grid position of its right edge (colspans expanded), so a blank
cell keeps its column (h2t-style text loses it). Numbers: '(25,433' and '( 21,296 )' are negative; '—' / '-' cells are 0;
'$', ')' and '%' cells are ignored. Labels split across rows ('Selling, general and' / 'administrative') are re-joined.
Results are cached as JSON in $FICO_SRC/tab/.
"""
import re, os, json, hashlib, warnings
from bs4 import BeautifulSoup
warnings.filterwarnings('ignore')
S = os.environ.get('FICO_SRC', '/tmp/fico_src')
NUM = re.compile(r'^\(?\s*-?[\d,]*\.?\d+\s*\)?$')
DASH = {'—', '-', '–', '— —', '—%', '- -'}

def cell_num(c):
    c = c.replace('$', '').replace('\xa0', ' ').replace('​', '').strip()
    c = re.sub(r'\s*%$', '', c)
    if c in DASH: return 0.0
    if not NUM.match(c): return None
    neg = c.startswith('(') or c.startswith('-')
    s = re.sub(r'[()\s,\-]', '', c)
    if not s or s == '.': return None
    try: v = float(s)
    except ValueError: return None
    return -v if neg else v

def clean_label(s):
    s = s.replace('\xa0', ' ').replace('​', '')
    s = re.sub(r'\(\s*(\d|\*+|[a-c])\s*\)', '', s)
    return re.sub(r'\s+', ' ', s).strip(' :')

def _parse(path):
    soup = BeautifulSoup(open(path, 'rb').read(), 'lxml')
    for t in soup(['script', 'style']): t.decompose()
    tabs = soup.find_all('table')
    out = []
    for n, tb in enumerate(tabs):
        grid = []
        for tr in tb.find_all('tr'):
            cells, pos = [], 0
            for td in tr.find_all(['td', 'th']):
                span = int(td.get('colspan', 1) or 1) if str(td.get('colspan', '1')).isdigit() else 1
                cells.append((pos, pos + span - 1, td.get_text(' ', strip=True)))
                pos += span
            grid.append(cells)
        tb.replace_with(soup.new_string(f'\n@@TABLE{n}@@\n'))
        out.append(grid)
    text = soup.get_text('\n')
    parts = re.split(r'@@TABLE(\d+)@@', text)
    ctx = {}
    for k in range(1, len(parts), 2):
        pre = re.sub(r'\s+', ' ', parts[k - 1])[-400:]
        ctx[int(parts[k])] = pre
    res = []
    for n, grid in enumerate(out):
        # numeric cells: (row, end-position, value); label = text cells before the first numeric cell
        rows = []
        for cells in grid:
            lab, nums, seen_num = [], [], False
            for a, b, t in cells:
                t2 = t.strip()
                if not t2 or t2 in ('$', ')', '%', ')%', '(', '$ (', '%)'): continue
                v = cell_num(t2)
                if v is not None and (seen_num or lab or a > 0):
                    nums.append((b, v)); seen_num = True
                elif not seen_num:
                    lab.append(t2)
            rows.append((clean_label(' '.join(lab)), nums))
        if not any(r[1] for r in rows): continue
        cnt = {}
        for _, nums in rows:
            for b, _ in nums: cnt[b] = cnt.get(b, 0) + 1
        ends = sorted(cnt)
        # cluster nearby end positions (merged $ / number cells) into value columns
        cols = []
        for e in ends:
            if cols and e - cols[-1][-1] <= 1: cols[-1].append(e)
            else: cols.append([e])
        cmap = {e: i for i, grp in enumerate(cols) for e in grp}
        rr, pend = [], ''
        for lab, nums in rows:
            if not nums:
                if lab and len(lab) < 80: pend = (pend + ' ' + lab).strip() if pend and (lab[:1].islower()) else lab
                else: pend = ''
                rr.append([lab, []]); continue
            vals = [None] * len(cols)
            for b, v in nums: vals[cmap[b]] = v
            if pend and lab[:1].islower(): lab = clean_label(pend + ' ' + lab)
            pend = ''
            rr.append([lab, vals])
        res.append({'ctx': ctx.get(n, ''), 'rows': rr, 'ncol': len(cols), 'idx': n})
    return res

def tables(path):
    os.makedirs(os.path.join(S, 'tab'), exist_ok=True)
    c = os.path.join(S, 'tab', hashlib.md5(path.encode()).hexdigest() + '.json')
    if os.path.exists(c) and os.path.getmtime(c) > os.path.getmtime(__file__): return json.load(open(c))
    r = _parse(path); json.dump(r, open(c, 'w')); return r

def find_table(tabs, need, ctx=None, start=0, nth=0):
    """first table (from index start) that has a row label matching every regex in `need` (and ctx regex in its context)."""
    k = 0
    for t in tabs[start:]:
        labs = [r[0] for r in t['rows']]
        if all(any(re.search(p, l, re.I) for l in labs) for p in need) and (ctx is None or re.search(ctx, t['ctx'], re.I)):
            if k == nth: return t
            k += 1
    return None

def get(t, pat, col=0, nth=0, after=None):
    """value in column `col` of the nth row matching pat (rows with any number)."""
    if t is None: return None
    p = re.compile(pat, re.I); k = 0; go = after is None
    for lab, vals in t['rows']:
        if not go:
            if re.search(after, lab, re.I): go = True
            continue
        if vals and p.search(lab):
            if k == nth: return vals[col] if col < len(vals) else None
            k += 1
    return None

def rowlist(t, start_pat, stop_pat, col=0, incl_start=False):
    """[(label, value)] for rows strictly between the first row matching start_pat and the next matching stop_pat."""
    out, go = [], False
    for lab, vals in t['rows']:
        if not go:
            if re.search(start_pat, lab, re.I) and vals:
                go = True
                if incl_start: out.append((lab, vals[col] if col < len(vals) else None))
            continue
        if re.search(stop_pat, lab, re.I) and vals: break
        if vals: out.append((lab, vals[col] if col < len(vals) else None))
    return out
