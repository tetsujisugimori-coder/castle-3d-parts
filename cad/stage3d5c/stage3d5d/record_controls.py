"""Complete portable controls. These are synthetic observation/proof claims."""
from pathlib import Path
import copy,json,hashlib,zipfile
from .gates import ERRORS,REQUIRED,assess,conditional_clearance,sampling_record
from .evidence_contract import audit_archive,compare_reference

def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def record(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);cases=[]
    ref={'storage_origin':'STORED','trim_uses':['end-a','wall1','wall2','wall3','wall4','end-b'],'orientation':'Forward','void_extra_material':False,'end_closed':True,'location_applications':1}
    for name,key,value in [('origin-mislabel','storage_origin','GENERATED'),('trim-missing','trim_uses',['end-a']),('orientation-reversed','orientation','Reversed'),('void-extra-material','void_extra_material',True),('end-not-closed','end_closed',False),('double-transform','location_applications',2)]:
        c=copy.deepcopy(ref);c[key]=value;r=compare_reference(c,ref)
        assert r['status']=='FAIL';cases.append({'id':name,'scope':'synthetic observation JSON, not mutated BRep','reference':ref,'input':c,'expected':'FAIL','actual':r})
    cases.insert(0,{'id':'normal-record','scope':'synthetic observation JSON','input':ref,'reference':ref,'expected':'PASS','actual':compare_reference(ref,ref)})
    props={k:{'kind':'claimed_native_theorem','status':'PASS','sha256':'f'*64} for k in REQUIRED}
    errors={k:{'kind':'sample_maximum','status':'PASS','upper_m':'0'} for k in ERRORS}
    result=assess(props,errors,'PASS');assert result['representative']=='NOT_TESTED'
    cases.append({'id':'forged-pass-zero-error','input':{'propositions':props,'errors':errors,'claim':'PASS'},'expected':'NOT_TESTED','actual':result,'scope':'untrusted proof claim, no certificate issuer'})
    cases.append({'id':'sample23-zero','input':{'maxdev':'0','nb_control':23},'expected_continuous_upper':None,'actual':sampling_record('0'),'scope':'analytical semantics of sampled maximum'})
    # Understated sum countercheck is exact supplied arithmetic, not native truth.
    terms={k:'1/10000' for k in ERRORS};computed=sum(__import__('fractions').Fraction(v) for v in terms.values())
    reported='7/10000';assert __import__('fractions').Fraction(reported)<computed
    cases.append({'id':'underreported-error-sum','input':{'terms':terms,'reported_sum':reported},'expected':'FAIL','actual':{'status':'FAIL','reason':'REPORTED_SUM_BELOW_EXACT_SUM','required_sum':str(computed)},'scope':'synthetic exact error inputs'})
    payload={'source/.github/workflows/synthetic.yml':b'synthetic hidden fixture\n','source/runner.py':b'synthetic runner fixture\n'}
    expected={k:{'size':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in payload.items()}
    for name,selected,want in [('complete',payload,'PASS'),('hidden-missing',{'source/runner.py':payload['source/runner.py']},'FAIL'),('source-free',{},'FAIL')]:
        p=out/(name+'.zip')
        with zipfile.ZipFile(p,'w') as z:
            for k,v in selected.items():z.writestr(k,v)
        result=audit_archive(p,expected);assert result['status']==want
        cases.append({'id':name,'input_zip':p.name,'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'expected_inventory':expected,'expected':want,'actual':result,'scope':'synthetic archive packaging; old artifact not modified'})
    write(out/'full-controls.json',cases)
    write(out/'summary.json',{'cases':len(cases),'matched':len(cases),'native_geometric_tests':0,'actual_interval':'NOT_TESTED','scope':'portable contract tests only'})
    return cases
