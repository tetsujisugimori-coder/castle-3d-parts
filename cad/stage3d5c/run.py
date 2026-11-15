"""One isolated run, immutable past output directories; all base bytes protected."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,datetime,copy
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cad/stage3d5b'))
import native
sys.path.insert(0,str(ROOT/'cad/stage3d2'))
import proof
from proof_contract import ERROR_DOMAINS,NATIVE_OBLIGATIONS,representative,line_plane_identity,fixed_path_controls,chain,error_sum
BASE='6ed080ff38e50c7cb808d42ff0c36aeafc118ecd'

def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+str(ROOT),*a],cwd=ROOT)
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def preserve(out):
    base=git('ls-tree','-r','-z',BASE).split(b'\0')[:-1];rows={}
    for row in base:
        meta,name=row.split(b'\t');p=name.decode();raw=git('show',BASE+':'+p);actual=(ROOT/p).read_bytes()
        if p!='LOG.md' and raw!=actual:raise ValueError('BASE_BYTES_CHANGED:'+p)
        if p=='LOG.md' and not actual.startswith(raw):raise ValueError('LOG_HISTORY_NOT_PRESERVED')
        rows[p]={'size_bytes':len(raw),'sha256':sha(raw),'current_size':len(actual),'current_sha256':sha(actual),'equal':raw==actual,'allowed_additive_log':p=='LOG.md'}
    write(out/'base-preservation.json',rows)
    paths=git('ls-files','-z').decode().split('\0')[:-1]
    base_paths=set(rows)
    added=set(paths)-base_paths
    if any(not (p.startswith(('cad/stage3d5c/','docs/stage3d5c/')) or p=='.github/workflows/stage3d5c.yml') for p in added):raise ValueError('UNAPPROVED_ADDED_PATH')
    if base_paths-set(paths):raise ValueError('REMOVED_TRACKED_PATH')
    paths+= [p.relative_to(ROOT).as_posix() for d in ('cad/stage3d5c','docs/stage3d5c') for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    paths+=['.github/workflows/stage3d5c.yml']
    manifest={}
    for p in sorted(set(paths)):
        raw=(ROOT/p).read_bytes();dst=out/'source'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
        manifest[p]={'size_bytes':len(raw),'sha256':sha(raw)}
    write(out/'source-manifest.json',manifest)
    return manifest

def main(out,with_native):
    out.mkdir(parents=True,exist_ok=False);tmp=out/'tmp';tmp.mkdir();os.environ['TMPDIR']=str(tmp.resolve())
    m=preserve(out);write(out/'identity.json',{'git':git('show','-s','--format=%H %T %P').decode().strip(),'submitted_head':os.environ.get('SUBMITTED_HEAD'),'status':git('status','--porcelain').decode(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base':BASE})
    commands=[]
    def run(label,args):
        with (out/(label+'.stdout')).open('wb') as so,(out/(label+'.stderr')).open('wb') as se:
            rc=subprocess.run(args,cwd=ROOT,stdout=so,stderr=se).returncode
        commands.append({'id':label,'argv':args,'exit_code':rc});write(out/'commands.json',commands)
        if rc:raise RuntimeError('COMMAND_FAILED:'+label)
    run('new-tests',[sys.executable,'-B','-m','unittest','discover','-s','cad/stage3d5c','-p','test_*.py','-v'])
    run('existing-5b-tests',[sys.executable,'-B','-m','unittest','discover','-s','cad/stage3d5b','-p','test_*.py','-v'])
    run('existing-5-tests',[sys.executable,'-B','-m','unittest','discover','-s','cad/stage3d5','-p','test_*.py','-v'])
    c=json.loads(native.CONTRACT.read_bytes());sources={p:sha((ROOT/p).read_bytes()) for p in c['sources']}
    r=proof.verify(c,'9e8bb54754f2ce8ff0623bc5a2676788f22ec2154f4da98c66939eaae0b287a2',sources)
    assert len(r['intervals'])==128 and all(x['status']=='PASS' for x in r['intervals'])
    write(out/'analytical128.json',r)
    chosen=r['intervals'][0];assessment=representative(chosen,dict.fromkeys(ERROR_DOMAINS,None))
    write(out/'representative.json',{'id':'D2-ordinal-0','selection':'first unchanged adaptive leaf; smallest travel near closed baseline; no extrapolation','contract_sha256':sha(native.CONTRACT.read_bytes()),'assessment':assessment})
    from test_proof_contract import fixture
    cases=[]
    def case(id,inp,fn,expected):
        res=fn(inp);cases.append({'id':id,'input':inp,'expected':expected,'actual':res,'scope':'synthetic mathematical definitions, not native collision'})
        assert res['status']==expected,id
    case('normal-line-plane',fixture(),line_plane_identity,'PASS')
    for field,index in [('c0',0),('c1',0),('p0',1),('p1',0),('origin',2),('u_axis',2),('v_axis',2)]:
        f=fixture();f[field][index]=str(int(f[field][index])+1);case(field+'-inconsistent',f,line_plane_identity,'FAIL')
    entries,ids=fixed_path_controls()
    for label,e in [('normal',entries),('double-location',entries[:1]+entries),('missing-parent',entries[:1]+entries[2:]),('wrong-order',entries[::-1])]:
        case(label,e,lambda x:chain(x,ids,'local','m-world'),'PASS' if label=='normal' else 'FAIL')
    wrong=copy.deepcopy(entries);wrong[-1]['matrix']=list(entries[0]['matrix']);case('wrong-unit',wrong,lambda x:chain(x,ids,'local','m-world'),'FAIL')
    b=dict.fromkeys(ERROR_DOMAINS,'1/10000');case('underreported-error',{'bounds':b,'reported':'7/10000'},lambda x:error_sum(x['bounds'],x['reported']),'FAIL')
    run('between-samples-control',[sys.executable,'-B','cad/stage3d2/run.py',str(out/'model-between-samples')])
    write(out/'controls.json',cases)
    if with_native:
        run('native-capture',[sys.executable,'-B','cad/stage3d5c/native_capture.py',str(out/'native')])
        from audit_observation import controls
        captured=json.loads((out/'native/native-capture.json').read_bytes())
        write(out/'native-observation-controls.json',{name:controls(row) for name,row in captured['records'].items()})
        run('isolated-document',[sys.executable,'-B','cad/stage3d5b/planar_document.py',str(out/'document')])
    for p,row in m.items():
        if sha((ROOT/p).read_bytes())!=row['sha256']:raise ValueError('EXECUTION_SOURCE_CHANGED:'+p)
    write(out/'results.json',{'technical_execution':'PASS','native_capture':'PASS' if with_native else 'NOT_TESTED','native_material':'UNKNOWN','native_void':'UNKNOWN','finite_real_error':'UNKNOWN','all_state_equivalence':'UNKNOWN','representative_native':'NOT_TESTED','current_native128':{'NOT_TESTED':128},'historical_D4_native128':{'UNKNOWN':128},'historical_D5B_native128':{'NOT_TESTED':128},'analytical128':{'PASS':128},'independent_kernel':'NOT_TESTED','source_unchanged':'PASS','physical_safety':'NOT_TESTED'})
    manifest={p.relative_to(out).as_posix():{'size_bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in out.rglob('*') if p.is_file()}
    write(out/'manifest.json',manifest)

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),'--native' in sys.argv)
