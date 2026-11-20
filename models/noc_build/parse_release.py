"""Parse a Northrop Grumman earnings release (8-K Item 2.02, Ex. 99 / 99.1) from its text version ($NOC_SRC/txt, one table row per
line, cells joined by ' | ') into typed blocks with resolved columns.

Every release since 2006 prints: a consolidated table (sales and operating income by segment, intersegment eliminations,
segment operating income, the reconciliation to operating income — unallocated corporate expense, net pension / FAS-CAS
adjustment, royalty reversal, divestiture items — then interest, pension items below operating income, other, earnings before
taxes, taxes, net earnings), the consolidated statements (Schedule 1 earnings, Schedule 2 financial position, Schedule 3
cash flows, year to date), backlog, and (from 2013) pension-adjusted / MTM-adjusted per-share tables. Titles and column order
vary by era, so tables are identified by content and each value column is resolved from the nearest header with year tokens:
layout = ['v','v','c','v','v','c'] (value / change columns); the first value block is the quarter (three months) and the
second the year to date (six / nine months or the full year in fourth-quarter releases).

Values are in USD millions as published (per share in $; shares in millions). '(524' / '(524)' -> -524; '—' -> 0.0.
Rows whose values are rates (contain %) are skipped. Rows with fewer cells than the layout (empty cells are dropped by the
text conversion) are resolved greedily: change columns consume a token only when it is marked (%, bps, NM) or when more tokens
remain than value columns; a change-marked token never fills a value column (a missing comparative therefore stays None).
"""
import re

CHG = re.compile(r'%|bps|^NM$|^N/M$|^n/m$', re.I)
JUNK = {'%)', ')', '%', ')%', '', '$', '(', 'bps', 'bps)'}

def pnum(tok):
    t = tok.strip().replace('$', '').replace('\xa0', ' ').strip()
    if t in ('—', '–', '-', '―', '--', '— —', '(—', '—)'): return 0.0
    neg = t.startswith('(') or t.startswith('-')
    t = t.strip('()-').replace(',', '').strip()
    if not re.fullmatch(r'\d+(\.\d+)?|\.\d+', t): return None
    v = float(t)
    return -v if neg else v

def clean_tokens(cells):
    out = []
    for c in cells:
        c = c.strip()
        if c in JUNK: continue
        c = re.sub(r'\s*\|?\s*%\)$', '%)', c)
        out.append(c)
    return out

def is_chg(tok): return bool(CHG.search(tok))

def split_line(line):
    parts = [re.sub(r'\s+', ' ', p.replace('\xa0', ' ')).strip() for p in line.split('|')]
    return parts[0], clean_tokens(parts[1:])

def layout_from_header(line):
    """header tokens -> ['v' | 'c' | 'x'] (year / Change / other) or None"""
    lab, toks = split_line(line)
    if re.fullmatch(r'(19|20)\d\d\s*(\(\d\))?', lab.strip()): toks = [lab] + toks
    lay = []
    for t in toks:
        if re.search(r'change', t, re.I): lay.append('c')
        elif re.search(r'(?<!\d)(19|20)\d\d(?!\d)', t) and not re.search(r'[a-z]{4,}', re.sub(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\.?', '', t, flags=re.I)): lay.append('v')
        else: lay.append('x')
    if lay.count('v') >= 1 and 'x' not in lay: return lay
    return None

def months_from_text(txt):
    t = txt.lower()
    out = []
    for m in re.finditer(r'(three|six|nine|twelve) ?months|first quarter|second quarter|third quarter|fourth quarter|total year|full year|year ended|year to date|year-to-date|twelve', t):
        s = m.group(0)
        if 'three' in s or 'quarter' in s: out.append(3)
        elif 'six' in s: out.append(6)
        elif 'nine' in s: out.append(9)
        else: out.append(12)
    return out

def assign(toks, lay):
    """-> list of values (len = number of 'v' in layout), greedy per the module docstring"""
    nv = lay.count('v')
    vals, ti = [], 0
    for i, k in enumerate(lay):
        rem = len(toks) - ti
        rem_v = nv - len(vals)
        if k == 'v':
            if ti < len(toks) and not is_chg(toks[ti]):
                vals.append(pnum(toks[ti])); ti += 1
            else:
                vals.append(None)
        else:  # change column
            if ti < len(toks) and (is_chg(toks[ti]) or rem > rem_v):
                ti += 1
    return vals

class Doc:
    def __init__(self, text):
        self.lines = text.splitlines()

    def rows(self, start, end):
        out = []
        pend = ''
        for i in range(start, min(end, len(self.lines))):
            l = self.lines[i]
            if '|' not in l:
                s = l.strip()
                if s and len(s) < 90 and not s.endswith('.'): pend = s
                elif s: pend = ''
                continue
            lab, toks = split_line(l)
            if pend and (not lab or lab[0].islower() or lab.startswith(('before', 'operations', '(', 'income taxes', 'included above'))):
                lab = (pend + ' ' + lab).strip()
            pend = ''
            out.append((i, lab, toks))
        return out

    def header_near(self, i, up=12):
        """nearest layout header above line i, plus the months words in the header area"""
        lay, hdr_txt = None, ''
        for j in range(i - 1, max(-1, i - up), -1):
            l = self.lines[j]
            if lay is None:
                lay = layout_from_header(l)
                if lay: hdr_txt = l
                continue
            hdr_txt = l + ' ' + hdr_txt
        return lay, hdr_txt

def find(lines, rx, start=0, end=None, flags=re.I):
    for i in range(start, len(lines) if end is None else min(end, len(lines))):
        if re.search(rx, lines[i], flags): return i
    return None

# ------------------------------------------------------------------ segment names
SEGS = [('Aeronautics Systems', r'^aeronautics systems'), ('Defense Systems', r'^defense systems'), ('Mission Systems', r'^mission systems'),
        ('Space Systems', r'^space systems'), ('Aerospace Systems', r'^aerospace systems'), ('Innovation Systems', r'^innovation systems'),
        ('Technology Services', r'^technology services'), ('Electronic Systems', r'^electronic systems'), ('Information Systems', r'^information systems'),
        ('Technical Services', r'^technical services'), ('Shipbuilding', r'^shipbuil'), ('Information & Services', r'^information (&|and) services'),
        ('Aerospace', r'^aerospace$|^aerospace \d'), ('Electronics', r'^electronics$|^electronics \d'), ('Ships', r'^ships$|^ships \d'),
        ('Mission Systems (legacy)', r'^mission systems \(legacy\)'), ('Information Technology', r'^information technology'),
        ('Integrated Systems', r'^integrated systems'), ('Space Technology', r'^space technology'), ('Newport News', r'^newport news'),
        ('Ship Systems', r'^ship systems')]
def segname(lab):
    L = lab.lower().strip().rstrip('0123456789 ,').strip()
    pre = ''
    if L.startswith('total ') and not L.startswith('total sales') and not L.startswith('total segment'):
        pre, L = 'Total ', L[6:]
    for n, rx in SEGS:
        if re.search(rx, L): return pre + n
    if re.fullmatch(r'other', L): return 'Other'
    return None

RECON_END = re.compile(r'^(total )?operating (\(loss\) )?(income|margin)( \(loss\))?\s*\d?$', re.I)

def consolidated_table(doc):
    """the first 'Sales' block listing segments -> dict with q (3-month) and y (year-to-date) parts"""
    lines = doc.lines
    i0 = None
    for i, l in enumerate(lines):
        if re.fullmatch(r'\s*(Sales|Sales and Service Revenues)\s*\|?\s*', l):
            # next non-empty row must be a segment
            for j in range(i + 1, min(i + 4, len(lines))):
                if '|' in lines[j]:
                    if segname(split_line(lines[j])[0]): i0 = i
                    break
        if i0 is not None: break
    if i0 is None: return None
    lay, hdr = doc.header_near(i0)
    if lay is None: return None
    mon = months_from_text(hdr)
    nv = lay.count('v')
    blocks = nv // 2
    out = {'layout': lay, 'header': hdr.strip(), 'months': mon, 'line': i0, 'q': {}, 'y': {}}
    state = 'sales'
    rows = doc.rows(i0 + 1, i0 + 80)
    seg_s, seg_o, recon, below, elim_s, elim_o, tot_s, seg_oi, oi_tot = {}, {}, [], [], None, None, None, None, None
    done = False
    for i, lab, toks in rows:
        L = lab.lower().strip()
        if not toks:
            if re.match(r'^(segment )?operating (\(loss\) )?(income|margin)|^segment operating', L): state = 'oi'
            elif re.match(r'^reconciliation', L): state = 'recon'
            elif re.match(r'^unallocated corporate', L): state = 'recon'
            continue
        if any('%' in t for t in toks) and not any(pnum(t) is not None and '%' not in t for t in toks): continue
        if re.search(r'margin rate|as a % of sales|^effective income tax rate|operating margin %|margin %', L): continue
        vals = assign(toks, lay)
        sn = segname(lab)
        if state == 'sales':
            if sn: seg_s[sn] = vals
            elif re.match(r'^intersegment', L): elim_s = vals
            elif L == '' or re.match(r'^total sales|^sales$', L) or pnum(lab) is not None:
                if pnum(lab) is not None: vals = assign([lab] + toks, lay)
                tot_s = vals; state = 'oi_hdr'
        elif state in ('oi_hdr', 'oi'):
            if sn: seg_o[sn] = vals; state = 'oi'
            elif re.match(r'^intersegment', L): elim_o = vals
            elif re.match(r'^(total )?segment operating (\(loss\) )?(income|margin)|^adjusted segment', L):
                seg_oi = vals; state = 'recon'
            elif state == 'oi' and RECON_END.match(L):
                oi_tot = vals; state = 'below'
        elif state == 'recon':
            if layout_from_header(lines[i]) or re.match(r'^sales\s*\d?$', L): oi_tot = None; break
            if RECON_END.match(L) and not re.search(r'adjusted|pension-adjusted', L):
                oi_tot = vals; state = 'below'
            else:
                recon.append((lab, vals))
        elif state == 'below':
            below.append((lab, vals))
            if re.match(r'^net (\(loss\) )?earnings|^net earnings \(loss\)|^net loss', L):
                if not re.search(r'per share|attributable to noncontrolling', L): done = True
        if done: break
    if oi_tot is None or not recon or any(re.match(r'^(sales|\d+)$', l.strip(), re.I) for l, v in recon):
        recon, below, oi_tot2, seg_oi2 = [], [], None, None
        for i, lab, toks in doc.rows(0, len(lines)):
            L = lab.lower().strip()
            if toks and re.match(r'^(total )?segment operating (\(loss\) )?(income|margin)\s*[\d, ]*$', L) and not re.search(r'adjusted', L):
                lay2, _ = doc.header_near(i, 16)
                if lay2 is None or lay2.count('v') != lay.count('v'): continue
                seg_oi2 = assign(toks, lay2); st = 'recon'; recon, below = [], []
                for i2, lab2, toks2 in doc.rows(i + 1, i + 40):
                    L2 = lab2.lower().strip()
                    if not toks2: continue
                    if re.search(r'margin rate|as a % of sales|^effective income tax rate', L2): continue
                    if layout_from_header(doc.lines[i2]): break
                    v2 = assign(toks2, lay2)
                    if st == 'recon':
                        if RECON_END.match(L2): oi_tot2 = v2; st = 'below'
                        else: recon.append((lab2, v2))
                    else:
                        below.append((lab2, v2))
                        if re.match(r'^net (\(loss\) )?earnings|^net earnings \(loss\)|^net loss', L2) and not re.search(r'per share', L2): break
                if oi_tot2 is not None: break
                recon, below = [], []
        if oi_tot2 is not None:
            oi_tot = oi_tot2
            if seg_oi is None: seg_oi = seg_oi2
    def part(k):
        o = {'sales': {s: v[k] for s, v in seg_s.items()}, 'elim_sales': elim_s[k] if elim_s else None, 'total_sales': tot_s[k] if tot_s else None,
             'oi': {s: v[k] for s, v in seg_o.items()}, 'elim_oi': elim_o[k] if elim_o else None, 'seg_oi': seg_oi[k] if seg_oi else None,
             'recon': [(l, v[k]) for l, v in recon], 'oi_total': oi_tot[k] if oi_tot else None, 'below': [(l, v[k]) for l, v in below]}
        return o
    out['q'] = {'cur': part(0), 'py': part(1) if nv >= 2 else None}
    if blocks >= 2:
        out['y'] = {'cur': part(2), 'py': part(3) if nv >= 4 else None}
    return out

# ------------------------------------------------------------------ statements (Schedules 1-3)
def statement(doc, title_rx, first_row_rx, stop_rx, max_rows=90, incl_stop=None):
    """rows of a consolidated statement -> {'layout','months','rows': [(label, [values])]}"""
    lines = doc.lines
    t = find(lines, title_rx)
    if t is None: return None
    s = find(lines, first_row_rx, t, t + 40)
    if s is None: return None
    lay, hdr = doc.header_near(s, 14)
    if lay is None:
        # statements sometimes carry the years on the title line block: search a bit further up
        for j in range(s - 1, max(-1, s - 25), -1):
            lay = layout_from_header(lines[j])
            if lay: hdr = ' '.join(lines[j - 3:j + 1]); break
    if lay is None: return None
    rows = []
    for i, lab, toks in doc.rows(s, s + max_rows):
        if re.search(stop_rx, lab, re.I) and rows: break
        if not toks: rows.append((lab, [])); continue
        rows.append((lab, assign(toks, lay)))
        if incl_stop and re.search(incl_stop, lab, re.I): break
    return {'layout': lay, 'months': months_from_text(hdr), 'header': hdr.strip(), 'rows': rows, 'line': s}

def income_statement(doc):
    return statement(doc, r'CONSOLIDATED STATEMENTS? OF (EARNINGS|OPERATIONS|INCOME)', r'^(Sales|Total sales|Product sales|Product|Sales and service revenues)\s*\|', r'^(Other comprehensive|Comprehensive|Net earnings \(from above\))')

def balance_sheet(doc):
    return statement(doc, r'CONSOLIDATED STATEMENTS? OF FINANCIAL POSITION|CONSOLIDATED BALANCE SHEETS?', r'^Cash and cash equivalents\s*\|', r'^(SCHEDULE|Northrop Grumman)', 70, incl_stop=r'^total liabilities and (share|stock)holders.? equity')

def cash_flow(doc):
    return statement(doc, r'CONSOLIDATED STATEMENTS? OF CASH FLOWS', r'^(Net earnings|Net \(loss\) earnings|Net earnings \(loss\)|Sources of cash|Cash received from customers|Operating activities)', r'^(SCHEDULE|Supplemental|Non-cash (investing|financing)|Northrop Grumman)', 110, incl_stop=r'^cash and cash equivalents,? (at )?end of|^cash,? cash equivalents.* end of')

# ------------------------------------------------------------------ backlog, awards, FCF, non-GAAP rows, guidance
def backlog(doc):
    """total backlog ($m) from the backlog schedule; funded/unfunded where printed; by segment"""
    lines = doc.lines
    t = find(lines, r'^(TOTAL )?BACKLOG|^Backlog\s*$|^Total backlog \|')
    out = {}
    h = find(lines, r'^TOTAL BACKLOG', flags=0)
    i = find(lines, r'^Total( backlog)? \|', h, h + 20) if h is not None else None
    if i is None: i = find(lines, r'^Total backlog \|', 0)
    if i is not None:
        lab, toks = split_line(lines[i])
        vals = [pnum(x) for x in toks if pnum(x) is not None and '%' not in x]
        out['total_row'] = vals
        segs = {}
        for j in range(i - 8, i):
            if j < 0: continue
            l2, t2 = split_line(lines[j])
            sn = segname(l2)
            if sn: segs[sn] = [pnum(x) for x in t2 if pnum(x) is not None and '%' not in x]
        out['segments'] = segs
        out['header'] = ' '.join(lines[max(0, i - 12):i - len(segs)])[-300:]
    txt = ' '.join(lines)
    for rx in (r'total backlog[^.$]{0,45}?(?:was|totaled|of|increased to|grew to|reached|to)\s*\$([\d.,]+)\s*billion',
               r'backlog (?:increase[sd]|grew|rose|declined|decreased|increasing|up|down) (?:\d+ percent )?to (?:a record )?\$([\d.,]+)\s*billion',
               r'(?:record |total )?backlog (?:of|was|totaled|at) (?:a record )?\$([\d.,]+)\s*billion'):
        m = re.search(rx, txt, re.I)
        if m: out['total_bn_text'] = float(m.group(1).replace(',', '')); break
    m = re.search(r'(?:new|net) awards\s*(?:totaled|of|were|totaling)\s*\$([\d.,]+)\s*billion', txt, re.I)
    if m: out['awards_bn_text'] = float(m.group(1).replace(',', ''))
    m = re.search(r'book[- ]to[- ]bill (?:ratio )?of ([\d.]+)x', txt, re.I)
    if m: out['book_to_bill_text'] = float(m.group(1))
    return out

NG_RX = re.compile(r'MTM|mark-to-market|pension[- ]adjusted|net pension adjustment|FAS|CAS|transaction-adjusted|adjusted (diluted )?EPS|adjusted net earnings|free cash flow|'
                   r'capital expenditures|discretionary pension|net cash (provided|used)|tax effect|federal tax|deferred state tax|per share impact|after-tax|'
                   r'intangible asset amortization|weighted[- ]average|dilutive effect|diluted EPS|tax reform|unallocated corporate|royalty|operating income|'
                   r'proceeds from sale of equipment|effective income tax rate|organic|earnings per share|^basic\b|^diluted\b|^net (\(loss\) )?earnings|'
                   r'^total backlog|^interest expense|^other, net|^earnings before|^federal and foreign income tax|^gain on sale|^make-whole|^transaction costs|^state tax impact', re.I)
def ngaap_rows(doc):
    """every data row whose label matches a non-GAAP / pension / cash-flow keyword, with its table's layout and months"""
    out = []
    lay, hdr, mon, last_h = None, '', [], -99
    for i, l in enumerate(doc.lines):
        h = layout_from_header(l)
        if h:
            lay, hdr, mon, last_h = h, ' '.join(doc.lines[max(0, i - 4):i + 1]), months_from_text(' '.join(doc.lines[max(0, i - 4):i + 1])), i
            continue
        if '|' not in l or lay is None: continue
        lab, toks = split_line(l)
        if not toks or not NG_RX.search(lab): continue
        if re.search(r'margin rate|as a % of sales', lab, re.I): continue
        vals = assign(toks, lay)
        out.append({'line': i, 'label': lab, 'vals': vals, 'layout': lay, 'months': mon, 'table_line': last_h})
    return out

def guidance_text(doc):
    lines = doc.lines
    s = find(lines, r'^(20\d\d )?(Financial )?Guidance\s*$|^Guidance$|^\d{4} Guidance|Guidance \(|^20\d\d Financial Guidance')
    if s is None: return None
    e = find(lines, r'^SCHEDULE 1|^About Northrop|^Northrop Grumman Corporation 2980|^Forward-Looking|^Table \d|^Consolidated Operating Results', s + 1)
    if e is None: e = s + 60
    return '\n'.join(x for x in lines[s:min(e, s + 120)] if x.strip())

def parse(text):
    doc = Doc(text)
    return {'cons': consolidated_table(doc), 'is': income_statement(doc), 'bs': balance_sheet(doc), 'cf': cash_flow(doc),
            'backlog': backlog(doc), 'ng': ngaap_rows(doc), 'guidance': guidance_text(doc)}

if __name__ == '__main__':
    import sys, json
    r = parse(open(sys.argv[1]).read())
    c = r['cons']
    if c:
        print('layout', c['layout'], c['months'], '|', c['header'])
        for k in ('q', 'y'):
            if c[k]: print(k, json.dumps(c[k]['cur'], indent=None)[:1500])
    for k in ('is', 'bs', 'cf'):
        t = r[k]
        print('\n==', k, t and (t['layout'], t['months']))
        if t:
            for lab, v in t['rows'][:60]: print('  ', lab[:70], v)
    print('\n== backlog', r['backlog'])
    print('\n== ng rows'); [print('  ', x['line'], x['label'][:60], x['vals'], x['months']) for x in r['ng'][:60]]
    print('\n== guidance\n', (r['guidance'] or '')[:1500])
