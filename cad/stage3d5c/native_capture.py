"""D5C read-only complete native inventory and represented affine checks.

No numeric result here encloses the real BRep. Exact fractions compare stored
IEEE coefficients only. No repair, save, winding normalization or mutation is
performed. Missing API flags and native-to-real obligations stay UNKNOWN.
"""
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'cad/stage3d5b'))
import native
import planar_native


def q(x):
    if isinstance(x, bool):
        raise ValueError('BOOLEAN_GEOMETRY')
    return str(F(x))


def vec(v):
    return [q(v.x), q(v.y), q(v.z)] if hasattr(v, 'z') else [q(v.x), q(v.y)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def identity(obj, kind, source_hash):
    return {'descriptor_sha256': sha(canonical(obj)), 'kind': kind,
            'source_brep_sha256': source_hash,
            'identity_scope': 'fixed BRep bytes plus complete descriptor/incidence; local lookup numbers are not persistent identities'}


def matrix(placement):
    return [q(x) for x in placement.toMatrix().A]


def affine_pcurve(curve, first, last):
    name = type(curve).__name__
    result = {'type': name, 'use_parameter_range_ieee': [q(first), q(last)],
              'storage_origin': 'UNKNOWN',
              'storage_origin_reason': 'FreeCAD Face.curveOnSurface omits OCCT isStored; a Plane pcurve may be generated on request',
              'saved_trim_proven': False}
    if name == 'Line2d':
        result.update(origin_uv_ieee=vec(curve.Location), direction_uv_ieee=vec(curve.Direction),
                      coefficient_origin='native Line2d Location/Direction API')
    elif name == 'Line2dSegment':
        a, b = F(curve.FirstParameter), F(curve.LastParameter)
        start, end = [list(map(F, vec(v))) for v in (curve.StartPoint, curve.EndPoint)]
        if a == b:
            raise ValueError('ZERO_PCURVE_PARAMETER_SPAN')
        d = [(end[i] - start[i]) / (b - a) for i in range(2)]
        result.update(origin_uv_ieee=[str(start[i] - a*d[i]) for i in range(2)],
                      direction_uv_ieee=list(map(str,d)),
                      native_segment_parameter_range_ieee=[str(a), str(b)],
                      native_start_uv_ieee=list(map(str,start)), native_end_uv_ieee=list(map(str,end)),
                      coefficient_origin='exact rational secant of returned Line2dSegment endpoints and parameter limits; native-real interpolation theorem NOT_PROVEN')
    else:
        result.update(coefficient_origin='UNSUPPORTED', status='UNKNOWN')
    return result


def represented_link(surface, curve3d, pc):
    """Universal affine equality in the *represented* rational model, not samples."""
    if type(surface).__name__ != 'Plane' or type(curve3d).__name__ != 'Line' or 'origin_uv_ieee' not in pc:
        return {'status':'UNKNOWN','reason':'UNSUPPORTED_REPRESENTED_AFFINE_FORM'}
    pos = list(map(F, vec(surface.Position)))
    # Plane tangent frame returned by the API. Its native-real semantics remain
    # an obligation; it is not inferred from a bbox, vertex samples, or normal.
    u, v = [list(map(F, vec(x))) for x in surface.tangent(0, 0)]
    po, pd = list(map(F, pc['origin_uv_ieee'])), list(map(F, pc['direction_uv_ieee']))
    mapped_o = [pos[i]+u[i]*po[0]+v[i]*po[1] for i in range(3)]
    mapped_d = [u[i]*pd[0]+v[i]*pd[1] for i in range(3)]
    co, cd = list(map(F, vec(curve3d.Location))), list(map(F, vec(curve3d.Direction)))
    delta_o, delta_d = [mapped_o[i]-co[i] for i in range(3)], [mapped_d[i]-cd[i] for i in range(3)]
    return {'status':'PASS' if all(x == 0 for x in delta_o+delta_d) else 'FAIL',
            'scope':'exact equality of represented affine coefficient model for all real t, NOT real BRep consistency or an error bound',
            'surface_u_ieee':list(map(str,u)), 'surface_v_ieee':list(map(str,v)),
            'mapped_origin_ieee':list(map(str,mapped_o)), 'mapped_direction_ieee':list(map(str,mapped_d)),
            'origin_difference_ieee':list(map(str,delta_o)), 'direction_difference_ieee':list(map(str,delta_d)),
            'native_relation':'UNKNOWN'}


def flag(obj, name):
    try:
        value = getattr(obj, name)
        if callable(value): value = value()
        if type(value) is not bool: raise TypeError('API did not return bool')
        return {'availability':'OBSERVED', 'value':value, 'proof':'UNKNOWN'}
    except (AttributeError, TypeError) as e:
        return {'availability':'UNAVAILABLE','value':None,'proof':'UNKNOWN','reason':str(e)}


def extract(shape, source_hash):
    t = planar_native.topology(shape)
    vertices, edges, wires, faces, shells, solids = shape.Vertexes, shape.Edges, shape.Wires, shape.Faces, shape.Shells, shape.Solids
    same = planar_native.index_same
    for index, (row, obj) in enumerate(zip(t['vertices'], vertices)):
        row['placement_ieee'] = matrix(obj.Placement)
        row['identity'] = identity(row, 'Vertex', source_hash)
    for index, (row, obj) in enumerate(zip(t['edges'], edges)):
        row['placement_ieee'] = matrix(obj.Placement)
        row['curve3d'] = {'type':type(obj.Curve).__name__, 'parameter_range_ieee':[q(obj.FirstParameter),q(obj.LastParameter)]}
        if type(obj.Curve).__name__ == 'Line':
            row['curve3d'].update(origin_mm_ieee=vec(obj.Curve.Location), direction_ieee=vec(obj.Curve.Direction))
        row['SameParameter'] = flag(obj, 'SameParameter')
        row['SameRange'] = flag(obj, 'SameRange')
        row['identity'] = identity(row, 'Edge', source_hash)
    for row, obj in zip(t['wires'],wires):
        row['placement_ieee'] = matrix(obj.Placement)
        row['identity'] = identity(row, 'Wire', source_hash)
    for fi, (row, face) in enumerate(zip(t['faces'], faces)):
        row['placement_ieee'] = matrix(face.Placement)
        if type(face.Surface).__name__ == 'Plane':
            row['surface_frame_ieee'] = {'origin_mm':vec(face.Surface.Position),
                'u':vec(face.Surface.tangent(0,0)[0]),'v':vec(face.Surface.tangent(0,0)[1]),
                'axis':vec(face.Surface.Axis), 'scope':'returned Plane frame coefficients, not real enclosure'}
        uses = []
        for wi, wire in enumerate(face.Wires):
            for order, edge in enumerate(wire.OrderedEdges):
                ei = same(edge,edges)
                use = {'wire_id':same(wire,wires),'edge_id':ei,'order':order,
                       'edge_use_orientation':edge.Orientation,'wire_use_orientation':wire.Orientation,
                       'edge_descriptor_sha256':t['edges'][ei]['identity']['descriptor_sha256']}
                pc = face.curveOnSurface(edge)
                if pc is None:
                    use.update(pcurve=None, relation={'status':'UNKNOWN','reason':'MISSING_NATIVE_PCURVE'})
                else:
                    curve, first, last = pc
                    desc = affine_pcurve(curve,first,last)
                    use.update(pcurve=desc, relation=represented_link(face.Surface,edge.Curve,desc),
                               represented_range_equal=[q(first),q(last)] == [q(edge.FirstParameter),q(edge.LastParameter)],
                               pcurve_uv_endpoints_observed=[vec(curve.value(first)),vec(curve.value(last))])
                uses.append(use)
        row['pcurve_uses'] = uses
        row['identity'] = identity(row,'Face',source_hash)
    t['shells'] = [{'orientation':s.Orientation,'closed_observed':s.isClosed(),
                    'face_ids':[same(f,faces) for f in s.Faces],
                    'face_use_orientations':[f.Orientation for f in s.Faces],
                    'placement_ieee':matrix(s.Placement)} for s in shells]
    t['solids'] = [{'orientation':s.Orientation,'closed_observed':s.isClosed(),
                    'shell_ids':[same(sh,shells) for sh in s.Shells],
                    'shell_use_orientations':[sh.Orientation for sh in s.Shells],
                    'face_ids':[same(f,faces) for f in s.Faces],
                    'face_use_orientations':[f.Orientation for f in s.Faces],
                    'placement_ieee':matrix(s.Placement)} for s in solids]
    for key in ('shells','solids'):
        for row in t[key]:row['identity']=identity(row,key[:-1],source_hash)
    # Check entire imported inventories against every use. Counts are recomputed,
    # not trusted from a boolean or caller-provided certificate.
    edge_uses=Counter(u['edge_id'] for f in t['faces'] for u in f['pcurve_uses'])
    wire_uses=Counter(i for f in t['faces'] for i in f['wire_ids'])
    vertex_uses={v for e in t['edges'] for v in e['vertex_ids']}
    shell_faces={f for s in t['shells'] for f in s['face_ids']}
    solid_shells={s for so in t['solids'] for s in so['shell_ids']}
    coverage={
        'vertices':vertex_uses==set(range(len(vertices))),
        'edges':set(edge_uses)==set(range(len(edges))) and all(n==2 for n in edge_uses.values()),
        'wires':set(wire_uses)==set(range(len(wires))) and all(n==1 for n in wire_uses.values()),
        'faces':shell_faces==set(range(len(faces))),
        'shells':solid_shells==set(range(len(shells))),
        'one_solid':len(solids)==1}
    t['inventory_coverage']={'status':'PASS' if all(coverage.values()) else 'FAIL','checks':coverage,
        'scope':'complete inventories exposed by this import/API; not proof of source parser completeness or material set equivalence'}
    t['shape_placement_ieee']=matrix(shape.Placement)
    t['shape_orientation']=shape.Orientation
    t['native_valid_observed']=shape.isValid()
    t['native_closed_observed']=shape.isClosed()
    t['native_material_side']='UNKNOWN'
    t['full_trim_to_native_real']='UNKNOWN'
    return t


def main(out):
    out.mkdir(parents=True,exist_ok=False)
    sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/lib/freecad/lib'])
    import FreeCAD as A
    import Part
    if A.Version()[:3] != ['1','0','0'] or Part.OCC_VERSION != '7.8.1':
        raise ValueError('FIXED_RUNTIME_MISMATCH')
    original=native.FCSTD.read_bytes()
    if sha(original)!=native.FCSTD_PIN:raise ValueError('FIXED_FCSTD_MISMATCH')
    isolated=out/'isolated';isolated.mkdir()
    copy_path=isolated/'assembly.FCStd';copy_path.write_bytes(original)
    records={}
    with zipfile.ZipFile(copy_path) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('FCSTD_CRC_OR_DUPLICATE')
        xml=ET.fromstring(archive.read('Document.xml'))
        for name in native.PARTS:
            metadata=native.xml_object(xml,name)
            if metadata['shape_ref'] != name+'.Shape.brp':raise ValueError('FIXED_OBJECT_MEMBER_MISMATCH')
            raw=archive.read(metadata['shape_ref']);(out/(name+'.original.brp')).write_bytes(raw)
            shape=Part.Shape();shape.importBrepFromString(raw.decode('utf-8'))
            before=shape.exportBrepToString().encode()
            topology=extract(shape,sha(raw))
            if before!=shape.exportBrepToString().encode():raise ValueError('EXTRACTION_MUTATED_SHAPE')
            uses=[u for f in topology['faces'] for u in f['pcurve_uses']]
            records[name]={'source_brep_sha256':sha(raw),'source_bytes':len(raw),'xml':metadata,'topology':topology,
                'pcurve_use_count':len(uses),
                'represented_affine_relation_counts':dict(Counter(u['relation']['status'] for u in uses)),
                'represented_range_equal_count':sum(u.get('represented_range_equal',False) for u in uses),
                'native_relation':'UNKNOWN','material_outer_inclusion':'UNKNOWN','void_inner_inclusion':'UNKNOWN'}
    if copy_path.read_bytes()!=original or native.FCSTD.read_bytes()!=original:raise ValueError('FCSTD_CHANGED')
    result={'schema':'stage3d5c-native-capture-v1','FreeCAD':A.Version(),'OCCT':Part.OCC_VERSION,
        'input':{'path':str(native.FCSTD.relative_to(ROOT)),'sha256':sha(original),'size_bytes':len(original)},
        'records':records,'original_and_isolated_fcstd_byte_equal_after':True,
        'original_document_opened':False,'document_saved':False,'repair_performed':False,
        'finite_native_error_bounds':None,'native_continuous_safety':'NOT_TESTED',
        'limitations':['SameParameter/SameRange not exposed by this FreeCAD Python Edge API; no assumed true',
          'pcurve stored/generated origin UNKNOWN; Face.curveOnSurface omits OCCT isStored flag',
          'pcurve represented affine equality does not certify native-real extraction or topology/material semantics',
          'Line2dSegment coefficient recovery uses represented endpoint/parameter data, not a real-valued enclosure',
          'Face/Wire orientations and OuterWire are observations, never normalized into native material proof']}
    (out/'native-capture.json').write_bytes(json.dumps(result,indent=2,allow_nan=False).encode()+b'\n')
    print(json.dumps({name:{'coverage':r['topology']['inventory_coverage'],'pcurves':r['pcurve_use_count'],
          'affine':r['represented_affine_relation_counts'],'ranges':r['represented_range_equal_count']} for name,r in records.items()}),flush=True)


if __name__=='__main__':
    out=Path(sys.argv[1]);created=not out.exists()
    try:main(out)
    except BaseException:
        error=traceback.format_exc()
        if created and out.is_dir() and not (out/'error.txt').exists():(out/'error.txt').write_text(error)
        os.write(2,error.encode());os._exit(1)
    os._exit(0)
