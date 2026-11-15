"""Independent post-transplant arithmetic/contract checker.

Imports ONLY --candidate-dir, never a historical HERE/candidate. Writes new
artifacts only. Reference arithmetic uses four corner expressions and divmod,
separate from the implementation formulas. Shared assumptions: Fraction,
declared exact synthetic geometry, and closed material/open void semantics.
This is not a FreeCAD/OCCT or real-BRep inclusion certificate.
"""
import argparse
import copy
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys


PRESERVED_HASHES = {
    'boundary_contract.py': '42dd5d5f24a6a12ff6d9c68fe3eb50adb5a8173b55d3afb8ab62d904a64f8b51',
    'circular_contract.py': 'd848af9b6745c86478b4a7fcab7214354aef979b181ae0ea2816f3b11ff83289',
    'test_boundary_contract.py': '892696f9c015850c04ad9a74e8d706cf12e9bf347a3e904bcd1c56b1fe2ea96d',
    'test_circular_contract.py': '63197b571ec57251c78e586b835170aab8f052c81856c67d72baff4040d5be73',
}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normal():
    """Reviewer fixture, separate from test_boundary_contract.fixture()."""
    h=lambda s: hashlib.sha256(s.encode()).hexdigest()
    faces={'xmin':'-X','xmax':'+X','ymin':'-Y','ymax':'+Y','zmin':'-Z','zmax':'+Z','bore':'toward-axis'}
    body={'valid':True,'closed':True,'solids':1,'faces':faces,
          'box_m':['-2','-2','-1','2','2','1'],
          'hole':{'kind':'circular-through-Z','center_xy_m':['1/10','-1/10'],
                  'radius_m':'1/4','wall_role':'bore','openings':['zmin','zmax']},
          'placement':{'rotation':['0','-1','0','1','0','0','0','0','1'],
                       'translation_m':['1/3','-2/5','7/9']}}
    record={'object_id':'GATE_BoltGuide_Left','shape_sha256':h('reviewer synthetic shape'),
            'fcstd_sha256':h('reviewer synthetic file'),'axis_local':['0','0','1'],
            'raw_unit':'mm','geometry_unit':'m','scale_to_m':'1/1000',
            'placement_applications':1,'transform_order':['scale','rotate','translate'],
            'primitive_frame':'local','brep_tolerance_m':'0','tolerance_budget_m':'0'}
    geometry={'kind':'synthetic-box-through-cylinder-v1','unit':'m','source':body,
              'model':copy.deepcopy(body),'face_mapping':{k:k for k in faces},
              'errors_m':{k:'0' for k in ['approximation','transform','distance_rounding','representation','pose','motion']},
              'rounding':{'exact_upper_m':'2/7','quantum_m':'1/1000','reported_upper_m':'143/500'}}
    data={'schema':'synthetic-observation-v1','manifest_sha256':h('reviewer manifest'),
          'evidence':{k:'reviewer synthetic definition/'+k for k in ['input','topology','geometry','placement','tolerance']},
          'records':{'source':copy.deepcopy(record),'model':copy.deepcopy(record)},'geometry':geometry}
    anchors={'manifest_sha256':data['manifest_sha256'],
             **{k:{f:record[f] for f in ['object_id','shape_sha256','fcstd_sha256']} for k in ['source','model']}}
    return data,anchors


def mutations():
    return [
      ('I17-01-radius-larger','hole-radius-correspondence',lambda d:d['geometry']['model']['hole'].update(radius_m='13/50')),
      ('I17-02-radius-smaller','hole-radius-correspondence',lambda d:d['geometry']['model']['hole'].update(radius_m='6/25')),
      ('I17-03-center-shift','hole-center-correspondence',lambda d:d['geometry']['model']['hole'].update(center_xy_m=['11/100','-1/10'])),
      ('I17-04-axis-reverse','directed-hole-frame',lambda d:d['records']['model'].update(axis_local=['0','0','-1'])),
      ('I17-05-normal-reverse','face-inventory-or-orientation',lambda d:d['geometry']['model']['faces'].update(bore='away-from-axis')),
      ('I17-06-face-missing','face-inventory-or-orientation',lambda d:d['geometry']['model']['faces'].pop('ymin')),
      ('I17-07-solid-open','invalid-or-open-solid',lambda d:d['geometry']['model'].update(closed=False)),
      ('I17-08-placement-missing',"'placement'",lambda d:d['geometry']['model'].pop('placement')),
      ('I17-09-placement-double','placement-application-count',lambda d:d['records']['model'].update(placement_applications=2)),
      ('I17-10-unit-wrong','unit-conversion',lambda d:d['records']['model'].update(scale_to_m='1')),
      ('I17-11-round-down','unsafe-rounding',lambda d:d['geometry']['rounding'].update(reported_upper_m='285/1000')),
      ('I17-12-tolerance-excess','tolerance-exceeds-declared-budget',lambda d:d['records']['model'].update(brep_tolerance_m='1/1000')),
      ('I17-13-shape-wrong','shape-anchor-mismatch',lambda d:d['records']['model'].update(object_id='GATE_Bolt')),
      ('I17-14-manifest-absent',"'manifest_sha256'",lambda d:d.pop('manifest_sha256')),
      ('I17-15-evidence-absent','mandatory-evidence',lambda d:d['evidence'].pop('placement')),
      ('I17-16-count-bool','placement-application-count',lambda d:d['records']['model'].update(placement_applications=True)),
      ('I17-17-order-wrong','transform-order-or-frame',lambda d:d['records']['model'].update(transform_order=['translate','rotate','scale'])),
    ]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-dir',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    candidate=args.candidate_dir.resolve()
    if not candidate.is_dir(): raise ValueError('candidate directory missing')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    out=args.output_dir
    # Use a fresh process: refuse accidental reuse of a historical implementation.
    if 'boundary_contract' in sys.modules or 'circular_contract' in sys.modules:
        raise RuntimeError('implementation already imported; start a fresh process')
    sys.path.insert(0,str(candidate))
    import boundary_contract as impl
    import circular_contract as circle
    if Path(impl.__file__).resolve()!=candidate/'boundary_contract.py' or Path(circle.__file__).resolve()!=candidate/'circular_contract.py':
        raise RuntimeError('candidate import provenance mismatch')
    sources={name:digest(candidate/name) for name in PRESERVED_HASHES}
    source_matches={name:value==PRESERVED_HASHES[name] for name,value in sources.items()}
    failures=[]
    if not all(source_matches.values()): failures.append({'id':'source-preservation','actual':source_matches})

    def emit(handle,row):
        handle.write(json.dumps(row,separators=(',',':'))+'\n')

    normal_data,normal_anchors=normal()
    normal_result=impl.validate_observation(normal_data,normal_anchors)
    controls=[{'id':'I17-normal','input':normal_data,'anchors':normal_anchors,'expected_status':'PASS','actual':normal_result}]
    if normal_result['status']!='PASS': failures.append({'id':'I17-normal','actual':normal_result})
    for label,reason,mutate in mutations():
        data,anchors=normal();mutate(data)
        result=impl.validate_observation(data,anchors)
        expected={'status':'FAIL','reason':reason}
        controls.append({'id':label,'input':data,'anchors':anchors,'expected':expected,'actual':result})
        if result!=expected: failures.append({'id':label,'actual':result,'expected':expected})
    # Same prior tangent input plus a much smaller exact inward/outward offset.
    for label,x,expected in [('contact-tangent','3/5','FAIL'),
                             ('contact-clear-1e-12','599999999999/1000000000000','PASS'),
                             ('contact-intrude-1e-12','600000000001/1000000000000','FAIL')]:
        values=['1','0','0','0',x,'4/5','1/1000000000000']
        result=impl.void_rectangle(*values)
        controls.append({'id':label,'input':values,'expected_status':expected,'actual':result})
        if result['status']!=expected: failures.append({'id':label,'actual':result,'expected':expected})
    data,anchors=normal();data['schema']='brep-observation-v1'
    real_result=impl.validate_observation(data,anchors)
    controls.append({'id':'real-input-gate','input':data,'anchors':anchors,'expected_status':'UNKNOWN','actual':real_result})
    if real_result['status']!='UNKNOWN': failures.append({'id':'real-input-gate','actual':real_result})
    with (out/'controls.json').open('x',encoding='utf-8') as f:
        f.write(json.dumps(controls,indent=2)+'\n')

    rnd=random.Random(35052)
    with (out/'rounding-inputs.jsonl').open('x',encoding='utf-8') as f:
        for i in range(5000):
            value=F(rnd.randint(-100000,100000),rnd.randint(1,99))
            quantum=F(rnd.randint(1,99),rnd.randint(1,1000))
            quotient,remainder=divmod(value,quantum)
            expected={'lower':str(quotient*quantum),'upper':str((quotient+int(remainder!=0))*quantum)}
            actual={k:str(impl.round_grid(str(value),str(quantum),k)) for k in expected}
            row={'id':f'Q5000-{i:05d}','input':{'value':str(value),'quantum':str(quantum)},'expected':expected,'actual':actual}
            emit(f,row)
            if actual!=expected: failures.append(row)
    with (out/'rectangle-inputs.jsonl').open('x',encoding='utf-8') as f:
        for i in range(10000):
            radius=F(rnd.randint(1,2000),1000)
            ec,er,et=[F(rnd.randint(0,100),1000) for _ in range(3)]
            x,y=[F(rnd.randint(1,2000),1000) for _ in range(2)]
            quantum=F(1,1000);rho=radius-ec-er-et
            values=list(map(str,(radius,ec,er,et,x,y,quantum)))
            corners=[a*a+b*b for a in (-x,x) for b in (-y,y)]
            expected='UNKNOWN' if rho<=0 else ('PASS' if max(corners)<rho*rho else 'FAIL')
            actual=impl.void_rectangle(*values)
            row={'id':f'R10000-{i:05d}','input':values,'expected_status':expected,'actual':actual,
                 'reference_max_corner_squared':str(max(corners)),'reference_rho_squared':str(rho*rho)}
            emit(f,row)
            if actual['status']!=expected: failures.append(row)

    counts={'old_reference':impl.aggregate_intervals(['UNKNOWN']*128),
            'current_not_executed':impl.aggregate_intervals(['NOT_TESTED']*128)}
    if counts['old_reference']['UNKNOWN']!=128 or counts['current_not_executed']['NOT_TESTED']!=128:
        failures.append({'id':'interval-snapshot-separation'})
    for bad in [['PASS']*127,['PASS']*129,['BLOCKED']*128]:
        try: impl.aggregate_intervals(bad)
        except ValueError: pass
        else: failures.append({'id':'bad-interval-snapshot-accepted'})
    summary={'scope':'fresh post-transplant conditional arithmetic/observation-contract check; no real CAD proof',
             'status':'PASS' if not failures else 'FAIL','source_sha256':sources,'preserved_source_bytes_match':source_matches,
             'checker_sha256':digest(Path(__file__)),'seed':35052,
             'counts':{'independent_fault_inputs':17,'normal_inputs':1,'contact_inputs':3,'real_gate_inputs':1,
                       'rectangle_inputs':10000,'rounding_input_pairs':5000},
             'failures':failures,'interval_snapshots':counts,
             'shared_components':['implementation is called only as system under test',
                'reference and implementation both use Python Fraction','same explicit closed-material/open-void semantics',
                'candidate observation validation uses candidate circular.rigid; reviewer does not independently read actual transforms'],
             'independent_components':['reviewer fixture and mutations','four-corner reference equations','divmod grid-rounding reference'],
             'real_brep_inclusion':'UNKNOWN','actual_cad_execution':'NOT_TESTED',
             'command_template':'python -B cad/stage3d5b/independent_check.py --candidate-dir cad/stage3d5b --output-dir NEW_OUTPUT'}
    with (out/'summary.json').open('x',encoding='utf-8') as f:f.write(json.dumps(summary,indent=2)+'\n')
    entries=[{'path':p.name,'size_bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(out.iterdir()) if p.is_file()]
    with (out/'manifest.json').open('x',encoding='utf-8') as f:
        f.write(json.dumps({'scope':'new checker output payload; manifest excludes itself','files':entries},indent=2)+'\n')
    print('Independent post-transplant check:',summary['status'])
    print('Inputs: 17 faults, 1 normal, 3 contact, 1 real gate, 10000 rectangles, 5000 rounding pairs')
    print('Actual CAD: NOT_TESTED; real BRep inclusion: UNKNOWN')
    return 0 if not failures else 1


if __name__=='__main__': sys.exit(main())
