"""EDGAR XBRL company facts (us-gaap, The Brink's Company, CIK 78890) -> values by period (calendar fiscal year).

Durations: 'Q' (~3 months), 'H' (6), '9M' (9), 'FY' (12); instants at period end. pick='first' returns the value as originally
filed (10-K / 10-Q only), pick='last' the latest (restated) value. dump_subset() writes the concepts used by the model to
data/_xbrl.json so the build runs from committed data without the raw company-facts download."""
import json, os, datetime as dt
S = os.environ.get('BCO_SRC', '/tmp/bco_src')
CIK = '78890'
_F = None
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
FORMS = ('10-K', '10-Q', '10-K/A', '10-Q/A')

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

def dump_subset(used):
    keep = ('start', 'end', 'val', 'filed', 'form')
    out = {k: [{a: f[a] for a in keep if a in f} for f in facts().get(k, []) if f.get('form') in FORMS] for k in sorted(used)}
    json.dump(out, open(SUBSET, 'w'), separators=(',', ':'))

def dur(f):
    if 'start' not in f: return 'I'
    d = (dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days
    return 'Q' if 80 < d < 100 else 'H' if 170 < d < 190 else '9M' if 260 < d < 280 else 'FY' if 355 < d < 380 else None

USED = set()
def value(concept, year, kind, q=None, pick='first', scale=1e6, filed_from=None):
    """kind: 'FY' | 'Q' (discrete quarter q) | 'YTD' (q quarters to date) | 'I' (instant at the end of quarter q; q=4 = year end)."""
    USED.add(concept)
    want = {'FY': 'FY', 'Q': 'Q', 'I': 'I'}.get(kind) or {1: 'Q', 2: 'H', 3: '9M', 4: 'FY'}[q]
    qq = 4 if kind == 'FY' else q
    end = f'{year}-' + {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}[qq]
    best = None
    for f in facts().get(concept, []):
        if f.get('form') not in FORMS or f['end'] != end or dur(f) != want: continue
        if filed_from and f['filed'] < filed_from: continue
        key = f['filed']
        if best is None or (key < best[0] if pick == 'first' else key > best[0]): best = (key, f['val'])
    if best is None: return None
    return best[1] / scale if scale else best[1]

def first_of(concepts, *a, **k):
    for c in concepts:
        v = value(c, *a, **k)
        if v is not None: return v
    return None
