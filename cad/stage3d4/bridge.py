"""Fail-closed native premise assessment, NOT a BRep-to-polyhedron proof."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PARTS=['GATE_Bolt','GATE_BoltGuide_Left']
CONTRACT=ROOT/'cad/stage3d2/contract.json'
PIN='88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa'

def sources():
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=PIN:raise ValueError('D2_CONTRACT_CHANGED')
    expected=json.loads(CONTRACT.read_text())['sources']
    actual={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in expected}
    if actual!=expected:raise ValueError('ORIGINAL_SOURCE_CHANGED')
    return actual

def assess(data):
    reasons=[]
    if data.get('sources')!=sources():reasons.append('SOURCE_IDENTITY')
    if data.get('unit')!='mm' or data.get('frame')!='FreeCAD world':reasons.append('UNIT_FRAME')
    if type(data.get('door_degrees')) is not int or data['door_degrees']!=0 or data.get('travel_mm')!=[0,140] or any(type(v) is not int for v in data.get('travel_mm',[])):reasons.append('MOTION_SCOPE')
    parts=data.get('parts',{})
    if set(parts)!=set(PARTS):reasons.append('PART_SET')
    for name in PARTS:
        p=parts.get(name,{})
        if not p or not p.get('brep_sha256') or not p.get('placement'):
            reasons.append('MISSING_IDENTITY:'+name)
        if p.get('valid') is not True or p.get('closed') is not True or p.get('solids')!=1 or p.get('shells')!=1:
            reasons.append('INVALID_CLOSED_SOLID:'+name)
        faces=p.get('faces',[])
        if not faces:reasons.append('EMPTY_FACES:'+name)
        for f in faces:
            if f.get('surface')!='Plane':reasons.append('UNSUPPORTED_SURFACE:'+name)
            if f.get('orientation') not in ['Forward','Reversed']:reasons.append('AMBIGUOUS_ORIENTATION:'+name)
            wires=f.get('wires',[])
            if not wires:reasons.append('MISSING_TRIMS:'+name)
            for w in wires:
                if w.get('closed') is not True or not w.get('edges'):reasons.append('BROKEN_TRIM:'+name)
                for e in w.get('edges',[]):
                    if e.get('curve')!='Line':reasons.append('UNSUPPORTED_EDGE:'+name)
                    if e.get('orientation') not in ['Forward','Reversed'] or len(e.get('vertices',[]))!=2:reasons.append('INVALID_EDGE:'+name)
    # Eligibility is observation only. No user-provided proof flag or numeric epsilon is consumed.
    missing=['NO_CERTIFIED_TRIM_TO_EXACT_BOUNDARY_RELATION','NO_VALIDATED_BREP_GEOMETRIC_ERROR_ENCLOSURE',
             'NO_CERTIFIED_WORLD_PLACEMENT_ENCLOSURE','NO_CERTIFIED_CONTINUOUS_NATIVE_TRANSFORM']
    guarantees={k:{'status':'UNKNOWN','reason':missing} for k in ['brep_boundary_relation','material_outer_containment','hole_inner_containment','placement_error','numeric_error','continuous_motion','d2_application']}
    guarantees['input_identity']={'status':'PASS' if data.get('sources')==sources() else 'FAIL','scope':'raw source bytes only'}
    return {'schema':'native-boundary-assessment-v1','eligibility':'REJECTED' if reasons else 'OBSERVED_ONLY',
            'reasons':sorted(set(reasons)),'guarantees':guarantees,'cad_intervals':{'PASS':0,'FAIL':0,'UNKNOWN':128},
            'physical_safety':'NOT_TESTED','generation_spec_guarantee':'NOT_ESTABLISHED'}
