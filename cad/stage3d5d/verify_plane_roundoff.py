"""Conditional, outward-rounded error bound for OCCT 7.8.1 Geom_Plane::D0.

This bounds the *direct surface-point evaluator* for the ten fixed native raw
plane frames, assuming IEEE-754 binary64 nearest-rounding and the OCCT 7.8.1
ElSLib::PlaneValue + gp_Pnt::Transform(translation) source path. This does NOT
bound BRepExtrema's optimizer, pcurve parameterization, or Solid occupancy.
"""
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA,D2_SHA,GUIDE_BREP_SHA,TRIM_SHA,GUIDE
from one_slice import FCSTD,CONTRACT

EPS=Q(1,2**53)  # unit roundoff in binary64 round-to-nearest
GAMMA16=16*EPS/(1-16*EPS)
DEC_SCALE=10**15

def h(b):
    return sha256(b).hexdigest()

def rat(v):
    if type(v) not in (int,float,str):
        raise ValueError('BAD_NATIVE_DOUBLE_OR_RATIONAL')
    return Q(v)  # float -> exact dyadic, never decimalize via str(float)

def vec(v,n):
    if len(v)!=n:return None
    return tuple(rat(x) for x in v)

def outward_up(q):
    return Q(-((-q.numerator*DEC_SCALE)//q.denominator), DEC_SCALE)

def outward_down(q):
    return Q((q.numerator*DEC_SCALE)//q.denominator, DEC_SCALE)

def bound_for_coordinate(origin,du,dv,translation,u_abs,v_abs):
    """A deliberately generous 16-op gamma bound for 5-op OCCT PlaneValue
    and translation addition, plus one U,V real->binary64 rounding each."""
    local_input=abs(du)*u_abs+abs(dv)*v_abs
    param_round=EPS*local_input
    total_abs=abs(origin)+abs(translation)+local_input+param_round
    return GAMMA16*total_abs+param_round

def analyze(native,trim,through):
    if (native.get('schema')!=1 or native.get('occt')!='7.8.1'
            or native.get('ieee_binary64_round_to_nearest') is not True
            or native.get('face_count')!=10 or len(native.get('faces',[]))!=10):
        raise ValueError('NATIVE_IEEE_OR_FACE_COUNT_UNVERIFIED')
    guide=trim.get('parts',{}).get(GUIDE,{})
    if (trim.get('source_fcstd_sha256')!=FCSTD_SHA
            or trim.get('source_d2_sha256')!=D2_SHA
            or guide.get('source_brep_sha256')!=GUIDE_BREP_SHA
            or guide.get('status')!='PASS' or len(guide.get('faces',[]))!=10):
        raise ValueError('UNPINNED_SAVED_FACE_COEFFICIENTS')
    if (through.get('status')!='PASS'
            or through.get('face_count')!=10
            or through.get('full_face_oriented_pcurve_uses')!=48
            or through.get('exact_represented_boundary_min_distance_sq_mm2')!='1'
            or through.get('native_full_q_void_inclusion')!='UNKNOWN'):
        raise ValueError('PRIOR_THROUGH_Q_PROOF_NOT_PASS')
    details=[]
    max_coord_bound=Q(0)
    for i,(n,f) in enumerate(zip(native['faces'],guide['faces'])):
        if n.get('face_index')!=i or f.get('face')!=i or n.get('orientation')!=f['orientation']:
            raise ValueError('NATIVE_FACE_IDENTITY_OR_ORIENTATION_CHANGED')
        o=vec(n['local_plane_origin_mm'],3)
        u=vec(n['native_u_direction'],3)
        v=vec(n['native_v_direction'],3)
        tr=vec(n['translation_mm'],3)
        box=vec(n['native_face_uv_bounds'],4)
        if None in (o,u,v,tr,box):
            raise ValueError('NATIVE_FRAME_LENGTH_BAD')
        if (n['transform_form'] not in ('Identity','Translation')
                or n.get('native_affine_matrix_is_identity') is not True
                or type(n.get('raw_transform_form_enum')) is not int
                or n['raw_transform_form_enum'] not in (0,1,2,4,5,6,7,8)):
            raise ValueError('NON_UNIT_LINEAR_NATIVE_FRAME')
        if n['transform_form']=='Identity' and n['raw_transform_form_enum']!=0:
            raise ValueError('TRANSFORM_FORM_IDENTITY_DISAGREEMENT')
        if n['transform_form']=='Identity' and tr!=(0,0,0):
            raise ValueError('IDENTITY_FRAME_HAS_TRANSLATION')
        if (sorted(sum(x!=0 for x in w) for w in (u,v))!=[1,1]
                or sum(x*x for x in u)!=1
                or sum(x*x for x in v)!=1
                or sum(u[j]*v[j] for j in range(3))!=0):
            raise ValueError('NON_UNIT_OR_NON_AXIS_NATIVE_PLANE')
        world=tuple(o[j]+tr[j] for j in range(3))
        recorded=tuple(tuple(Q(x) for x in r) for r in f['plane'])
        if (world,u,v)!=recorded:
            raise ValueError('RAW_NATIVE_SURFACE_DIFFERS_FROM_WORLD_REPRESENTATION:'+str(i))
        if box != tuple(Q(x) for x in f['uv_bounds']):
            raise ValueError('RAW_NATIVE_UV_BOUNDS_CHANGED:'+str(i))
        loc=tuple(tuple(Q(x) for x in row) for row in f['location'])
        expected=((Q(1),Q(0),Q(0),tr[0]),
                  (Q(0),Q(1),Q(0),tr[1]),
                  (Q(0),Q(0),Q(1),tr[2]),
                  (Q(0),Q(0),Q(0),Q(1)))
        if loc!=expected:
            raise ValueError('NATIVE_FRAME_LOCATION_DOUBLED_OR_DIFFERENT:'+str(i))
        umax=max(abs(box[0]),abs(box[1]))
        vmax=max(abs(box[2]),abs(box[3]))
        per=[bound_for_coordinate(o[j],u[j],v[j],tr[j],umax,vmax)
             for j in range(3)]
        localmax=max(per)
        max_coord_bound=max(max_coord_bound,localmax)
        details.append({
            'face':i,'native_raw_plane_frame_match':'PASS',
            'native_translation_match':'PASS',
            'coordinate_roundoff_upper_mm':str(localmax),
            'coordinate_roundoff_upper_decimal_mm':str(outward_up(localmax)),
            'exact_model_distance_to_q_sq_mm2':
                through['face_results'][i]['exact_boundary_to_q_distance_sq_mm2'],
        })
    # || delta xyz ||_2 <= sqrt(3)*delta_coord < 2*delta_coord.
    # Thus dist(evaluated face point,Q) >= 1-2*delta_coord for
    # every real UV of the model, under exactly the stated FP assumptions.
    euclidean_bound=2*max_coord_bound
    safe_distance=Q(1)-euclidean_bound
    if safe_distance<=0:
        raise ValueError('FP_EVALUATION_ERROR_OVERWHELMS_1_MM_GAP')
    return {
        'schema':'d5d-native-plane-point-roundoff-v1',
        'status':'PASS','face_count':10,
        'native_raw_frame_equal_saved_world_planes':'PASS',
        'binary64_rounding_assumptions_observed':'PASS',
        'occt_source_evaluation_path':'Geom_Plane::D0 -> ElSLib::PlaneValue; gp_Pnt::Transform gp_Translation',
        'roundoff_formula':'gamma16*(|local_origin|+|translation|+|du|*umax+|dv|*vmax+roundparam)+roundparam; roundparam=2^-53*(|du|*umax+|dv|*vmax)',
        'max_point_coordinate_roundoff_upper_exact_mm':str(max_coord_bound),
        'max_point_coordinate_roundoff_upper_decimal_mm':str(outward_up(max_coord_bound)),
        'max_euclidean_eval_roundoff_upper_exact_mm':str(euclidean_bound),
        'max_euclidean_eval_roundoff_upper_decimal_mm':str(outward_up(euclidean_bound)),
        'conditional_evaluated_plane_point_distance_to_exact_q_lower_exact_mm':str(safe_distance),
        'conditional_evaluated_plane_point_distance_to_exact_q_lower_decimal_mm':str(outward_down(safe_distance)),
        'model_boundary_distance_to_q_exact_mm':'1',
        'face_details':details,
        'bounded_operation':'direct 10-plane native stored frame surface point evaluation for real UV once rounded into binary64',
        'NOT_bounded':'BRepExtrema optimization, Geom2d/3d curve parameter generation, topology classification, arbitrary OpenCASCADE geometry',
        'brep_extrema_total_error_upper_mm':None,
        'brep_extrema_total_error_status':'UNKNOWN',
        'native_full_q_void_inclusion':'UNKNOWN',
        'native_material_outer':'UNKNOWN',
        'native_representative_interval':'NOT_TESTED',
    }

def main(native_path,trim_path,through_path,output_dir):
    output_dir.mkdir(parents=True,exist_ok=False)
    if h(FCSTD.read_bytes())!=FCSTD_SHA or h(CONTRACT.read_bytes())!=D2_SHA:
        raise ValueError('FIXED_SOURCE_SHA_CHANGED')
    with ZipFile(FCSTD) as z:
        if h(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError('GUIDE_BREP_SHA_CHANGED')
    raw=(native_path.read_bytes(),trim_path.read_bytes(),through_path.read_bytes())
    if h(raw[1])!=TRIM_SHA:
        raise ValueError('SAVED_TRIM_SHA_CHANGED')
    try:
        result=analyze(*(json.loads(b) for b in raw))
    except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError) as e:
        result={'status':'FAIL','reason':str(e),'brep_extrema_total_error_status':'UNKNOWN',
                'native_full_q_void_inclusion':'UNKNOWN','native_representative_interval':'NOT_TESTED'}
    result['inputs_sha256']={name:h(b) for name,b in zip(('native_raw_plane','trim','through_q'),raw)}
    (output_dir/'plane-roundoff-bound.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    if len(sys.argv)!=5:
        raise SystemExit('usage: verify_plane_roundoff.py NATIVE_JSON TRIM_JSON THROUGH_Q_JSON OUTPUT_DIR')
    sys.exit(main(*(Path(p) for p in sys.argv[1:])))
