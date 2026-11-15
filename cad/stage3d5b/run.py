"""Fresh synthetic evidence and unmodified D4 interval regression; no native promotion."""
import hashlib, importlib.util, json
from pathlib import Path
import sys
from fractions import Fraction as F
from boundary_contract import validate_observation, void_rectangle, aggregate_intervals
from test_boundary_contract import fixture, fault_cases

ROOT=Path(__file__).resolve().parents[2]

def main(out):
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for name,reason,data,anchors in fault_cases():
        result=validate_observation(data,anchors)
        if result!={'status':'FAIL','reason':reason}:raise AssertionError(name)
        rows.append({'id':name,'input':data,'anchors':anchors,'expected':{'status':'FAIL','reason':reason},'actual':result})
    normal=validate_observation(*fixture())
    if normal['status']!='PASS':raise AssertionError('normal')
    contact=[]
    for name,dy,expected in [('contact',F(0),'FAIL'),('micro-separation',-F(1,10**12),'PASS'),('micro-intrusion',F(1,10**12),'FAIL')]:
        args=['1','0','0','0','3/5',str(F(4,5)+dy),'1/1000000000000000']
        result=void_rectangle(*args)
        if result['status']!=expected:raise AssertionError(name)
        contact.append({'id':name,'input':args,'expected':expected,'actual':result,
                        'semantics':'closed rectangle in open empty disk; boundary is material'})
    sys.path.insert(0,str(ROOT/'cad/stage3d4'))
    spec=importlib.util.spec_from_file_location('d4_fresh_report',ROOT/'cad/stage3d4/run.py')
    d4=importlib.util.module_from_spec(spec);spec.loader.exec_module(d4)
    analytical=d4.build_report()
    counts=aggregate_intervals([r['status'] for r in analytical['analytical']['intervals']])
    report={'scope':'synthetic contracts + fresh unchanged D4 exact-model interval regression',
            'normal':normal,'fault_input_count':len(rows),'fault_inputs':rows,'contact_cases':contact,
            'analytical_counts':counts,'real_CAD_counts':aggregate_intervals(['NOT_TESTED']*128),
            'prior_D4_real_CAD_counts':analytical['cad_counts'],
            'prior_status_scope':'D4 assessment UNKNOWN128 remains separate from unexecuted D5B interval tests',
            'D2_contract_sha256':hashlib.sha256((ROOT/'cad/stage3d2/contract.json').read_bytes()).hexdigest(),
            'real_brep_inclusion':'UNKNOWN','finite_real_error':'UNKNOWN',
            'cad_connection':'NOT CONNECTED: real correspondence, finite errors and continuous motion unproved'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (out/'d4-fresh-regression.json').write_text(json.dumps(analytical,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'analytical':counts,'real_CAD':report['real_CAD_counts'],'faults':len(rows)}))

if __name__=='__main__':main(Path(sys.argv[1]))
