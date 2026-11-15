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
from source_set import source_paths
paths=source_paths(root)
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
