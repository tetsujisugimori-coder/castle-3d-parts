"""Run one check without a timeout/kill; retain raw logs and exact source identity."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

out = Path(sys.argv[1]).resolve()
command = sys.argv[2:]
if command and command[0] == '--':
    command = command[1:]
out.mkdir(parents=True, exist_ok=False)


def git(*args):
    return subprocess.check_output(['git', *args]).decode('utf-8').strip()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


sources = {}
for name in subprocess.check_output(['git','ls-files','-z']).decode().split('\0'):
    if name:
        sources[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
# Untracked additions are also execution inputs before the submission commit.
for name in subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0'):
    if name and (name.startswith(('scripts/','tests/','cad/','site/')) or name=='evidence/stage3c/shared-viewer-exceptions.json' or name.endswith('-permitted.patch')) and '__pycache__' not in name:
        sources[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
record = {'command':command, 'head':git('rev-parse','HEAD'),
          'tree':git('show','-s','--format=%T','HEAD'),
          'working_tree':git('status','--porcelain'), 'sources':sources,
          'platform':platform.platform(), 'python':platform.python_version(),
          'node':subprocess.check_output(['node','--version']).decode().strip(),
          'started_at':now(), 'status':'RUNNING'}
record_path = out/'execution.json'
record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
with (out/'stdout.log').open('wb') as stdout, (out/'stderr.log').open('wb') as stderr:
    run = subprocess.run(command, stdout=stdout, stderr=stderr)
record.update(ended_at=now(),exit_code=run.returncode,status='PASS' if run.returncode==0 else 'FAIL')
text=(out/'stdout.log').read_text(encoding='utf-8',errors='replace')+'\n'+(out/'stderr.log').read_text(encoding='utf-8',errors='replace')
counts={}
for label in ['tests','pass','fail','cancelled','skipped','todo']:
    match=re.search(r'\b'+label+r' (\d+)\s*$',text,re.MULTILINE)
    if match:
        counts[label]=int(match.group(1))
match=re.search(r'Ran (\d+) tests?',text)
if match:
    counts['tests']=int(match.group(1))
    if re.search(r'^OK\s*$',text,re.MULTILINE):
        counts.update(passed=counts['tests'],failed=0)
record['counts']=counts
record['logs_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'stdout.log',out/'stderr.log']}
record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:record[k] for k in ['command','status','exit_code','started_at','ended_at']}))
sys.exit(run.returncode)
