"""Checks OCCT observations, without converting distances to certified bounds."""
from fractions import Fraction as F
import math

def check_native(native,q,modeled,faces):
    if (native.get('schema')!=1 or native.get('occt')!='7.8.1'
        or native.get('face_count')!=10 or native.get('solid_count')!=1
        or native.get('shell_count')!=1 or
        native.get('shell_closed_flag') is not True or
        native.get('brepcheck_solid_valid') is not True or
        native.get('native_all_point_void_inclusion')!='UNKNOWN'):
        raise ValueError('NATIVE_TOPOLOGY_OR_SCOPE_MISMATCH')
    if tuple(F(x) for x in native['q_closed_box_mm'])!=q:
        raise ValueError('NATIVE_Q_IS_DIFFERENT')
    if (native.get('one_center_point_mm')!=[-190,-105,1020] or
            native.get('one_center_state')!='OUT' or
            not 0 < float(native['one_center_tolerance_mm']) < 1e-4):
        raise ValueError('FIXED_Q_CENTER_NOT_NATIVE_OUT')
    if len(native.get('faces',[]))!=10:
        raise ValueError('NATIVE_FACE_COUNT_MISSING')
    results=[]
    for i,(item,record,model) in enumerate(zip(native['faces'],faces,modeled)):
        if (item.get('face_index')!=i or
                item.get('orientation')!=record['orientation'] or
                item.get('distance_is_done') is not True or
                type(item.get('distance_solution_count')) is not int or
                item['distance_solution_count']<1):
            raise ValueError('NATIVE_FACE_DISTANCE_NOT_OBSERVED:'+str(i))
        v=float(item['boundary_to_q_observed_distance_mm'])
        tol=float(item['face_tolerance_mm'])
        if not math.isfinite(v) or not math.isfinite(tol) or v<=0.5 or tol<0:
            raise ValueError('NATIVE_FACE_DISTANCE_NONPOSITIVE_OR_BAD:'+str(i))
        sq=F(model['exact_boundary_to_q_distance_sq_mm2'])
        # Consistency check on a numerical OCCT algorithm, not a proof bound.
        if abs(v*v-float(sq)) > 1e-4*max(1.0,float(sq)):
            raise ValueError('MODEL_NATIVE_DISTANCE_DISAGREEMENT:'+str(i))
        results.append({'face':i,
                        'occt_distance_to_closed_q_mm':v,
                        'occt_solutions':item['distance_solution_count'],
                        'comparison':'numerical observation consistent with exact modeled geometry'})
    return {'status':'PASS','scope':'10 numerical OCCT Face-to-Q distances and one OUT point; not an interval proof',
            'native_shell_closed_flag':True,
            'native_brepcheck_solid_valid':True,
            'one_center_point':native['one_center_point_mm'],
            'one_center_native_state':'OUT',
            'all_ten_faces_distance_done':True,
            'all_ten_distances_observed_positive':True,
            'native_faces':results,
            'all_point_certified_native_void':'UNKNOWN'}
