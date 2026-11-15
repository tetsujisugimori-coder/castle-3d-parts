"""Actual FreeCAD read-only extraction and bounded isolated native mutations."""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib'])
import FreeCAD as A
import Part
from correspondence import SOURCES, PARTS, evaluate, fingerprint
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'cad/stage3c'))
from state import load_document, transition


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def describe(shape):
    brep = shape.exportBrepToString().encode()
    return {'brep_sha256': hashlib.sha256(brep).hexdigest(), 'brep_bytes': len(brep),
            'valid': shape.isValid(), 'closed': shape.isClosed(), 'solids': len(shape.Solids),
            'faces': len(shape.Faces), 'edges': len(shape.Edges), 'vertices': len(shape.Vertexes),
            'bounds_mm_observed': [getattr(shape.BoundBox, k) for k in ('XMin','YMin','ZMin','XMax','YMax','ZMax')],
            'volume_mm3_observed': shape.Volume,
            'placement_observed': str(shape.Placement),
            'face_types': [type(f.Surface).__name__ for f in shape.Faces],
            'face_wires': [len(f.Wires) for f in shape.Faces],
            'edge_types': [type(e.Curve).__name__ for e in shape.Edges],
            'vertex_points_mm_observed': [[v.Point.x,v.Point.y,v.Point.z] for v in shape.Vertexes],
            'tolerance_max_mm_observed': shape.getTolerance(1),
            'tolerance_min_mm_observed': shape.getTolerance(-1)}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    sources = {p: sha(ROOT / p) for p in SOURCES}
    if sources != SOURCES:
        raise ValueError('PINNED_SOURCE_MISMATCH')
    doc = load_document(ROOT / 'cad/stage3c/generated/assembly.FCStd')
    for obj in doc.Objects:
        if 'KeepUpdated' in obj.PropertiesList:
            obj.KeepUpdated = False
    ids = sorted(o.PartID for o in doc.Objects if 'PartID' in o.PropertiesList)
    if len(ids) != 23:
        raise ValueError('PART_COUNT')
    poses = []
    for mm in (0, 70, 140):
        transition(doc, 0, mm / 1000)
        poses.append({'travel_mm':mm, 'parts':{p:describe(doc.getObject(p).Shape) for p in PARTS},
                      'distance_mm_observed':doc.getObject(PARTS[0]).Shape.distToShape(doc.getObject(PARTS[1]).Shape)[0]})
    transition(doc, 0, 0)
    original = {p: doc.getObject(p).Shape.copy() for p in PARTS}
    reference = {'sources':sources, 'unit':'mm', 'coordinate_frame':'FreeCAD world; project m -> native mm x1000',
                 'door_degrees':0, 'travel_mm':[0,140], 'parts':{p:describe(s) for p,s in original.items()}}
    rows = [{'case':'original', 'kind':'real FreeCAD original observation', 'input':reference, 'result':evaluate(reference, reference)}]
    # All mutations are isolated shape copies. The loaded document is never saved.
    enlarged = Part.makeBox(900, 22, 40, A.Vector(-400,-116,1000))
    wall = Part.makeBox(20, 2, 42, A.Vector(-200,-116,999))
    shifted = original[PARTS[0]].copy(); shifted.translate(A.Vector(0,1,0))
    contact = original[PARTS[0]].copy(); contact.translate(A.Vector(0,0,1))
    near = original[PARTS[0]].copy(); near.translate(A.Vector(0,0,0.00000005))
    cases = [('bolt_enlarged',PARTS[0],enlarged), ('hole_shrunk',PARTS[1],original[PARTS[1]].fuse(wall)),
             ('placement_shift',PARTS[0],shifted), ('nominal_contact',PARTS[0],contact), ('near_tolerance_shift',PARTS[0],near)]
    for name,p,shape in cases:
        mutated = json.loads(json.dumps(reference)); mutated['parts'][p] = describe(shape)
        result = evaluate(mutated, reference)
        if result['status'] != 'REJECTED' or not any('SHAPE_OR_PLACEMENT_CHANGED' in r for r in result['reasons']):
            raise AssertionError(name)
        (out / (name+'.brep')).write_text(shape.exportBrepToString())
        rows.append({'case':name, 'kind':'isolated real FreeCAD shape mutation, not physical fault', 'input':mutated, 'result':result})
    topology = {}
    for name in PARTS + ['GATE_BoltGuide_LeftStock','GATE_BoltGuide_LeftBore']:
        obj = doc.getObject(name)
        topology[name] = {'type_id':obj.TypeId, 'placement':str(obj.Placement),
                          'expressions':[(x,str(y)) for x,y in obj.ExpressionEngine],
                          'dependencies':[o.Name for o in obj.OutList], 'shape':describe(obj.Shape)}
        (out / (name+'.brep')).write_text(obj.Shape.exportBrepToString())
    A.closeDocument(doc.Name)
    after = {p:sha(ROOT/p) for p in SOURCES}
    if after != sources:
        raise AssertionError('ORIGINAL_CHANGED')
    data = {'FreeCAD':A.Version(), 'occ_version':getattr(Part,'OCC_VERSION','UNKNOWN'), 'source_hashes_before':sources,
            'source_hashes_after':after, 'part_ids':ids, 'reference':reference, 'reference_sha256':fingerprint(reference),
            'topology':topology, 'poses':poses, 'cases':rows,
            'containment':'UNKNOWN', 'hole_void_lower_bound':'UNKNOWN', 'd2_real_CAD':'128 UNKNOWN',
            'reason':'BRep arithmetic/Boolean and topology tolerances lack certified outward error and void inclusion; no theorem checker implemented'}
    (out/'native.json').write_text(json.dumps(data,indent=2,allow_nan=False))
    print('Completed real FreeCAD extraction + 5 isolated native mutations; actual correspondence UNKNOWN',flush=True)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
    os._exit(0)
