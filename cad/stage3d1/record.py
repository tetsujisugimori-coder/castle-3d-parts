"""Capture command logs and repository identity; no persistent Git configuration."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
command=sys.argv[2:]
if command[:1]==['--']:command=command[1:]
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+str(root),*args],cwd=root,text=True).strip()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
record={'command':command,'git':git('show','-s','--format=%H %T %P'),'started_at':now(),'status':'RUNNING','sources':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'cad/stage3d1').glob('*.py')}}
path=out/'execution.json';path.write_text(json.dumps(record,indent=2))
with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
 run=subprocess.run(command,stdout=stdout,stderr=stderr)
record.update(ended_at=now(),exit_code=run.returncode,status='PASS' if run.returncode==0 else 'FAIL',logs_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.log')})
path.write_text(json.dumps(record,indent=2));print(json.dumps(record));sys.exit(run.returncode)
