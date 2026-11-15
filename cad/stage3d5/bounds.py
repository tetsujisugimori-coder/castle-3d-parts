"""Exact, synthetic orthotope certificate. Never certifies a BRep.

All coordinates are decimal/rational STRINGS in metres. For corresponding
closed cells A,B, coordinate clamping gives distance <= sum_i max(|a_i-b_i|,
|A_i-B_i|). The L1 bound dominates Euclidean distance. Taking the maximum
over a COMPLETE source-cell cover proves directed union containment.
The cover is an axiom for synthetic fixtures only; OCCT extraction does not
establish it. Real CAD is deliberately kept UNKNOWN by this module.
"""
from fractions import Fraction
import re


def q(value):
    if not isinstance(value, str) or not re.fullmatch(r'-?\d+(?:\.\d+|/\d+)?', value):
        raise ValueError('exact rational string required')
    return Fraction(value)


def cell(value):
    if len(value) != 6:
        raise ValueError('six coordinates required')
    values = tuple(map(q, value))
    if any(values[i] >= values[i+3] for i in range(3)):
        raise ValueError('degenerate or reversed cell')
    return values


def directed_bound(a, b):
    a, b = cell(a), cell(b)
    return sum(max(abs(a[i]-b[i]), abs(a[i+3]-b[i+3])) for i in range(3))


def validate(data):
    """Fail closed; unknown evidence cannot become a positive CAD claim."""
    try:
        if not isinstance(data, dict):
            raise ValueError('certificate object required')
        if data['kind'] != 'synthetic-exact-cell-union-v1':
            return {'status': 'UNKNOWN', 'reason': 'real BRep cover/inclusion unproved'}
        if data['unit'] != 'm' or data['coordinates'] != 'world-right-handed-Z-up':
            raise ValueError('C: units/coordinate convention')
        src, dst = data['source'], data['model']
        for solid in (src, dst):
            if not isinstance(solid['cells'], dict):
                raise ValueError('cell inventory must be an object')
            for box in solid['cells'].values():
                cell(box)
        # Inventory and semantic checks are contract checks, not topology proofs.
        for category in ('faces', 'holes'):
            actual, expected = src[category], dst[category]
            if set(actual) != set(expected):
                raise ValueError('A/B: incomplete inventory')
            for key in actual:
                if actual[key] != expected[key]:
                    raise ValueError('A/B: normal, hole or orientation mismatch: '+key)
        if src['transform'] != dst['transform']:
            raise ValueError('C: unresolved placement difference')
        if not isinstance(data['mapping'], dict):
            raise ValueError('A: cell map must be an object')
        if not src['cells'] or set(data['mapping']) != set(src['cells']):
            raise ValueError('A: incomplete source cell map')
        if any(k not in dst['cells'] for k in data['mapping'].values()):
            raise ValueError('A: missing model cell')
        epsilon = max(directed_bound(src['cells'][k], dst['cells'][v])
                      for k, v in data['mapping'].items())
        # These are exact synthetic sets: all other error components MUST be 0.
        errors = data['errors_m']
        required = {'brep_tolerance', 'extraction', 'placement', 'floating_point', 'predicate'}
        if set(errors) != required or any(q(v) != 0 for v in errors.values()):
            return {'status': 'UNKNOWN', 'reason': 'D: nonzero/unproved non-geometric error'}
        if q(data['epsilon_m']) < epsilon or q(data['epsilon_m']) < 0:
            raise ValueError('D: claimed bound smaller than proven cell bound')
        return {'status': 'PASS', 'scope': 'synthetic directed cell-union containment only',
                'epsilon_m': str(epsilon), 'real_cad': 'UNKNOWN'}
    except (KeyError, ValueError, TypeError, ZeroDivisionError, IndexError, AttributeError) as error:
        return {'status': 'FAIL', 'reason': str(error)}


def continuous_lower_bound(lower, epsilon_a, epsilon_b, movement_a, movement_b):
    """Caller must supply independently proven bounds, not sample distances.

    Pure arithmetic helper, NOT an admission path into the 128-interval CAD
    verifier. None represents missing evidence; a nonpositive result does not
    distinguish contact from penetration.
    """
    if any(v is None for v in (lower, epsilon_a, epsilon_b, movement_a, movement_b)):
        return {'status': 'UNKNOWN', 'reason': 'missing bound'}
    try:
        l, ea, eb, ma, mb = map(q, (lower, epsilon_a, epsilon_b, movement_a, movement_b))
        if min(l, ea, eb, ma, mb) < 0:
            raise ValueError('negative distance/error bound')
        result = l-ea-eb-ma-mb
        return {'status': 'PASS' if result > 0 else 'UNKNOWN',
                'scope': 'conditional arithmetic only', 'lower_m': str(result)}
    except (ValueError, ZeroDivisionError) as error:
        return {'status': 'FAIL', 'reason': str(error)}


def rotation_chord_bound(radius, angle_abs_upper, translation, rounding):
    """R*min(alpha,2) >= 2R*sin(alpha/2) for 0<=alpha<=pi;
    for wider ranges the diameter 2R bounds all displacements.
    Fixed axis/pivot and rigid shape are REQUIRED external premises.
    radians, metres; rational upper bounds avoid transcendental rounding.
    """
    r, a, t, e = map(q, (radius, angle_abs_upper, translation, rounding))
    if min(r, a, t, e) < 0:
        raise ValueError('negative upper bound')
    return r*min(a, 2)+t+e
