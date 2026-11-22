"""All-point exact-real bridge: OCCT stored trimmed planar Faces -> D2 CSG boundary.

Not a floating point all-point FaceClassifier / SolidClassifier certificate.
Finite atomic cells are a symbolic partition, NOT point samples: membership
of each closed axis-aligned planar box is constant throughout each atom.
"""
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
from pathlib import Path
from zipfile import ZipFile
import json
import sys

from face_region import FCSTD_SHA,D2_SHA,GUIDE_BREP_SHA,TRIM_SHA,GUIDE
from one_slice import FCSTD,CONTRACT
from through_q import exact_q,face_rects,gap_sq


def sha(b):
    return sha256(b).hexdigest()


def v(row,n):
    if not isinstance(row,(list,tuple)) or len(row)!=n:
        raise ValueError("WRONG_DIMENSION")
    return tuple(F(x) for x in row)


def analytic_d2_boundary(contract):
    """Independently derive the boundary of FOUR existing CLOSED material boxes.

    M = [x0,x1] * ([y0,y1]*[z0,z1] \ (yi0,yi1)*(zi0,zi1)).
    This is a regular closed extruded rectangular annulus. Boundary consists
    of 4 outer walls, 4 inner walls and two annular ends, all CLOSED.
    """
    _,boxes=exact_q(contract)
    x0,x1=boxes[0][0],boxes[0][3]
    y0,y1=boxes[0][1],boxes[1][4]
    z0,z1=boxes[0][2],boxes[0][5]
    yi0,yi1=boxes[0][4],boxes[1][1]
    zi0,zi1=boxes[2][5],boxes[3][2]
    if not (x0<x1 and y0<yi0<yi1<y1 and z0<zi0<zi1<z1):
        raise ValueError("NON_RECTANGULAR_D2_CSG")
    expected=[
        (x0,y0,z0,x1,yi0,z1),
        (x0,yi1,z0,x1,y1,z1),
        (x0,yi0,z0,x1,yi1,zi0),
        (x0,yi0,zi1,x1,yi1,z1),
    ]
    if boxes!=expected:
        raise ValueError("D2_FOUR_MATERIAL_BOX_STRUCTURE_CHANGED")
    faces=[]
    def add(box,normal):
        if len(box)!=6 or len(normal)!=3:
            raise ValueError("BAD_ANALYTIC_FACET")
        faces.append((box,normal))
    neg=F(-1);pos=F(1);zero=F(0)
    for x,sgn in ((x0,neg),(x1,pos)):
        for ya,yb,za,zb in (
            (y0,yi0,z0,z1),(yi1,y1,z0,z1),
            (yi0,yi1,z0,zi0),(yi0,yi1,zi1,z1)):
            add((x,ya,za,x,yb,zb),(sgn,zero,zero))
    for y,sgn,za,zb in (
        (y0,neg,z0,z1),(y1,pos,z0,z1),
        (yi0,pos,zi0,zi1),(yi1,neg,zi0,zi1)):
        add((x0,y,za,x1,y,zb),(zero,sgn,zero))
    for z,sgn,ya,yb in (
        (z0,neg,y0,y1),(z1,pos,y0,y1),
        (zi0,pos,yi0,yi1),(zi1,neg,yi0,yi1)):
        add((x0,ya,z,x1,yb,z),(zero,zero,sgn))
    if len(faces)!=16:
        raise ValueError("ANALYTIC_BOUNDARY_PIECES_CHANGED")
    return faces


def contains(box,p):
    return all(box[i]<=p[i]<=box[i+3] for i in range(3))


def atoms_1d(bounds):
    """Singletons, open intervals, and two exterior unbounded atoms.

    Every AABB containment predicate is constant on each of these sets.
    Values are exact rational representatives, not approximate sampling.
    """
    values=sorted(set(bounds))
    if not values:raise ValueError("EMPTY_ATOM_LEVELS")
    return [values[0]-1]+[
        t for i,x in enumerate(values)
        for t in ([x,(x+values[i+1])/2] if i+1<len(values) else [x])
    ]+[values[-1]+1]


def equality_certificate(actual,expected):
    if not actual or not expected:
        raise ValueError("EMPTY_BOUNDARY")
    allboxes=[box for box,normal in actual+expected]
    levels=[
        atoms_1d([a[j] for a in allboxes]+[a[j+3] for a in allboxes])
        for j in range(3)
    ]
    count=0;boundary_atoms=0
    for p in product(*levels):
        actual_normals={normal for box,normal in actual if contains(box,p)}
        expected_normals={normal for box,normal in expected if contains(box,p)}
        if actual_normals!=expected_normals:
            raise ValueError("ORIENTED_BOUNDARY_ATOM_MISMATCH:"+str(p))
        count+=1
        if actual_normals:
            boundary_atoms+=1
    return count,boundary_atoms,[len(x) for x in levels]


def proof(native,trim,stored,solid,through,plane,contract):
    if (native.get("schema")!=1 or native.get("occt")!="7.8.1"
            or native.get("solid_count")!=1 or native.get("shell_count")!=1
            or native.get("face_count")!=10 or native.get("solid_valid_observed") is not True
            or native.get("shell_closed") is not True
            or native.get("native_all_point_classifier_equivalence")!="UNKNOWN"
            or native.get("native_full_q_void_inclusion")!="UNKNOWN"):
        raise ValueError("NATIVE_OCCT_FACE_SEMANTICS_INVALID")
    if native.get("solid_orientation")!="Forward" or native.get("shell_orientation")!="Forward":
        raise ValueError("NATIVE_SOLID_SHELL_ORIENTATION_CHANGED")
    g=trim.get('parts',{}).get(GUIDE,{})
    if (trim.get('source_fcstd_sha256')!=FCSTD_SHA
            or trim.get('source_d2_sha256')!=D2_SHA
            or g.get('source_brep_sha256')!=GUIDE_BREP_SHA
            or len(g.get("faces",[]))!=10 or g.get("status")!="PASS"):
        raise ValueError("PINNED_NATIVE_GEOMETRY_SOURCE_CHANGED")
    if (solid.get('status')!='PASS'
            or solid.get('native_solid_shell_face_ancestry')!='PASS'
            or solid.get('native_shell_faces_exhaustive')!='PASS'
            or solid.get('native_to_stored_all_48_oriented_uses')!='PASS'
            or solid.get('native_material_boundary_real_set_equality')!='UNKNOWN'):
        raise ValueError("NATIVE_FACE_EXHAUSTIVENESS_NOT_PASS")
    if (through.get('status')!='PASS'
            or through.get('exact_represented_boundary_disjoint')!='PASS'
            or through.get('exact_represented_boundary_min_distance_sq_mm2')!='1'
            or through.get('native_full_q_void_inclusion')!='UNKNOWN'):
        raise ValueError("FIXED_Q_NONINTERSECTION_CHANGED")
    if (plane.get('status')!='PASS' or plane.get('face_count')!=10
            or plane.get('native_raw_frame_equal_saved_world_planes')!='PASS'
            or plane.get('brep_extrema_total_error_status')!='UNKNOWN'
            or plane.get('native_full_q_void_inclusion')!='UNKNOWN'):
        raise ValueError("NATIVE_WORLD_PLANE_OR_SCOPE_CHANGED")
    from_store=stored.get('parts',{}).get(GUIDE,[])
    if len(from_store)!=48 or any(row.get('status')!='PASS' for row in from_store):
        raise ValueError("STORED_PCURVE_48_ORIGINAL_MISSING")
    stored_keys={(r['face'],r['wire'],r['edge'],r['formula_use_order']) for r in from_store}
    if len(stored_keys)!=48:
        raise ValueError("NON_UNIQUE_STORED_PCURVE_USE")
    if len(native.get('faces',[]))!=10 or [f.get('face') for f in native['faces']]!=list(range(10)):
        raise ValueError("NATIVE_FACES_NOT_0_THROUGH_9")
    uses=[];actual=[];face_records=[]
    for i,(nf,face) in enumerate(zip(native['faces'],g['faces'])):
        if (face['face']!=i or nf.get('orientation')!=face['orientation']
                or nf.get('surface_type')!='Geom_Plane'
                or nf.get('natural_restriction') is not False):
            raise ValueError("NATIVE_FACE_SURFACE_OR_RESTRICTION_NOT_COMPATIBLE:"+str(i))
        saved_wires=face['wires'];observed=nf.get('wires',[])
        if (nf.get('wire_count')!=len(saved_wires) or
                len(observed)!=len(saved_wires) or
                any(w.get('closed_flag') is not True for w in observed)):
            raise ValueError("NATIVE_FACE_WIRES_NOT_CLOSED:"+str(i))
        # Do not use wire iteration order to assign outer/inner. Identity is
        # established by earlier orientation/uses and the native face census.
        if sorted(w.get('orientation') for w in observed)!=sorted(
                w['orientation'] for w in saved_wires):
            raise ValueError("NATIVE_FACE_WIRE_ORIENTATIONS_CHANGED:"+str(i))
        world,occurrences=face_rects(face)
        uses+=occurrences
        normal=v(face['normal'],3)
        if sum(x*x for x in normal)!=1 or sum(int(x!=0) for x in normal)!=1:
            raise ValueError("NON_AXIS_NATIVE_FACE_NORMAL")
        if not world:
            raise ValueError("UNSUPPORTED_NON_RECTANGULAR_NATIVE_FACE")
        actual.extend((tuple(box),normal) for box in world)
        face_records.append({'face':i,'wire_count':len(saved_wires),
                             'material_side_outward_normal':[str(x) for x in normal],
                             'closed_planar_pieces':len(world),
                             'native_natural_restriction':False,
                             'native_closed_wires':True})
    if len(uses)!=48 or len(set(uses))!=48 or set(uses)!=stored_keys:
        raise ValueError("REAL_FACE_TO_STORED_EDGE_USES_NOT_BIJECTIVE")
    expected=analytic_d2_boundary(contract)
    atom_count,boundary_atom_count,shapes=equality_certificate(actual,expected)
    if len(actual)!=16 or len(expected)!=16:
        raise ValueError("REAL_VS_CSG_PIECES_COUNT_CHANGED")
    q,_=exact_q(contract)
    if any(gap_sq(box,q)<1 for box,normal in actual):
        raise ValueError("REAL_REPRESENTED_FACE_INTERSECTS_Q")
    if plane['model_boundary_distance_to_q_exact_mm']!='1':
        raise ValueError("ROUNDING_CERTIFICATE_DISTANT_FROM_Q_SOURCE")
    return {
        'schema':'d5d-guide-occt-trim-to-ideal-solid-semantic-bridge-v1',
        'status':'PASS',
        'source_semantics_occt':'7.8.1',
        'native_faces_natural_restriction_false':'PASS',
        'native_12_wires_closed_and_oriented':'PASS',
        'native_10_world_surfaces_match':'PASS',
        'native_10_faces_shell_exhaustive':'PASS',
        'native_48_edge_use_to_saved_pcurve':'PASS',
        'native_face_trimmed_exact_region_to_analytic_d2_csg_boundary':'PASS',
        'exact_real_oriented_boundary_all_point_equality':'PASS',
        'analytic_model_material_is_regular_closed':'PASS',
        'analytic_model_solid_boundary_is_all_ten_trimmed_faces':'PASS',
        'exact_real_boundary_nonintersect_fixed_q':'PASS',
        'atom_partition':'3D singleton/open-interval atom representatives: proof for ALL real points because membership is constant on each atom',
        'atom_count':atom_count,'boundary_atoms':boundary_atom_count,
        'axis_atom_counts':shapes,
        'face_piece_count':len(actual),'analytic_csg_piece_count':len(expected),
        'face_results':face_records,
        'ideal_occt_brep_semantics_solid_equals_csg':'CONDITIONAL_PASS',
        'semantic_condition':'The abstract OCCT BRep Solid denotes the regular closed bounded side of the stored oriented Shell, with each Face denoting exactly its Plane trimmed by stored opposite-oriented nested wires. The all-point exact-real boundary identity then implies ideal Solid equals D2 union.',
        'native_numeric_faceclassifier_all_point_equivalence':'UNKNOWN',
        'native_numeric_solidclassifier_all_point_equivalence':'UNKNOWN',
        'native_material_real_set_boundary_equivalence':'UNKNOWN',
        'native_full_q_void_inclusion':'UNKNOWN',
        'native_representative_interval':'NOT_TESTED',
        'finite_real_error_total_bound_mm':None,
        'scope':'All-point mathematical equality of stored ideal BRep trimmed Face boundaries and independent D2 regular-closed box union; not a proof of all-point finite-precision OCCT classifier behavior'
    }


def main(native_path,trim_path,stored_path,solid_path,through_path,plane_path,dest):
    dest.mkdir(parents=True,exist_ok=False)
    if sha(FCSTD.read_bytes())!=FCSTD_SHA or sha(CONTRACT.read_bytes())!=D2_SHA:
        raise ValueError("PINNED_CAD_D2_CHANGED")
    with ZipFile(FCSTD) as z:
        if sha(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError("PINNED_GUIDE_BREP_CHANGED")
    paths=[native_path,trim_path,stored_path,solid_path,through_path,plane_path]
    raw=[p.read_bytes() for p in paths]
    if sha(raw[1])!=TRIM_SHA:
        raise ValueError("PINNED_NATIVE_TRIM_CHANGED")
    try:
        result=proof(*(json.loads(b) for b in raw),
                     json.loads(CONTRACT.read_text(encoding='utf-8')))
    except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError) as e:
        result={'status':'FAIL','reason':str(e),
                'native_material_real_set_boundary_equivalence':'UNKNOWN',
                'native_full_q_void_inclusion':'UNKNOWN',
                'native_representative_interval':'NOT_TESTED'}
    result['inputs_sha256']={k:sha(b) for k,b in zip(
        ('native_face_semantics','trim','stored','solid_census','through_q','plane'),raw)}
    (dest/'semantic-bridge.json').write_text(
        json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',
        encoding='utf-8')
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    if len(sys.argv)!=8:
        raise SystemExit('usage: occt_semantic_bridge.py NATIVE TRIM STORED SOLID_CENSUS THROUGH_Q PLANE OUTDIR')
    sys.exit(main(*(Path(p) for p in sys.argv[1:])))
