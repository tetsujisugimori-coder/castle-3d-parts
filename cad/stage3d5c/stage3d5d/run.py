"""Local cross-environment recorder; no install, delete, repair or proof promotion."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='923bda856015398e1578f66bfc9b5d6553cf49a1'

def git(*args):return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);tmp=out/'tmp';tmp.mkdir();os.environ['TMPDIR']=str(tmp)
    paths=git('ls-tree','-rz','--name-only',BASE).decode().split('\0')[:-1];base={}
    for p in paths:
        b=git('show',BASE+':'+p);a=(ROOT/p).read_bytes()
        if a!=b:raise ValueError('EXISTING_ASSET_CHANGED:'+p)
        base[p]={'size':len(b),'sha256':sha(b)}
    write(out/'base-manifest.json',base)
    new=[p.relative_to(ROOT).as_posix() for d in ['cad/stage3d5c/stage3d5d','docs/stage3d5c/stage3d5d'] for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    sources={}
    for p in sorted(set(paths+new)):
        b=(ROOT/p).read_bytes();dest=out/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);sources[p]={'size':len(b),'sha256':sha(b)}
    write(out/'source-manifest.json',sources)
    write(out/'identity.json',{'git':git('show','-s','--format=%H %T %P').decode().strip(),'source_status':git('status','--porcelain').decode(),'base':BASE,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    cmds=[]
    def command(name,args,allowed=(0,)):
        with (out/(name+'.stdout')).open('wb') as so,(out/(name+'.stderr')).open('wb') as se:r=subprocess.run(args,cwd=ROOT,stdout=so,stderr=se).returncode
        cmds.append({'name':name,'argv':args,'exit':r});write(out/'commands.json',cmds)
        if r not in allowed:raise ValueError('COMMAND_FAILED:'+name)
        return r
    command('inherited5c-with-add-only5d',['/usr/bin/python3','-B','cad/stage3d5c/run.py',str(out/'inherited5c'),'--native'])
    rc=command('direct-occt',[sys.executable,'-B','cad/stage3d5c/stage3d5d/direct_capture.py',str(out/'direct')],(0,2))
    for p,r in sources.items():
        if sha((ROOT/p).read_bytes())!=r['sha256']:raise ValueError('EXECUTION_SOURCE_CHANGED:'+p)
    write(out/'results.json',{'existing_assets_unchanged':'PASS','local_inherited_suite':'PASS','direct_occt_capture':'PASS' if rc==0 else 'BLOCKED','independent_new_dedicated_CI':'BLOCKED','native_material_outer':'UNKNOWN','native_void_inner':'UNKNOWN','native8errors':'UNKNOWN','native_allstate_motion':'UNKNOWN','representative_native':'NOT_TESTED','actual_intervals_evaluated':0,'expand_to128':False})
    manifest={p.relative_to(out).as_posix():{'size':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in out.rglob('*') if p.is_file()}
    write(out/'manifest.json',manifest)
if __name__=='__main__':main(sys.argv[1])
