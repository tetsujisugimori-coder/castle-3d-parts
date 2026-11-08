"""Replay preserved independent inputs against old and fixed implementations.
Run: PW_MODULE=/path/playwright/index.mjs THREE_DIR=/path/three /usr/bin/python3 .../replay.py
Original scripts/snapshots are never edited. Path substitutions affect both conditions identically.
"""
from pathlib import Path
import tempfile, shutil, subprocess, os, json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=Path(tempfile.mkdtemp(prefix='palisade-independent-replay-'))
REPO=OUT/'repo'
shutil.copytree(ROOT,REPO,ignore=shutil.ignore_patterns('.git','dist','node_modules','__pycache__','*.FCBak','*.blend1'))
rows=[]
def run(label,args):
    r=subprocess.run(args,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (OUT/(label+'.log')).write_text(r.stdout)
    rows.append({'label':label,'exit':r.returncode})
    return r
# Same original CAD runner; only relocatable working/output directory changes.
runner=(HERE/'audit_reopen.py').read_text().replace('/tmp/castle-cad-independent/repo',str(REPO)).replace('/tmp/castle-cad-independent/',str(OUT)+'/')
p=OUT/'audit_reopen.py';p.write_text(runner)
fixed=(REPO/'cad/prototype-v1/build.py').read_bytes()
(REPO/'cad/prototype-v1/build.py').write_bytes((HERE/'pre-review-build.py.txt').read_bytes())
r=run('cad-red',['/usr/bin/python3',str(p)]);assert r.returncode!=0 and '/template.svg' in r.stdout
(REPO/'cad/prototype-v1/build.py').write_bytes(fixed)
r=run('cad-green',['/usr/bin/python3',str(p)]);assert r.returncode==0
# Same two missing-source-set inputs against old/fixed validator.
f=REPO/'scripts/cad-prototype.mjs';fixed=f.read_bytes()
code="""import{validateSnapshot}from './scripts/cad-prototype.mjs';import{readFileSync}from'node:fs';const results=[];for(const all of[true,false]){const s=JSON.parse(readFileSync('cad/prototype-v1/reference-snapshot.json'));if(all)s.source_hashes={};else delete s.source_hashes['design/cad-reference.json'];try{validateSnapshot(s);results.push('accepted')}catch(e){results.push(e.message)}}console.log(JSON.stringify(results))"""
f.write_bytes((HERE/'pre-review-cad-prototype.mjs.txt').read_bytes());r=run('provenance-red',['node','--input-type=module','-e',code]);assert json.loads(r.stdout)==['accepted','accepted']
f.write_bytes(fixed);r=run('provenance-green',['node','--input-type=module','-e',code]);assert json.loads(r.stdout)==['SOURCE_SET','SOURCE_SET']
pw=os.environ.get('PW_MODULE');three=os.environ.get('THREE_DIR')
if pw and three:
    runner=(HERE/'context-race.mjs').read_text().replace('/tmp/yamanaka-h-resume/repo/node_modules/playwright/index.mjs',pw).replace('/tmp/yamanaka-h-resume/repo/node_modules/three/',str(Path(three))+'/').replace('/workspace/scratch/e622c1e9421e/castle-cad-track-a/site/cad',str(REPO/'site/cad')).replace('/tmp/castle-cad-independent/context-race-result.json',str(OUT/'context-result.json'))
    p=OUT/'context-race.mjs';p.write_text(runner);f=REPO/'site/cad/app.js';fixed=f.read_bytes()
    f.write_bytes((HERE/'pre-review-app.js.txt').read_bytes());r=run('context-red',['node',str(p)]);assert r.returncode==0
    data=json.loads((OUT/'context-result.json').read_text());assert data['disabled'] is False and data['loaded']=='true'
    shutil.copyfile(OUT/'context-result.json',OUT/'context-red.json')
    f.write_bytes(fixed);r=run('context-green',['node',str(p)]);assert r.returncode==0
    data=json.loads((OUT/'context-result.json').read_text());assert data['disabled'] is True and data['loaded'] is None
    shutil.copyfile(OUT/'context-result.json',OUT/'context-green.json')
else:rows.append({'label':'context','status':'NOT_TESTED','reason':'Set PW_MODULE and THREE_DIR'})
(OUT/'results.json').write_text(json.dumps(rows,indent=2));print(OUT);print(json.dumps(rows))
