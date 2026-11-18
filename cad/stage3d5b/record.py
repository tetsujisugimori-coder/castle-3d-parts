"""Preserve exact current checkout inputs and command logs, including failure."""
import datetime, hashlib, importlib.util, json, os
from pathlib import Path
import subprocess, sys

ROOT=Path(__file__).resolve().parents[2]

def main():
    out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
    command=sys.argv[2:]
    if command[:1]==['--']:command=command[1:]
    spec=importlib.util.spec_from_file_location('d4_source_set',ROOT/'cad/stage3d4/source_set.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    paths=module.source_paths(ROOT)
    paths+=list((ROOT/'cad/stage3d5b').glob('*.py'))+list((ROOT/'cad/stage3d5').glob('*.py'))
    paths+=list((ROOT/'docs/stage3d5b').glob('*.md'))+[ROOT/'.github/workflows/stage3d5b.yml']
    manifest={}
    for p in sorted(set(paths)):
        rel=p.relative_to(ROOT);dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        raw=p.read_bytes();dst.write_bytes(raw)
        manifest[rel.as_posix()]={'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    git=lambda *args:subprocess.check_output(['git','-c','safe.directory='+str(ROOT),*args],cwd=ROOT,text=True).strip()
    now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
    record={'command':command,'git':git('show','-s','--format=%H %T %P'),
            'submitted_head':os.environ.get('SUBMITTED_HEAD'),'status':git('status','--porcelain'),
            'started_utc':now(),'source_bytes':manifest}
    (out/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    with (out/'stdout.log').open('wb') as so,(out/'stderr.log').open('wb') as se:
        try:code=subprocess.run(command,cwd=ROOT,stdout=so,stderr=se).returncode
        except Exception as error:se.write(repr(error).encode());code=127
    record.update(exit_code=code,ended_utc=now())
    (out/'execution.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'command':command,'exit_code':code,'git':record['git']}))
    return code

if __name__=='__main__':sys.exit(main())
