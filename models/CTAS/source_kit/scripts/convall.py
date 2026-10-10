import os,subprocess,sys
src,dst=sys.argv[1],sys.argv[2]; os.makedirs(dst,exist_ok=True)
for f in sorted(os.listdir(src)):
    if not f.lower().endswith(('.htm','.html')): continue
    o=os.path.join(dst,os.path.splitext(f)[0]+'.txt')
    if os.path.exists(o) and os.path.getsize(o)>0: continue
    with open(o,'w') as fh: subprocess.run([sys.executable,'-I',os.path.join(os.path.dirname(__file__),'h2t.py'),os.path.join(src,f)],stdout=fh,stderr=subprocess.DEVNULL)
