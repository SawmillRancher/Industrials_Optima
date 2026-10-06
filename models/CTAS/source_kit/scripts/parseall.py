import json,os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from relparse import parse
man=json.load(open('edgar/docs/manifest.json'))
out={}
for x in man:
    if x['form']!='8-K': continue
    exs=[f for f in x['files'] if re.search(r'ex.?99',os.path.basename(f),re.I)]
    if not exs: print('noex',x['filingDate']); continue
    t='edgar/txt/'+os.path.splitext(os.path.basename(exs[0]))[0]+'.txt'
    out[x['filingDate']]={'file':t,'tables':parse(t)}
# add Dec 2016 and Mar 2007
for d,f in [('2016-12-22','edgar/txt/2016-12-22_8-K_ex9912-16.txt'),('2007-03-22','edgar/txt/2007-03-22_8-K_ex99121906.txt')]:
    out[d]={'file':f,'tables':parse(f)}
json.dump(out,open('edgar/releases.json','w'))
print(len(out))
