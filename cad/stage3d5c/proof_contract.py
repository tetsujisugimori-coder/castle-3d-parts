"""Limited analytical obligations, NOT a native-real certificate issuer.

Exact polynomials concern explicit rational coefficients. No caller status/hash,
OCCT tolerance, sampled distance, or observation count establishes native sets.
"""
from fractions import Fraction as Q
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'stage3d5b'))
from transform_bounds import q, Interval, distance_lower, chain, IDENTITY

ERROR_DOMAINS = ('geometry', 'extraction', 'kernel_representation', 'coordinate_transform',
                 'unit', 'arithmetic_rounding', 'state_generation', 'continuous_displacement')
NATIVE_OBLIGATIONS = ('material_outer', 'void_inner', 'whole_trim_native_set',
                      'placement_all_states', 'finite_real_errors', 'motion_all_states')


def vector(x, n):
    if not isinstance(x, list) or len(x) != n: raise ValueError('VECTOR_DIMENSION')
    return list(map(q,x))


def line_plane_identity(case):
    """C(t)=c0+t*c1; P(t)=p0+t*p1; S(u,v)=o+u*U+v*V.

    Equality of constant and linear coefficients is equivalent to identity over
    any nondegenerate interval. Values are rational model definitions, never a
    proof that the API returned enclosing coefficients of the geometric real.
    """
    c0,c1=(vector(case[k],3) for k in ('c0','c1'))
    p0,p1=(vector(case[k],2) for k in ('p0','p1'))
    o,u,v=(vector(case[k],3) for k in ('origin','u_axis','v_axis'))
    lo,hi=vector(case['range'],2)
    if lo>=hi: raise ValueError('NONDEGENERATE_RANGE')
    if case['curve_type']!='Line' or case['pcurve_type']!='Line2d' or case['surface_type']!='Plane':
        return {'status':'UNKNOWN','reason':'UNSUPPORTED_ANALYTIC_FAMILY'}
    cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    if not any(cross):
        return {'status':'FAIL','reason':'DEGENERATE_PLANE_AXES','native_real_identity':'UNKNOWN'}
    a=[c0[i]-o[i]-p0[0]*u[i]-p0[1]*v[i] for i in range(3)]
    b=[c1[i]-p1[0]*u[i]-p1[1]*v[i] for i in range(3)]
    # Exact bound on represented discrepancy over the ENTIRE parameter domain.
    enclosure=[Interval.point(a[i])+Interval(lo,hi)*b[i] for i in range(3)]
    return {'status':'PASS' if not any(a+b) else 'FAIL',
            'reason':'COEFFICIENT_IDENTITY' if not any(a+b) else 'PCURVE_SURFACE_3D_INCONSISTENCY',
            'constant_residual':[str(x) for x in a], 'linear_residual':[str(x) for x in b],
            'represented_L1_upper_mm':str(sum((x.abs_upper() for x in enclosure),Q(0))),
            'scope':'defined rational line/plane model over full interval',
            'native_real_identity':'UNKNOWN'}


def error_sum(bounds, reported=None):
    if not isinstance(bounds,dict) or set(bounds)!=set(ERROR_DOMAINS): raise ValueError('ERROR_INVENTORY')
    known=[q(v) for v in bounds.values() if v is not None]
    if any(v<0 for v in known): raise ValueError('NEGATIVE_ERROR')
    missing=[k for k,v in bounds.items() if v is None]
    if missing: return {'status':'UNKNOWN','upper_m':None,'missing':missing,'scope':'conditional arithmetic'}
    total=sum(known,Q(0))
    if reported is not None and q(reported)<total:
        return {'status':'FAIL','reason':'UNDERREPORTED_ERROR','required_m':str(total)}
    return {'status':'PASS','upper_m':str(total),'scope':'sum of supplied bounds, not provenance certification'}


def representative(analytical_row, bounds, declarations=None):
    """Evaluate arithmetic separately; unproved native premises cannot be asserted.

    Declarations are retained as claims only. This bounded implementation has no
    proof-producing bridge from OCCT sets to real enclosures, hence cannot issue
    native PASS even if an input labels all premises PASS.
    """
    total=error_sum(bounds)
    candidate=None
    if total['status']=='PASS':
        candidate=distance_lower(str(q(analytical_row['clearance_lower'])/1000),total['upper_m'],'0','0','0')
    return {'status':'NOT_TESTED','native_safety':'NOT_TESTED',
            'analytical_row':analytical_row, 'conditional_arithmetic':candidate,
            'error_assessment':total, 'unproved_obligations':list(NATIVE_OBLIGATIONS),
            'supplied_declarations_not_evidence':declarations,
            'reason':'NO_CERTIFIED_NATIVE_REAL_BRIDGE',
            'native_intervals':{'PASS':0,'FAIL':0,'UNKNOWN':0,'NOT_TESTED':128}}


def fixed_path_controls():
    # Independent contract for SYNTHETIC nested translation, not native path.
    def step(id,a,b,m): return {'id':id,'from_frame':a,'to_frame':b,'from_unit':'mm','to_unit':'mm','matrix':m}
    obj=IDENTITY.copy();obj[3]=10
    parent=IDENTITY.copy();parent[7]=20
    entries=[step('object','local','parent',obj),step('parent','parent','world',parent),
        {'id':'mm-to-m','from_frame':'world','to_frame':'m-world','from_unit':'mm','to_unit':'m','matrix':[str(Q(x,1000)) for x in IDENTITY]}]
    return entries, ['object','parent','mm-to-m']
