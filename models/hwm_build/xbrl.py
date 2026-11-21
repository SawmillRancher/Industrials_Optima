"""EDGAR XBRL company facts (us-gaap / dei, Howmet Aerospace Inc., CIK 4281) -> values by calendar period.

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated / recast) value, pick=<year> the value in the filing whose fiscal
year (fy) is that year. Facts are tied to the earnings-release statements in check_data.py before use (playbook 5.1)."""
import json, os, datetime as dt
S = os.environ.get('HWM_SRC', '/tmp/hwm_src')
CIK = '4281'
_F = None
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
FORMS = ('10-K', '10-Q', '10-K/A', '10-Q/A')

def dump_subset(used):
    """write the concepts used by the model (10-K / 10-Q facts, periods ending 2018+) to data/_xbrl.json so the build runs without the raw download."""
    keep = ('start', 'end', 'val', 'filed', 'form', 'fy')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in FORMS and f['end'] >= '2018-01-01'] for k in sorted(used)}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def facts():
    global _F
    raw = os.path.join(S, f'cf_{CIK}.json')
    if _F is None and os.path.exists(SUBSET) and not os.path.exists(raw):
        _F = json.load(open(SUBSET))
    if _F is None:
        _F = {}
        d = json.load(open(raw))['facts']
        for ns in ('us-gaap', 'dei'):
            for k, v in d.get(ns, {}).items():
                for u, fs in v['units'].items():
                    _F.setdefault(k, []).extend(fs)
    return _F

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if d < 100 else 'H' if d < 190 else '9M' if d < 280 else 'FY' if d < 380 else None

USED = set()
def value(concept, year, kind, q=None, pick='first', scale=True):
    """kind: 'FY' | 'Q' | 'YTD' (q quarters to date) | 'I' (instant at quarter q end; q=4 -> year end)."""
    USED.add(concept)
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    end = f'{year}-' + {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[qq]
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS or f['end'] != end or dur(f) != want: continue
        if want != 'I' and dt.date.fromisoformat(f['start']).year != year: continue
        key = f['filed']
        if isinstance(pick, int):
            if f.get('fy') != pick: continue
            if best is None or key < best[0]: best = (key, f['val'])
        elif best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    v = best[1]
    if not scale: return v
    return v / 1e6 if abs(v) >= 1000 else v

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
