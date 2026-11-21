"""Conditional exact correspondence from observed BRep topology to D2 boxes.

A PASS certifies only rational *represented candidates*. Native OCCT real-set
containment, placement equivalence and all-state motion remain UNKNOWN.
"""
from fractions import Fraction as F
from itertools import product
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'cad/stage3d5b'))
import planar_contract
import planar_native


def rational(value):
    if isinstance(value, bool) or isinstance(value, float) and not math.isfinite(value):
        raise ValueError('NONFINITE_OR_BOOLEAN_COEFFICIENT')
    if type(value) not in (str, int, float, F):
        raise ValueError('UNSUPPORTED_COEFFICIENT')
    return F(value)


def boxes_mm_to_m(raw):
    result = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            raise ValueError('BOX_SIX_ENDPOINTS_REQUIRED')
        b = tuple(rational(v) / 1000 for v in row)
        if any(b[j] >= b[j+3] for j in range(3)):
            raise ValueError('NONPOSITIVE_BOX')
        result.append(b)
    if not result:
        raise ValueError('NO_BOXES')
    return result


def boxes_m(raw):
    return [tuple(rational(v) for v in row) for row in raw]


def endpoint_link(t):
    """Check all represented affine Line(t) endpoints; not native pcurves."""
    seen = 0
    for edge in t['edges']:
        if edge['curve_type'] != 'Line' or edge['degenerated_observed']:
            raise ValueError('UNSUPPORTED_EDGE_FOR_AFFINE_LINK')
        ids = edge['vertex_ids']
        if not isinstance(ids, list) or len(ids) != 2 or len(set(ids)) != 2:
            raise ValueError('EDGE_VERTEX_PAIR')
        lo, hi = map(rational, edge['parameters_ieee'])
        if not lo < hi:
            raise ValueError('DEGENERATE_LINE_DOMAIN')
        origin = list(map(rational, edge['curve_location_mm_observed']))
        direction = list(map(rational, edge['curve_direction_observed']))
        if len(origin) != 3 or len(direction) != 3 or not any(direction):
            raise ValueError('DEGENERATE_LINE_FRAME')
        endpoints = {tuple(origin[j] + parameter * direction[j] for j in range(3))
                     for parameter in (lo, hi)}
        vertices = {tuple(map(rational, t['vertices'][vid]['point_mm_ieee'])) for vid in ids}
        if endpoints != vertices:
            raise ValueError('LINE_ENDPOINT_PARAMETERS_DISAGREE_WITH_VERTICES')
        seen += 1
    if not seen:
        raise ValueError('EMPTY_EDGE_INVENTORY')
    return {'status': 'PASS', 'edge_count': seen,
            'scope': 'exact stored affine coefficients and endpoints, not native-real geometry'}


def contained(a, b):
    """Exact closed finite box-union A subset B on a common rational grid.

    Occupancy is constant on open atomic cells. Each finite positive-volume
    closed box union is the closure of its interior, so this also covers all
    boundary points for the exact model. This is not empirical BRep sampling.
    """
    a, b = list(a), list(b)
    if not a or not b:
        raise ValueError('EMPTY_UNION')
    for box in a+b:
        if len(box) != 6 or any(box[j] >= box[j+3] for j in range(3)):
            raise ValueError('MALFORMED_ATOMIC_BOX')
    axis = [sorted({v[k] for v in a+b} | {v[k+3] for v in a+b}) for k in range(3)]
    if math.prod(len(v)-1 for v in axis) > 32768:
        raise ValueError('ATOMIC_GRID_BUDGET')
    def inside(union, point):
        return any(all(q[j] <= point[j] <= q[j+3] for j in range(3)) for q in union)
    checked = 0
    for indices in product(*(range(len(v)-1) for v in axis)):
        midpoint = tuple((axis[j][indices[j]]+axis[j][indices[j]+1])/2 for j in range(3))
        if inside(a, midpoint):
            checked += 1
            if not inside(b, midpoint):
                return {'status': 'FAIL', 'checked_atomic_interior_cells': checked,
                        'uncovered_exact_midpoint_m': list(map(str,midpoint))}
    return {'status': 'PASS', 'checked_atomic_interior_cells': checked,
            'scope': 'exact inclusion of finite closed positive rational box unions'}


def squared_gap_m(a, b):
    return sum(max(a[i]-b[i+3], b[i]-a[i+3], F(0))**2 for i in range(3))


def min_gap_squared_mm2(a, b):
    return min(squared_gap_m(x, y) for x in a for y in b) * 1000000


def correspondence(t, nominal_boxes_mm, query_mm=None):
    """Complete topology -> line/plane/trim candidate -> exact two-way material."""
    base = {'status': 'UNKNOWN', 'real_material_inclusion': 'UNKNOWN',
            'real_void_inclusion': 'UNKNOWN', 'real_parameter_trim': 'UNKNOWN',
            'real_finite_error': 'UNKNOWN', 'native_motion': 'NOT_TESTED',
            'scope': 'native-derived rational proposal, NOT actual OCCT-real set theorem'}
    try:
        edge = endpoint_link(t)
        proposal, winding = planar_native.proposal(t)
        theorem = planar_contract.verify_boundary(proposal)
        if theorem['status'] != 'PASS':
            return {**base, 'status': 'FAIL', 'reason': 'CANDIDATE_BOUNDARY_INVALID',
                    'boundary_result': theorem}
        observed = boxes_m(theorem['exact_material_cells_m'])
        nominal = boxes_mm_to_m(nominal_boxes_mm)
        outer = contained(observed, nominal)
        reverse = contained(nominal, observed)
        result = {**base, 'edge_parameter_link': edge,
                  'topology_inventory': t.get('counts'),
                  'winding_proposal_operations': winding,
                  'candidate_boundary_status': theorem['status'],
                  'candidate_material_cells_m': theorem['exact_material_cells_m'],
                  'candidate_boundary_face_count': theorem['face_count'],
                  'candidate_atomic_patches': theorem['atomic_boundary_patch_count'],
                  'candidate_outer_to_D2': outer, 'D2_to_candidate': reverse,
                  'represented_set_equality': 'PASS' if outer['status'] == reverse['status'] == 'PASS' else 'FAIL'}
        if query_mm is not None:
            q = boxes_mm_to_m([query_mm])[0]
            void = planar_contract.certify_void_box(proposal, list(map(str, q)))
            gap = min_gap_squared_mm2(observed, [q])
            result['candidate_void_to_query'] = {
                'status': 'PASS' if void['status'] == 'PASS' and gap > 0 else 'FAIL',
                'min_squared_gap_mm2': str(gap),
                'open_void_contract_status': void['status'],
                'scope': 'closed query strictly inside exact proposed open complement'}
        result['status'] = 'PASS' if result['represented_set_equality'] == 'PASS' and (
            'candidate_void_to_query' not in result or result['candidate_void_to_query']['status'] == 'PASS') else 'FAIL'
        return result
    except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError, AttributeError) as error:
        return {**base, 'status': 'FAIL', 'reason': str(error)}


def pair_gap(bolt, guide):
    """One fixed reference pose. Never issues a real native interval PASS."""
    if bolt.get('status') != 'PASS' or guide.get('status') != 'PASS':
        return {'status': 'NOT_TESTED',
                'reason': 'MISSING_CANDIDATE_CORRESPONDENCE', 'real_pair': 'UNKNOWN'}
    a = boxes_m(bolt['candidate_material_cells_m'])
    b = boxes_m(guide['candidate_material_cells_m'])
    sq = min_gap_squared_mm2(a, b)
    return {'status': 'PASS' if sq > 0 else 'FAIL',
            'min_squared_gap_mm2': str(sq),
            'scope': 'exact represented candidate sets at one reference pose',
            'real_pair': 'UNKNOWN', 'real_interval': 'NOT_TESTED'}
