"""Parse the XBRL instance documents of the Google / Alphabet 10-K and 10-Q filings (2009+) into flat fact lists.

Each fact: (concept, value, start, end, dims, accession, filed, form, period_of_report). Instants have start=None. dims is a
tuple of sorted (axis, member) pairs (local names, prefix stripped), () for the undimensioned (face-statement) fact.
Values are as tagged (USD, shares, USD/share); the scale conversion to millions happens in extract.py. The parsed facts are
cached per filing as JSON in $GOOG_SRC/xfacts/<accession>.json."""
import json, os, re
from lxml import etree
S = os.environ.get('GOOG_SRC', '/tmp/goog_src')
XBRLI = 'http://www.xbrl.org/2003/instance'
XDI = 'http://xbrl.org/2006/xbrldi'

def local(q): return q.split('}')[-1] if '}' in q else q.split(':')[-1]

def parse(path):
    root = etree.parse(path, etree.XMLParser(huge_tree=True, recover=True)).getroot()
    ctx = {}
    for c in root.iter('{%s}context' % XBRLI):
        p = c.find('{%s}period' % XBRLI)
        st, en, ins = p.find('{%s}startDate' % XBRLI), p.find('{%s}endDate' % XBRLI), p.find('{%s}instant' % XBRLI)
        dims = []
        for m in c.iter('{%s}explicitMember' % XDI):
            dims.append((local(m.get('dimension')), local(m.text.strip())))
        for m in c.iter('{%s}typedMember' % XDI):
            dims.append((local(m.get('dimension')), (''.join(m.itertext())).strip()))
        if ins is not None: ctx[c.get('id')] = (None, ins.text.strip(), tuple(sorted(dims)))
        else: ctx[c.get('id')] = (st.text.strip(), en.text.strip(), tuple(sorted(dims)))
    out = []
    for el in root:
        if not isinstance(el.tag, str): continue
        cr = el.get('contextRef')
        if cr is None or cr not in ctx: continue
        t = (el.text or '').strip()
        if not t or el.get('{http://www.w3.org/2001/XMLSchema-instance}nil') == 'true': continue
        try: v = float(t)
        except ValueError: continue
        st, en, dims = ctx[cr]
        out.append((local(el.tag), v, st, en, [list(d) for d in dims], el.get('unitRef'), el.get('decimals')))
    return out

def filing_facts(o):
    """o: a filings.json record (10-K / 10-Q). Returns the cached fact list or None if no instance was downloaded."""
    cache = os.path.join(S, 'xfacts', o['acc'] + '.json')
    if os.path.exists(cache): return json.load(open(cache))
    docs = os.path.join(S, 'docs')
    pre = f"{o['date']}_{o['form']}_{o['acc']}_"
    xs = [f for f in os.listdir(docs) if f.startswith(pre) and f.lower().endswith('.xml') and 'defnref' not in f.lower()]
    if not xs: return None
    facts = parse(os.path.join(docs, xs[0]))
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    json.dump(facts, open(cache, 'w'))
    return facts
