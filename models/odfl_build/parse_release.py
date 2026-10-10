"""Parse an ODFL earnings release (8-K Ex. 99.1, converted by h2t.py) into the statement of operations and the
operating-statistics table. Returns current-quarter values and (where shown) current year-to-date values.

ODFL releases (2006-2026) share one layout: summary table, Statements of Operations (three-month and year-to-date
columns, each with a % of revenue column), Operating Statistics, condensed Balance Sheets. % columns are dropped.
"""
import re

NUM = re.compile(r'^\(?-?\$?\(?[\d,]*\.?\d+\)?$')

def _cells(line):
    line = line.replace('| )%', ')%').replace('|)%', ')%')
    return [c.strip() for c in line.split('|')]

def _val(c):
    c = c.replace('$', '').replace(',', '').strip()
    if c in ('—', '–', '-', '— ', '--'): return 0.0
    neg = c.startswith('(') or c.endswith(')')
    c = c.strip('()')
    try:
        v = float(c)
    except ValueError:
        return None
    return -v if neg else v

def numbers(line):
    """Numeric (non-%) cells after the label."""
    cells = _cells(line)
    out = []
    for c in cells[1:]:
        if c.endswith('%') or c.endswith('%)'): continue
        v = _val(c)
        if v is not None: out.append(v)
    return out

IS_MAP = [  # key, regex on label (first match wins within the statement section)
    ('swb', r'^salaries,? wages'),
    ('ops', r'^operating supplies'),
    ('gen', r'^general supplies'),
    ('taxlic', r'^operating taxes'),
    ('ins', r'^insurance'),
    ('comm', r'^communications'),
    ('dda', r'^depreciation'),
    ('pt', r'^purchased transportation'),
    ('rents', r'^building and office'),
    ('misc', r'^miscellaneous'),
    ('total_opex', r'^total operating expenses'),
    ('op_income', r'^operating income'),
    ('int_exp', r'^interest expense(?!, net)'),
    ('int_net', r'^interest expense, net'),
    ('int_inc', r'^interest income'),
    ('other_exp', r'^other (expense|\(income\) expense|income|\(expense\) income|expense \(income\))'),
    ('ebt', r'^income before income taxes'),
    ('tax', r'^provision for income taxes'),
    ('cum_eff', r'^cumulative effect'),
    ('net_income', r'^net income'),
]
ST_MAP = [
    ('work_days', r'^work days'),
    ('or', None),
    ('miles', r'^(ltl )?intercity miles'),
    ('ltl_tons', r'^ltl tons(?! per)(?!.*per day)'),
    ('tons_day', r'^ltl (tons|tonnage) per day'),
    ('total_tons', r'^total tons'),
    ('ltl_ship', r'^ltl shipments(?! per)(?!.*per day)'),
    ('ship_day', r'^ltl shipments per day'),
    ('total_ship', r'^total shipments'),
    ('pct_ltl', r'^percent ltl'),
    ('rev_mile', r'^revenue per intercity mile'),
    ('rev_cwt_xf', r'^(ltl )?rev(enue)?( ?/ ?| per )(ltl )?(cwt|hundredweight).*(less fsc|excluding fuel)'),
    ('rev_cwt', r'^(ltl )?rev(enue)?( ?/ ?| per )(ltl )?(cwt|hundredweight)'),
    ('rev_shp_xf', r'^(ltl )?rev(enue)?( ?/ ?| per )(ltl )?(shp|shipment).*(less fsc|excluding fuel)'),
    ('rev_shp', r'^(ltl )?rev(enue)?( ?/ ?| per )(ltl )?(shp|shipment)'),
    ('wps', r'^(ltl )?weight per (ltl )?shipment'),
    ('loh', r'^average length of haul'),
    ('emp_avg', r'^average active full-time employees'),
]

def parse(text):
    lines = [l.strip() for l in text.split('\n')]
    out = {'q': {}, 'ytd': {}, 'labels': {}}
    # ---- statement of operations: from the first 'Salaries, wages' row back to its 'Revenue' row
    i_swb = next((i for i, l in enumerate(lines) if re.match(r'(?i)^salaries,? wages', l) and '|' in l), None)
    if i_swb is None: return None
    i_rev = max(i for i in range(max(0, i_swb - 12), i_swb) if re.match(r'(?i)^(total )?revenue', lines[i]) or i == max(0, i_swb - 12))
    # LTL / other services revenue split: summary table at the top of the release (2014+) or the statement itself
    for i in range(0, i_swb):
        l = lines[i].lower(); n = numbers(lines[i])
        if not n or '|' not in lines[i]: continue
        for key, rx in (('ltl_rev', r'^ltl services revenue'), ('other_rev', r'^other services revenue')):
            if re.match(rx, l) and key not in out['q']:
                out['q'][key] = n[0]
                if len(n) >= 3: out['ytd'][key] = n[2]
    # revenue lines between i_rev and swb (total, LTL services, other services)
    for i in range(i_rev, i_swb):
        l = lines[i].lower()
        n = numbers(lines[i])
        if not n or '|' not in lines[i]: continue
        if l.startswith('ltl services'): key = 'ltl_rev'
        elif l.startswith('other services'): key = 'other_rev'
        elif l.startswith(('revenue', 'total revenue')): key = 'revenue'
        else: continue
        out['q'][key] = n[0]
        if len(n) >= 3: out['ytd'][key] = n[2]
    end = next((i for i in range(i_swb, len(lines)) if re.match(r'(?i)^(diluted|basic and diluted)', lines[i])), i_swb + 40)
    seen = set()
    for i in range(i_swb, min(end + 12, len(lines))):
        l = lines[i]
        if '|' not in l: continue
        lab = _cells(l)[0].lower()
        for key, rx in IS_MAP:
            if key in seen: continue
            if re.match(rx, lab):
                n = numbers(l)
                if not n: break
                seen.add(key); out['labels'][key] = _cells(l)[0]
                out['q'][key] = n[0]
                if len(n) >= 3: out['ytd'][key] = n[2]
                break
    # EPS / shares after the statement
    blk = lines[end - 2:end + 14]
    mode = None
    for l in blk:
        ll = l.lower()
        if 'weighted average' in ll or 'outstanding shares' in ll: mode = 'sh'; continue
        if 'earnings per share' in ll and '|' not in l: mode = 'eps'; continue
        if '|' not in l: continue
        lab = _cells(l)[0].lower(); n = numbers(l)
        if not n: continue
        if lab.startswith('dividends declared'):
            out['q']['dps'] = n[0]
            if len(n) >= 3: out['ytd']['dps'] = n[2]
            continue
        is_sh = mode == 'sh' or (n[0] > 1000)
        if lab.startswith('basic and diluted'):
            for k in (('eps_basic', 'eps_dil') if not is_sh else ('sh_basic', 'sh_dil')):
                out['q'][k] = n[0]
                if len(n) >= 3: out['ytd'][k] = n[2]
        elif lab.startswith('basic') or lab.startswith('diluted'):
            k = ('sh_' if is_sh else 'eps_') + ('basic' if lab.startswith('basic') else 'dil')
            if k in out['q']: continue
            out['q'][k] = n[0]
            if len(n) >= 3: out['ytd'][k] = n[2]
    # ---- operating statistics
    i_st = next((i for i in range(end, len(lines)) if re.search(r'(?i)operating statistics', lines[i])), None)
    if i_st is not None:
        seen = set()
        for i in range(i_st, min(i_st + 40, len(lines))):
            l = lines[i]
            if re.match(r'(?i)^balance sheets', l): break
            if '|' not in l: continue
            lab = re.sub(r'[\*‡†]|\(\d\)', '', _cells(l)[0]).strip().lower()
            if lab.startswith('operating ratio'):
                cells = _cells(l)[1:]
                pc = [c for c in cells if c.endswith('%')]
                if pc:
                    out['q']['or_pub'] = float(pc[0].rstrip('%')) / 100
                    if len(pc) in (4, 6): out['ytd']['or_pub'] = float(pc[2 if len(pc) == 4 else 3].rstrip('%').strip('()')) / 100
                continue
            for key, rx in ST_MAP:
                if rx is None or key in seen: continue
                if re.match(rx, lab):
                    n = numbers(l)
                    if not n: break
                    seen.add(key); out['labels'][key] = _cells(l)[0]
                    out['q'][key] = n[0]
                    if len(n) >= 3: out['ytd'][key] = n[2]
                    break
    return out
