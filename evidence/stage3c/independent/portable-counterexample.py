import sys,json,tempfile,shutil,copy,hashlib
from pathlib import Path
root=Path.cwd();out=root/'evidence/stage3c/independent';src=root/'cad/stage3c/generated';sys.path.insert(0,str(root/'cad/stage3c'))
import check
old={ '__file__':str(root/'cad/stage3c/check.py'),'__name__':'before_check'};exec((out/'before-portable-check.py.txt').read_text(),old)
rows=[]
for name in ['missing_sources','duplicate_contacts']:
 d=Path(tempfile.mkdtemp(dir=out/'tmp'));shutil.copytree(src,d/'candidate');d=d/'candidate';m=json.loads((d/'manifest.json').read_text())
 if name=='missing_sources':m['source_hashes']={}
 else:
  p=d/'state-audit.json';s=json.loads(p.read_text());s['contacts'][-1]=copy.deepcopy(s['contacts'][0]);p.write_text(json.dumps(s));m['evidence_hashes']['state-audit.json']=hashlib.sha256(p.read_bytes()).hexdigest()
 (d/'manifest.json').write_text(json.dumps(m));r={'mutation':name}
 for key,func in [('before',old['check']),('after',check.check)]:
  try:func(d);r[key]='ACCEPTED'
  except Exception as e:r[key]='REJECTED';r[key+'_reason']=str(e)
 rows.append(r)
(out/'portable-counterexample.json').write_text(json.dumps(rows,indent=2))
assert all(r['after']=='REJECTED' for r in rows),rows
print(rows)
