"""Capture actual source bytes before a command; preserve failed executions."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
root=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
command=sys.argv[2:]
if command[:1]==['--']:command=command[1:]
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+str(root),*args],cwd=root,text=True).strip()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
paths=[p for p in (root/'cad/stage3d4').glob('*.py')]+list((root/'docs/stage3d4').glob('*.md'))
paths += [root/p for p in json.loads((root/'cad/stage3d2/contract.json').read_text())['sources']]
paths += list((root/'cad/stage3d1').glob('*.py')) + list((root/'cad/stage3d2').glob('*.py')) + list((root/'cad/stage3d3').glob('*.py'))
paths += [root/'cad/stage3d2/contract.json',root/'.github/workflows/stage3d4.yml',root/'scripts/stage3c-hash-evidence.py']
# Regression commands consume these additional source/input trees. Preserve raw bytes,
# not only hashes. No old bulky evidence archives are copied.
for folder in ['cad/stage3c','cad/stage3b','tests','scripts','site','catalog','research','observations','sources','design']:
    paths += [p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.mjs','.js','.json','.html','.css') and 'evidence' not in p.parts and 'generated' not in p.parts]
paths=sorted(set(paths))
manifest={}
for p in paths:
    rel=p.relative_to(root);dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
    raw=p.read_bytes();dst.write_bytes(raw)
    manifest[str(rel)]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
        'git_blob_sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
record={'command':command,'git':git('show','-s','--format=%H %T %P'),'started_at':now(),
        'dirty_status':git('status','--porcelain'),'sources':manifest,'status':'RUNNING'}
path=out/'execution.json';path.write_text(json.dumps(record,indent=2))
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
    try:
        run=subprocess.run(command,stdout=stdout,stderr=stderr)
        code=run.returncode
    except Exception as error:
        stderr.write((type(error).__name__+': '+str(error)).encode());code=127
record.update(ended_at=now(),exit_code=code,status='PASS' if code==0 else 'FAIL')
path.write_text(json.dumps(record,indent=2));print(json.dumps(record));sys.exit(code)
