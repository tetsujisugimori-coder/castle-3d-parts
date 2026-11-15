"""Audit a dedicated D4 ZIP. CI green does not substitute for this check."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cad/stage3d3'))
from audit_zip import audit as source_audit

def audit(path):
    base=source_audit(path)
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip():raise ValueError('ZIP_INTEGRITY')
        records=[n for n in names if n.endswith('/execution.json')]
        expected={'portable','archive-controls','native-command','d1-regression','d2-regression','d3-regression','analytical'}
        if {n.split('/')[-2] for n in records}!=expected or len(records)!=len(expected):raise ValueError('EXECUTION_SET')
        for n in records:
            r=json.loads(z.read(n))
            if r.get('status')!='PASS' or r.get('exit_code')!=0:raise ValueError('COMMAND_FAILED:'+n)
            if '.github/workflows/stage3d4.yml' not in r['sources']:raise ValueError('HIDDEN_SOURCE_MISSING')
            for suffix in ['stdout.log','stderr.log']:
                if n.rsplit('/',1)[0]+'/'+suffix not in names:raise ValueError('LOG_MISSING')
        def unique(suffix):
            found=[n for n in names if n.endswith(suffix)]
            if len(found)!=1:raise ValueError('RESULT_MISSING_OR_DUPLICATED:'+suffix)
            return json.loads(z.read(found[0]))
        native=unique('/native/native.json');analytical=unique('/analytical.json')
        if native['sources_before']!=native['sources_after']:raise ValueError('ORIGINAL_CHANGED')
        expected_cases=['original','bolt_enlarged','hole_shrunk','placement_shift','orientation_reversed','missing_face_open_shell','unsupported_curved','extra_solid']
        if [r['case'] for r in native['rows']]!=expected_cases:raise ValueError('NATIVE_CASE_SET')
        for r in native['rows']:
            if r['assessment']['cad_intervals']!={'PASS':0,'FAIL':0,'UNKNOWN':128}:raise ValueError('UNSUPPORTED_CAD_PROMOTION')
        if analytical['analytical_counts']!={'PASS':128,'FAIL':0,'UNKNOWN':0} or analytical['cad_counts']!={'PASS':0,'FAIL':0,'UNKNOWN':128}:raise ValueError('ANALYTICAL_CAD_MIXUP')
    return dict(base,d4_command_count=len(records),native_case_count=8,analytical_intervals=128,cad_unknown=128)
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
