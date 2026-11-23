"""Guide one-holed planar end face: an exact represented-domain theorem.

A PASS is about the exact rational Plane and saved pcurve *representations*.
This cannot prove the OCCT runtime real surface, tolerance neighborhoods,
complete Solid occupancy or all-state motion; those remain UNKNOWN.
"""
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import sys
import zipfile

FCSTD_SHA = 'c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a'
D2_SHA = '88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa'
GUIDE_BREP_SHA = '043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261'
TRIM_SHA = '412e4488136ecb28a59a616c4d33d010ffaf75ff4e3ab962bfcf138920f9afe3'
GUIDE = 'GATE_BoltGuide_Left'


def q(v):
    if type(v) not in (str, int, F):
        raise ValueError('NON_EXACT_RATIONAL_INPUT')
    return F(v)


def vec(v, size):
    if not isinstance(v, (list, tuple)) or len(v) != size:
        raise ValueError('VECTOR_LENGTH')
    return tuple(q(x) for x in v)


def plus(a, b):
    return tuple(x + y for x, y in zip(a, b, strict=True))


def scaled(c, v):
    return tuple(c * x for x in v)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def rectangle(loop):
    """Full exact loop equality to a nondegenerate axis-aligned rectangle."""
    p = [vec(x, 2) for x in loop]
    if len(p) != 4 or len(set(p)) != 4:
        raise ValueError('RECTANGLE_NEEDS_FOUR_DISTINCT_CORNERS')
    low = (min(x[0] for x in p), min(x[1] for x in p))
    high = (max(x[0] for x in p), max(x[1] for x in p))
    if not (low[0] < high[0] and low[1] < high[1]):
        raise ValueError('DEGENERATE_RECTANGLE')
    expected = set(product((low[0], high[0]), (low[1], high[1])))
    if set(p) != expected:
        raise ValueError('NOT_RECTANGLE_CORNERS')
    for a, b in zip(p, p[1:] + p[:1]):
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise ValueError('NOT_AXIS_ALIGNED_RECTANGLE_EDGE')
    area2 = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))
    area = (high[0]-low[0])*(high[1]-low[1])
    if abs(area2) != 2*area:
        raise ValueError('WRONG_WINDING_OR_SELF_OVERLAP')
    return {'low': low, 'high': high, 'area': area, 'signed_area2': area2}


def strict_nested(outer, hole):
    return all(outer['low'][i] < hole['low'][i] < hole['high'][i] < outer['high'][i]
               for i in range(2))


def plane_mapping(face):
    p = face['plane']
    if not isinstance(p, list) or len(p) != 3:
        raise ValueError('PLANE_FRAME_MISSING')
    origin, u, v = (vec(x, 3) for x in p)
    normal = cross(u, v)
    if not any(normal):
        raise ValueError('DEGENERATE_PLANE')
    if (sorted([sum(x!=0 for x in axis) for axis in (u,v,normal)]) != [1,1,1] or
            any(sum(x*x for x in axis) != 1 for axis in (u,v,normal))):
        raise ValueError('ONLY_EXACT_ORTHONORMAL_AXIS_FRAMES_SUPPORTED')
    expected_orient = normal if face['orientation']=='Forward' else tuple(-x for x in normal)
    if face['orientation'] not in ('Forward','Reversed') or vec(face['normal'],3) != expected_orient:
        raise ValueError('FACE_NORMAL_ORIENTATION_MISMATCH')
    return (origin,u,v)


def surface_point(plane, uv):
    o,u,v=plane
    return plus(o,plus(scaled(uv[0],u),scaled(uv[1],v)))


def verify_uses(face, stored):
    """Recheck all 8 existing same-process stored-pcurve join witnesses."""
    if not isinstance(stored, list) or len(stored) != 8:
        raise ValueError('NOT_EXACTLY_EIGHT_STORED_PCURVE_USES')
    witness = {}
    for s in stored:
        if s.get('status') != 'PASS':
            raise ValueError('STORED_PCURVE_WITNESS_NOT_PASS')
        key=(s.get('face'),s.get('wire'),s.get('edge'),s.get('formula_use_order'))
        if key in witness:
            raise ValueError('DUPLICATE_STORED_WITNESS')
        witness[key]=s
    if len(face.get('wires', [])) != 2:
        raise ValueError('EXPECTED_OUTER_AND_INNER_WIRE')
    plane=plane_mapping(face)
    roles=[];rects=[];keys=[]
    for w in face['wires']:
        if w['role'] not in ('outer','inner') or len(w.get('uses', []))!=4:
            raise ValueError('WRONG_WIRE_ROLE_OR_EDGE_COUNT')
        roles.append(w['role'])
        segs=[]
        for use in w['uses']:
            key=(face['face'],w['wire'],use['edge'],use['use'])
            if key not in witness:
                raise ValueError('MISSING_STORED_PCURVE_FOR_FACE_USE')
            keys.append(key)
            if use.get('represented_affine_link')!='PASS' or use['curve_type']!='Line' or use['pcurve_type'] not in ('Line2d','Line2dSegment'):
                raise ValueError('UNPROVEN_NATIVE_REPRESENTED_LINE')
            p0,p1=(vec(x,2) for x in use['pcurve'])
            c0,c1=(vec(x,3) for x in use['curve'])
            a,b=vec(use['pcurve_range'],2)
            if a>=b or (a,b)!=vec(use['curve_range'],2):
                raise ValueError('MISMATCHED_PARAMETER_RANGE')
            if surface_point(plane,p0)!=c0 or plus(scaled(p1[0],plane[1]),scaled(p1[1],plane[2]))!=c1:
                raise ValueError('NONIDENTICAL_REPRESENTED_CURVE_SURFACE')
            endpoints=[plus(p0,scaled(t,p1)) for t in (a,b)]
            if use['orientation']=='Reversed':
                endpoints.reverse()
            elif use['orientation']!='Forward':
                raise ValueError('UNKNOWN_EDGE_ORIENTATION')
            if endpoints!=[vec(x,2) for x in use['directed_uv']]:
                raise ValueError('DIRECTED_PCURVE_ENDPOINT_MISMATCH')
            if [surface_point(plane,uv) for uv in endpoints] != [vec(x,3) for x in use['directed_3d']]:
                raise ValueError('DIRECTED_PCURVE_3D_ENDPOINT_MISMATCH')
            segs.append(tuple(endpoints))
        if any(segs[i][1]!=segs[(i+1)%4][0] for i in range(4)):
            raise ValueError('NON_CLOSED_OR_UNORDERED_PCURVE_WIRE')
        polygon=[a for a,b in segs]
        if polygon!=[vec(x,2) for x in w['directed_loop']]:
            raise ValueError('WIRE_VERTEX_ORDER_DISAGREES')
        r=rectangle(polygon)
        if r['signed_area2'] != q(w['signed_area2_mm2']):
            raise ValueError('WIRE_AREA_MISMATCH')
        wanted=(1 if face['orientation']=='Forward' else -1)*(1 if w['role']=='outer' else -1)
        if (r['signed_area2']>0)!=(wanted>0):
            raise ValueError('WIRE_WINDING_MISMATCH')
        rects.append(r)
    if roles != ['outer','inner'] or len(set(keys))!=8 or len(set(witness))!=8:
        raise ValueError('NOT_ONE_OUTER_AND_ONE_INNER')
    outer,inner=rects
    if not strict_nested(outer,inner):
        raise ValueError('INNER_NOT_STRICTLY_INSIDE_OUTER')
    uv_bounds=vec(face['uv_bounds'],4)
    if uv_bounds!=(outer['low'][0],outer['high'][0],outer['low'][1],outer['high'][1]):
        raise ValueError('UV_BOUNDS_NOT_OUTER_RECTANGLE')
    if face.get('status')!='PASS' or face.get('represented_trim_polygon')!='PASS' or face.get('represented_material_side',{}).get('status')!='PASS':
        raise ValueError('PRIOR_FACE_TRIM_MATERIAL_GATE_NOT_PASS')
    return plane, outer, inner


def exact_face_membership(outer, inner, uv):
    """Rational full-domain predicate including both wire boundaries."""
    return (all(outer['low'][i]<=uv[i]<=outer['high'][i] for i in range(2))
            and not all(inner['low'][i]<uv[i]<inner['high'][i] for i in range(2)))


def model_end_cross_section(contract):
    boxes=[vec(b,6) for b in contract['obstacle_boxes']]
    if len(boxes)!=4 or any(b[i]>=b[i+3] for b in boxes for i in range(3)):
        raise ValueError('WRONG_D2_BOX_INVENTORY')
    x0=min(b[0] for b in boxes);x1=max(b[3] for b in boxes)
    if x0>=x1 or any(b[0]!=x0 or b[3]!=x1 for b in boxes):
        raise ValueError('D2_GUIDE_NOT_COMMON_X_EXTRUSION')
    return boxes,x0


def compare_closed_face_domain(face, plane, outer, hole, boxes, x0):
    """Exact equality of regular-closed 2D sets on a complete atomic grid.

    Domain is closed outer UV rectangle minus OPEN inner UV rectangle.
    Every full-dimensional atomic open cell has constant membership. Both
    sets are regular closed, so open-cell equivalence implies equality of
    their full closures including each inner/outer wire edge and vertex.
    This is symbolic partition, NOT spatial point sampling of OCCT geometry.
    """
    if plane[1][0] or plane[2][0] or plane[0][0]!=x0:
        raise ValueError('END_FACE_NOT_GUIDE_NEGATIVE_X_PLANE')
    def yz_rect(r):
        corners=list(product((r['low'][0],r['high'][0]),(r['low'][1],r['high'][1])))
        world=[surface_point(plane,uv) for uv in corners]
        return (min(p[1] for p in world),max(p[1] for p in world),
                min(p[2] for p in world),max(p[2] for p in world))
    outer_world=yz_rect(outer);hole_world=yz_rect(hole)
    grid_y=sorted({outer_world[0],outer_world[1],hole_world[0],hole_world[1],
                   *(b[i] for b in boxes for i in (1,4))})
    grid_z=sorted({outer_world[2],outer_world[3],hole_world[2],hole_world[3],
                   *(b[i] for b in boxes for i in (2,5))})
    if (len(grid_y)-1)*(len(grid_z)-1)>256:
        raise ValueError('ATOMIC_GRID_TOO_LARGE')
    checked=0
    for ylo,yhi in zip(grid_y,grid_y[1:]):
        for zlo,zhi in zip(grid_z,grid_z[1:]):
            # The open atomic rectangle is wholly inside/outside every exact
            # line-defined rectangle. Its midpoint is merely a symbolic label.
            y=(ylo+yhi)/2;z=(zlo+zhi)/2
            in_face=(outer_world[0]<y<outer_world[1] and outer_world[2]<z<outer_world[3]
                     and not (hole_world[0]<y<hole_world[1] and hole_world[2]<z<hole_world[3]))
            in_d2=any(b[1]<y<b[4] and b[2]<z<b[5] for b in boxes)
            checked+=1
            if in_face!=in_d2:
                raise ValueError('MODEL_AND_FACE_OPEN_ATOMIC_CELL_DIFFER')
    # Both are regular-closed finite orthogonal domains. The outer-closed
    # minus inner-open rectangular ring has nonzero side thickness.
    if not strict_nested(outer,hole) or checked==0:
        raise ValueError('NOT_A_REGULAR_CLOSED_RING')
    return {'status':'PASS','theorem':'exact regular-closed orthogonal domains: equality of all open atomic cells implies equality of their closures',
            'tested_symbolic_atomic_cells':checked,
            'world_outer_yz_mm':[str(x) for x in outer_world],
            'world_inner_yz_mm':[str(x) for x in hole_world]}


def select_target(guide, stored):
    if guide.get('status')!='PASS' or guide.get('edge_use_count')!=48 or len(guide.get('faces',[]))!=10:
        raise ValueError('UNEXPECTED_GUIDE_TRIM_CENSUS')
    if not isinstance(stored,list) or len(stored)!=48 or any(r.get('status')!='PASS' for r in stored):
        raise ValueError('UNEXPECTED_STORED_GUIDE_CENSUS')
    candidates=[f for f in guide['faces'] if len(f['wires'])==2]
    if len(candidates)!=2:
        raise ValueError('EXPECTED_TWO_END_FACES_WITH_INNER_WIRES')
    selected=min(candidates,key=lambda f:q(f['plane'][0][0]))
    if selected['face']!=0 or selected['orientation']!='Reversed':
        raise ValueError('TARGET_FACE_IDENTITY_CHANGED')
    return selected,[r for r in stored if r['face']==selected['face']]


def proof(trim, stored, contract):
    """Caller-independent certificate for one fixed Guide face only."""
    if (trim.get('source_fcstd_sha256')!=FCSTD_SHA or trim.get('source_d2_sha256')!=D2_SHA or
            stored.get('formula_sha256')!=TRIM_SHA or not stored.get('expansion_permitted')):
        raise ValueError('SOURCE_OR_STORED_PCURVE_PROVENANCE_CHANGED')
    guide=trim['parts'][GUIDE]
    face,uses=select_target(guide,stored['parts'][GUIDE])
    plane,outer,inner=verify_uses(face,uses)
    boxes,x0=model_end_cross_section(contract)
    comparison=compare_closed_face_domain(face,plane,outer,inner,boxes,x0)
    return {
      'status':'PASS',
      'scope':'one fixed face exact represented analytic domain, conditional on OCCT Face trim semantics',
      'target':{'part':GUIDE,'face':face['face'],'face_orientation':face['orientation'],
                'wire_roles':['outer','inner'],'saved_pcurve_uses':len(uses)},
      'plane_mm':[[str(v) for v in axis] for axis in plane],
      'outer_uv_mm':{'low':[str(v) for v in outer['low']],'high':[str(v) for v in outer['high']]},
      'inner_uv_mm':{'low':[str(v) for v in inner['low']],'high':[str(v) for v in inner['high']]},
      'represented_ring_area_mm2':str(outer['area']-inner['area']),
      'continuous_domain_rule':'outer closed rectangle MINUS inner open rectangle; both wire boundaries included',
      'D2_end_face':comparison,
      'represented_face_region_equivalence':'PASS',
      'native_geometric_face_semantics':'UNKNOWN',
      'native_entire_solid_material':'UNKNOWN',
      'native_void_subset':'UNKNOWN',
      'finite_native_real_error':'UNKNOWN',
      'all_states':'UNKNOWN',
      'native_representative_interval':'NOT_TESTED',
      'remaining_obligations':['OCCT native Face trimmed-domain semantics vs rational defined polynomial surface',
                               'native tolerance/rounding to continuum geometry enclosures',
                               'all other faces, complete native Solid boundary and oriented interior'],
    }


def execute(trim_path,stored_path,out,root):
    out.mkdir(parents=True,exist_ok=False)
    input_bytes=(root/'cad/stage3c/generated/assembly.FCStd').read_bytes()
    d2_bytes=(root/'cad/stage3d2/contract.json').read_bytes()
    trim_bytes=trim_path.read_bytes();stored_bytes=stored_path.read_bytes()
    if (sha256(input_bytes).hexdigest()!=FCSTD_SHA or sha256(d2_bytes).hexdigest()!=D2_SHA or
        sha256(trim_bytes).hexdigest()!=TRIM_SHA):
        raise ValueError('FIXED_SOURCE_OR_UNCHANGED_72_FORMULAS_SHA_MISMATCH')
    with zipfile.ZipFile(root/'cad/stage3c/generated/assembly.FCStd') as z:
        if sha256(z.read(GUIDE+'.Shape.brp')).hexdigest()!=GUIDE_BREP_SHA:
            raise ValueError('GUIDE_FIXED_BREP_CHANGED')
    try:
        result=proof(json.loads(trim_bytes),json.loads(stored_bytes),json.loads(d2_bytes))
    except Exception as exc:
        result={'status':'FAIL','reason':str(exc),'native_geometric_face_semantics':'UNKNOWN',
                'native_entire_solid_material':'UNKNOWN','native_void_subset':'UNKNOWN',
                'native_representative_interval':'NOT_TESTED'}
    result.update({'schema':'d5d-single-holed-face-region-v1',
                   'input_sha256':{'fcstd':FCSTD_SHA,'d2':D2_SHA,'guide_brep':GUIDE_BREP_SHA,
                                   'trim':TRIM_SHA,'stored_pcurve_report':sha256(stored_bytes).hexdigest()}})
    (out/'face-region.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    if len(sys.argv)!=5:
        raise SystemExit('usage: face_region.py TRIM_JSON STORED_JSON OUTPUT_DIR REPO_ROOT')
    sys.exit(execute(*(Path(x) for x in sys.argv[1:])))
