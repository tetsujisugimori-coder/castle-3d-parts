"""Guide through-void Q: exact 10-Face modeled boundary and bounded OCCT observations.

Q derives from the *existing* D2 moving cross section, not a new design.
PASS is rational displayed-BRep boundary disjointness plus bounded numerical
OCCT observations. It is NOT an interval-certified native Solid occupancy proof.
"""
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from face_region import (FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE,
                         vec, plane_mapping, surface_point, rectangle, strict_nested)
from one_slice import FCSTD, CONTRACT
from guide_q_native_helpers import check_native


def h(b):
    return sha256(b).hexdigest()


def exact_q(contract):
    if (contract.get('parts') != ['GATE_Bolt', GUIDE] or
            contract.get('unit') != 'mm' or
            len(contract.get('obstacle_boxes', [])) != 4):
        raise ValueError('FIXED_D2_CONTRACT_CHANGED')
    b=[vec(x,6) for x in contract['obstacle_boxes']]
    lo=b[0][0];hi=b[0][3]
    if not lo < hi or any(x[0]!=lo or x[3]!=hi for x in b):
        raise ValueError('GUIDE_X_EXTENSION_CHANGED')
    moving=vec(contract['moving_box'],6)
    q=(lo-F(1),moving[1],moving[2],hi+F(1),moving[4],moving[5])
    if q!=tuple(map(F,(-201,-115,1000,-179,-95,1040))):
        raise ValueError('FIXED_D2_Q_NOT_AS_EXPECTED')
    if not all(q[i]<q[i+3] for i in range(3)):
        raise ValueError('Q_DEGENERATE')
    if not (b[0][4] < q[1] < q[4] < b[1][1] and
            b[2][5] < q[2] < q[5] < b[3][2]):
        raise ValueError('D2_Q_NOT_INSIDE_PASSAGE')
    return q,b


def gap_sq(a,b):
    """Exact squared Euclidean distance between two closed AABBs."""
    ds=[max(a[i]-b[i+3],b[i]-a[i+3],F(0)) for i in range(3)]
    return sum(v*v for v in ds)


def face_rects(face):
    plane=plane_mapping(face)
    if (face.get('status')!='PASS' or
            face.get('represented_trim_polygon')!='PASS' or
            face.get('represented_material_side',{}).get('status')!='PASS'):
        raise ValueError('UNVERIFIED_REPRESENTED_FACE')
    wires=face['wires']
    if len(wires) not in (1,2) or [x['role'] for x in wires]!=(
            ['outer','inner'] if len(wires)==2 else ['outer']):
        raise ValueError('WRONG_FACE_WIRE_INVENTORY')
    rects=[]
    occurrences=[]
    for w in wires:
        if len(w.get('uses',[]))!=4:
            raise ValueError('NON_RECTANGULAR_WIRE')
        segments=[]
        for use in w['uses']:
            if (use.get('represented_affine_link')!='PASS' or
                    use.get('pcurve_type') not in ('Line2d','Line2dSegment') or
                    use.get('curve_type')!='Line'):
                raise ValueError('STORED_LINEAR_LINK_MISSING')
            p0,p1=[vec(v,2) for v in use['pcurve']]
            c0,c1=[vec(v,3) for v in use['curve']]
            a,b=vec(use['pcurve_range'],2)
            if a>=b or (a,b)!=vec(use['curve_range'],2):
                raise ValueError('PARAMETER_RANGE_MISMATCH')
            if (surface_point(plane,p0)!=c0 or
                    tuple(p1[0]*plane[1][i]+p1[1]*plane[2][i] for i in range(3))!=c1):
                raise ValueError('NON_EQUAL_CURVE_SURFACE_OVER_INTERVAL')
            ends=[tuple(p0[i]+t*p1[i] for i in range(2)) for t in (a,b)]
            if use['orientation']=='Reversed':
                ends.reverse()
            elif use['orientation']!='Forward':
                raise ValueError('UNKNOWN_EDGE_ORIENTATION')
            if ends != [vec(v,2) for v in use['directed_uv']]:
                raise ValueError('DIRECTED_UV_CHANGED')
            if [surface_point(plane,v) for v in ends]!=[vec(p,3) for p in use['directed_3d']]:
                raise ValueError('DIRECTED_WORLD_ENDS_CHANGED')
            segments.append(ends)
            occurrences.append((face['face'],w['wire'],use['edge'],use['use']))
        if any(segments[i][1]!=segments[(i+1)%4][0] for i in range(4)):
            raise ValueError('UNCONNECTED_4_EDGE_LOOP')
        corners=[pair[0] for pair in segments]
        if corners != [vec(x,2) for x in w['directed_loop']]:
            raise ValueError('WIRE_DIRECTION_CHANGED')
        rect=rectangle(corners)
        if rect['signed_area2']!=F(w['signed_area2_mm2']):
            raise ValueError('SIGNED_AREA_CHANGED')
        expected=(1 if face['orientation']=='Forward' else -1)*(1 if w['role']=='outer' else -1)
        if (rect['signed_area2']>0)!=(expected>0):
            raise ValueError('LOOP_ORIENTATION_CHANGED')
        rects.append(rect)
    if len(rects)==2 and not strict_nested(*rects):
        raise ValueError('HOLE_NOT_STRICTLY_NESTED')
    outer=rects[0]
    if vec(face['uv_bounds'],4)!=(outer['low'][0],outer['high'][0],
                                  outer['low'][1],outer['high'][1]):
        raise ValueError('FACE_UV_BOUNDS_CHANGED')
    # Orthogonal strips partition the closed ring exactly. For single wires,
    # use the full closed rectangle.
    u0,v0=outer['low'];u1,v1=outer['high']
    uvboxes=[(u0,v0,u1,v1)]
    if len(rects)==2:
        h0,h1=rects[1]['low'],rects[1]['high']
        uvboxes=[(u0,v0,h0[0],v1),(h1[0],v0,u1,v1),
                 (h0[0],v0,h1[0],h0[1]),(h0[0],h1[1],h1[0],v1)]
    world=[]
    for ua,va,ub,vb in uvboxes:
        if ua>=ub or va>=vb:
            raise ValueError('DEGENERATE_FACE_PARTITION')
        coords=[surface_point(plane,(u,v)) for u,v in product((ua,ub),(va,vb))]
        world.append(tuple(min(p[i] for p in coords) for i in range(3))+
                     tuple(max(p[i] for p in coords) for i in range(3)))
    return world,occurrences


def calculate(contract,trim,stored,native):
    q,boxes=exact_q(contract)
    if (trim.get('source_fcstd_sha256')!=FCSTD_SHA or
            trim.get('source_d2_sha256')!=D2_SHA or
            trim.get('parts',{}).get(GUIDE,{}).get('source_brep_sha256')!=GUIDE_BREP_SHA):
        raise ValueError('UNPINNED_BREP_TRIM_SOURCE')
    g=trim['parts'][GUIDE]
    faces=g['faces']
    if (g.get('status')!='PASS' or len(faces)!=10 or
            [f['face'] for f in faces]!=list(range(10))):
        raise ValueError('FIXED_FACE_CENSUS_CHANGED')
    if (len(stored)!=48 or
            any(s.get('status')!='PASS' for s in stored)):
        raise ValueError('STORED_PCURVE_48_WITNESSES_MISSING')
    store={(s['face'],s['wire'],s['edge'],s['formula_use_order']) for s in stored}
    if len(store)!=48:
        raise ValueError('DUPLICATED_SAVED_USES')
    observed=[];used=[];roles={'outer':0,'inner':0}
    for f in faces:
        world,occurrences=face_rects(f)
        used.extend(occurrences)
        for w in f['wires']:roles[w['role']]+=1
        d2=min(gap_sq(w,q) for w in world)
        if d2<=0:
            raise ValueError('Q_INTERSECTS_EXACT_REPRESENTED_FACE:'+str(f['face']))
        observed.append({'face':f['face'],'wire_count':len(f['wires']),
                         'represented_piece_count':len(world),
                         'exact_boundary_to_q_distance_sq_mm2':str(d2),
                         'native_observation':native['faces'][f['face']]})
    if len(used)!=48 or set(used)!=store or len(set(used))!=48:
        raise ValueError('STORED_PCURVE_TO_FULL_BOUNDARY_JOIN_FAIL')
    if roles!={'outer':10,'inner':2} or [
            f['face'] for f in faces if len(f['wires'])==2]!=[0,9]:
        raise ValueError('INNER_HOLE_FACE_INVENTORY_CHANGED')
    for b in boxes:
        if gap_sq(b,q)<=0:
            raise ValueError('Q_INTERSECTS_FIXED_D2_MATERIAL')
    native_result=check_native(native,q,observed,faces)
    minimum=min(F(row['exact_boundary_to_q_distance_sq_mm2']) for row in observed)
    if minimum!=1:
        raise ValueError('FIXED_EXACT_CANDIDATE_CLEARANCE_CHANGED')
    return {
        'schema':'d5d-guide-q-through-void-v1','status':'PASS',
        'q_source':'existing D2 moving cross-section plus 1 mm outside both Guide X faces',
        'q_closed_box_mm':[str(x) for x in q],
        'exact_represented_boundary_disjoint':'PASS',
        'exact_represented_boundary_min_distance_sq_mm2':str(minimum),
        'exact_represented_boundary_min_distance_mm':'1',
        'exact_d2_material_disjoint':'PASS',
        'face_count':len(faces),'full_face_oriented_pcurve_uses':len(used),
        'hole_face_indices':[0,9],
        'native_face_distance_observation':native_result,
        'face_results':observed,
        'conditional_continuity_argument':(
            'Q is convex and connected. If the actual solid is a correctly '
            'oriented closed set whose full boundary equals the 10 represented '
            'trimmed faces, and Q is disjoint from that actual boundary, an '
            'OUT point in Q implies every point of Q is OUT. These premises '
            'are not made exact by numerical OCCT observations.'),
        'conditional_continuity_model':'PASS',
        'native_10_face_boundary_nonintersection_certificate':'UNKNOWN',
        'native_full_q_void_inclusion':'UNKNOWN',
        'native_full_solid_material_set':'UNKNOWN',
        'native_representative_interval':'NOT_TESTED',
        'finite_native_real_error_upper_mm':None,
    }


def main(trim_path,stored_path,native_path,output):
    output.mkdir(parents=True,exist_ok=False)
    if h(FCSTD.read_bytes())!=FCSTD_SHA or h(CONTRACT.read_bytes())!=D2_SHA:
        raise ValueError('PINNED_CAD_OR_D2_CHANGED')
    with ZipFile(FCSTD) as z:
        if h(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError('PINNED_GUIDE_BREP_CHANGED')
    raw=[p.read_bytes() for p in (trim_path,stored_path,native_path)]
    if h(raw[0])!=TRIM_SHA:
        raise ValueError('PINNED_TRIM_CHANGED')
    try:
        report=calculate(json.loads(CONTRACT.read_text(encoding='utf-8')),
                         json.loads(raw[0]),
                         json.loads(raw[1])['parts'][GUIDE],
                         json.loads(raw[2]))
    except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError) as ex:
        report={'status':'FAIL','reason':str(ex),
                'native_full_q_void_inclusion':'UNKNOWN',
                'native_representative_interval':'NOT_TESTED'}
    report['source_sha256']={'trim':h(raw[0]),'stored':h(raw[1]),'native':h(raw[2]),
                             'fcstd':FCSTD_SHA,'d2':D2_SHA,'guide_brep':GUIDE_BREP_SHA}
    (output/'through-q.json').write_text(json.dumps(report,ensure_ascii=False,
                                       indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return 0 if report['status']=='PASS' else 2


if __name__=='__main__':
    if len(sys.argv)!=5:
        raise SystemExit('usage: through_q.py TRIM STORED_REPORT NATIVE_REPORT OUTPUT_DIR')
    sys.exit(main(*(Path(x) for x in sys.argv[1:])))
