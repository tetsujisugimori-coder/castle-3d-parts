"""Audit dedicated D4 ZIP against the checked-out execution source, not declarations."""
import hashlib,json,sys,zipfile
from pathlib import Path
from bridge import ROOT,PARTS,sources,assess
from source_set import source_paths
from run import build_report
sys.path.insert(0,str(ROOT/'cad/stage3d3'))
from audit_zip import audit as source_audit

def audit(path):
    base=source_audit(path)
    expected_sources={str(p.relative_to(ROOT)):p.read_bytes() for p in source_paths()}
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip():raise ValueError('ZIP_INTEGRITY')
        records=[n for n in names if n.endswith('/execution.json')]
        expected={'portable','archive-controls','native-command','d1-regression','d2-regression','d3-regression','analytical'}
        if {n.split('/')[-2] for n in records}!=expected or len(records)!=len(expected):raise ValueError('EXECUTION_SET')
        for n in records:
            r=json.loads(z.read(n));prefix=n.rsplit('/',1)[0]+'/source/'
            if r.get('status')!='PASS' or r.get('exit_code')!=0:raise ValueError('COMMAND_FAILED:'+n)
            if set(r['sources'])!=set(expected_sources):raise ValueError('FIXED_SOURCE_SET_MISMATCH')
            for p,b in expected_sources.items():
                if z.read(prefix+p)!=b:raise ValueError('SOURCE_CHECKOUT_BYTES_MISMATCH:'+p)
            for suffix in ['stdout.log','stderr.log']:
                if n.rsplit('/',1)[0]+'/'+suffix not in names:raise ValueError('LOG_MISSING')
        def unique(suffix):
            found=[n for n in names if n==suffix.lstrip('/') or n.endswith(suffix)]
            if len(found)!=1:raise ValueError('RESULT_MISSING_OR_DUPLICATED:'+suffix)
            return found[0],json.loads(z.read(found[0]))
        native_path,native=unique('/native/native.json');_,analytical=unique('/analytical.json')
        if native.get('sources_before')!=sources() or native.get('sources_after')!=sources():raise ValueError('NATIVE_INPUT_IDENTITY')
        expected_cases=['original','bolt_enlarged','hole_shrunk','placement_shift','orientation_reversed','missing_face_open_shell','unsupported_curved','extra_solid']
        if [r.get('case') for r in native.get('rows',[])]!=expected_cases:raise ValueError('NATIVE_CASE_SET')
        for r in native['rows']:
            data=r.get('input',{})
            if data.get('sources')!=sources() or set(data.get('parts',{}))!=set(PARTS):raise ValueError('NATIVE_INPUT_MISSING')
            for part in data['parts'].values():
                required={'brep_sha256','placement','valid','closed','solids','shells','solid_orientations','shell_orientations','faces','bounds_observed','tolerance_observed'}
                if set(part)!=required or not part['faces']:raise ValueError('NATIVE_TOPOLOGY_MISSING')
                for f in part['faces']:
                    if set(f)!={'surface','orientation','wires','normal_observed','area_observed'} or not f['wires']:raise ValueError('NATIVE_FACE_MISSING')
                    for w in f['wires']:
                        if set(w)!={'orientation','closed','edges'} or not w['edges']:raise ValueError('NATIVE_WIRE_MISSING')
                        for e in w['edges']:
                            if set(e)!={'curve','orientation','vertices','length_observed','tolerance_observed'}:raise ValueError('NATIVE_EDGE_MISSING')
            if r.get('assessment')!=assess(data):raise ValueError('NATIVE_ASSESSMENT_MISMATCH')
            if r['case']!='original' and (r.get('BRep_changed') is not True or r.get('fixed_observation_match')!='REJECTED_BREP_CHANGED'):raise ValueError('NATIVE_MUTATION_MISSING')
        prefix=native_path.rsplit('/',1)[0]+'/'
        base_parts=native['rows'][0]['input']['parts']
        for name in PARTS:
            raw=z.read(prefix+name+'.brep')
            if hashlib.sha256(raw).hexdigest()!=base_parts[name]['brep_sha256']:raise ValueError('ORIGINAL_BREP_MISMATCH')
        for row in native['rows'][1:]:
            for part in PARTS:
                raw=z.read(prefix+row['case']+'/'+part+'.brep')
                if hashlib.sha256(raw).hexdigest()!=row['input']['parts'][part]['brep_sha256']:raise ValueError('ROW_BREP_MISMATCH')
            changed=[p for p in PARTS if row['input']['parts'][p]['brep_sha256']!=base_parts[p]['brep_sha256']]
            if len(changed)!=1:raise ValueError('MUTATION_TARGET_MISMATCH')
            raw=z.read(prefix+row['case']+'.brep')
            if hashlib.sha256(raw).hexdigest()!=row['input']['parts'][changed[0]]['brep_sha256']:raise ValueError('MUTANT_BREP_MISMATCH')
        if analytical!=build_report():raise ValueError('ANALYTICAL_RECOMPUTATION_MISMATCH')
    return dict(base,d4_command_count=len(records),native_case_count=8,analytical_intervals=128,cad_unknown=128,source_checkout_match=True)
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
