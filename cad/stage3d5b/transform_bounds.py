"""Exact conditional affine/error arithmetic; never a real-BRep certificate.

All lengths are metres unless a chain explicitly declares mm. Rational strings
are exact *mathematical inputs*. ``stored_float`` encloses only the represented
IEEE value, not the unknown real which a CAD API rounded to that value. No
matrix is projected onto SO(3), and no missing uncertainty is replaced by zero.
The conditional PASS results prove arithmetic given the supplied enclosures;
their derivation from BRep/Document semantics remains a separate UNKNOWN.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
import re


def q(value):
    if isinstance(value, Fraction):
        return value
    if type(value) is int:
        return Fraction(value)
    if not isinstance(value, str) or not re.fullmatch(r'-?\d+(?:\.\d+|/\d+)?', value):
        raise ValueError('exact-rational-required; unknown reals need justified intervals')
    return Fraction(value)


@dataclass(frozen=True)
class Interval:
    lo: Fraction
    hi: Fraction

    def __post_init__(self):
        object.__setattr__(self, 'lo', q(self.lo))
        object.__setattr__(self, 'hi', q(self.hi))
        if self.lo > self.hi:
            raise ValueError('reversed-interval')

    @classmethod
    def point(cls, value):
        return cls(q(value), q(value))

    def __add__(self, other):
        other = as_interval(other)
        return Interval(self.lo + other.lo, self.hi + other.hi)

    def __neg__(self):
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + -as_interval(other)

    def __mul__(self, other):
        other = as_interval(other)
        values = [a*b for a in (self.lo, self.hi) for b in (other.lo, other.hi)]
        return Interval(min(values), max(values))

    def abs_upper(self):
        return max(abs(self.lo), abs(self.hi))

    def json(self):
        return [str(self.lo), str(self.hi)]


def as_interval(value):
    if isinstance(value, Interval):
        return value
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return Interval(value[0], value[1])
    return Interval.point(value)


def stored_float(value):
    """Exact binary-float value, NOT an enclosure of an unknown underlying real."""
    if type(value) is not float or not math.isfinite(value):
        raise ValueError('finite-binary-float-required')
    n, d = value.as_integer_ratio()
    return Interval.point(Fraction(n, d))


def affine(matrix):
    """3x4 row-major affine matrix; generic coefficients, not asserted rigid."""
    if not isinstance(matrix, (list, tuple)) or len(matrix) != 12:
        raise ValueError('affine-3x4-required')
    return [as_interval(v) for v in matrix]


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]


def compose(outer, inner):
    """Return outer(inner(x)); operations are exact interval operations."""
    a, b = affine(outer), affine(inner)
    result = []
    for i in range(3):
        for j in range(4):
            v = Interval.point(0)
            for k in range(3):
                v = v + a[4*i+k]*b[4*k+j]
            if j == 3:
                v = v + a[4*i+3]
            result.append(v)
    return result


def apply(matrix, box):
    a = affine(matrix)
    if not isinstance(box, (list, tuple)) or len(box) != 3:
        raise ValueError('three-coordinate-domain-required')
    x = [as_interval(v) for v in box]
    return [sum_intervals([a[4*i+j]*x[j] for j in range(3)] + [a[4*i+3]])
            for i in range(3)]


def sum_intervals(values):
    result = Interval.point(0)
    for value in values:
        result = result + value
    return result


def affine_error(actual_enclosure, nominal, domain_box_m):
    """For all enclosed A,t,x: ||(Ax+t)-(Bx+u)||2 <= sum(row abs-upper).

    A single interval per *coefficient* encloses every actual coefficient.
    Interval independence can overestimate but cannot underestimate this bound.
    This is a theorem over supplied rational intervals, not their CAD provenance.
    """
    if actual_enclosure is None or nominal is None or domain_box_m is None:
        return {'status': 'UNKNOWN', 'reason': 'missing-transform-or-domain-enclosure',
                'error_m': None, 'real_brep': 'UNKNOWN'}
    a, b = affine(actual_enclosure), affine(nominal)
    difference = [x-y for x, y in zip(a, b)]
    rows = apply(difference, domain_box_m)
    upper = sum((r.abs_upper() for r in rows), Fraction(0))
    return {'status': 'PASS', 'scope': 'conditional affine arithmetic only',
            'norm': 'L1 upper bounds Euclidean error', 'error_m': str(upper),
            'row_intervals_m': [r.json() for r in rows],
            'formula': 'sum_i max_abs(sum_j (Aij-Bij)*Xj + (ti-ui))',
            'coefficient_provenance': 'not established by this function',
            'real_brep': 'UNKNOWN'}


def observed_matrix_error(observed_4x4, nominal_3x4, domain_box_m):
    """Capture representation exactly, while refusing unknown CAD-real errors."""
    if not isinstance(observed_4x4, (tuple, list)) or len(observed_4x4) != 16:
        raise ValueError('observed-4x4-required')
    # Do not first round a rational/decimal input to float here. These values
    # must be the API's binary floats themselves; other inputs use explicit
    # rational intervals through affine_error instead.
    a = [stored_float(v) for v in observed_4x4]
    if any(a[12+i] != Interval.point(0) for i in range(3)) or a[15] != Interval.point(1):
        raise ValueError('non-affine-observed-last-row')
    represented = affine_error(a[:12], nominal_3x4, domain_box_m)
    return {'status': 'UNKNOWN',
            'reason': 'API-value-to-geometric-real-and-frame-link-not-enclosed',
            'represented_coefficients': [v.json() for v in a[:12]],
            'represented_vs_nominal': represented,
            'real_transform_error_m': None, 'real_brep': 'UNKNOWN'}


def round_enclosure(value, quantum):
    """Outward grid enclosure, including negative and asymmetric endpoints."""
    v, h = as_interval(value), q(quantum)
    if h <= 0:
        raise ValueError('positive-quantum-required')
    lo, hi = v.lo/h, v.hi/h
    floor = lo.numerator // lo.denominator
    ceil = -((-hi.numerator) // hi.denominator)
    return Interval(floor*h, ceil*h)


ERROR_COMPONENTS = ('geometry', 'extraction', 'transform', 'unit',
                    'arithmetic', 'rounding', 'pose')


def combined_error(components, reported_upper=None):
    """Conditional sum; None stays UNKNOWN rather than silently contributing 0."""
    if set(components) != set(ERROR_COMPONENTS):
        raise ValueError('error-component-inventory')
    known = [q(v) for v in components.values() if v is not None]
    if any(v < 0 for v in known):
        raise ValueError('negative-error')
    if any(v is None for v in components.values()):
        return {'status': 'UNKNOWN', 'error_m': None,
                'missing': [k for k, v in components.items() if v is None],
                'real_brep': 'UNKNOWN'}
    upper = sum(known, Fraction(0))
    if reported_upper is not None and q(reported_upper) < upper:
        return {'status': 'FAIL', 'reason': 'underreported-error', 'required_m': str(upper),
                'real_brep': 'UNKNOWN'}
    return {'status': 'PASS', 'scope': 'conditional additive Euclidean error bound only',
            'error_m': str(upper), 'real_brep': 'UNKNOWN'}


def offset_box(box_m, error_m, direction):
    """Conditional conservative offsets, not a verifier of BRep premises.

    Outer: A subset Q (+) Ball(e) implies A subset coordinate-expanded Q.
    Inner: if Q is an OPEN model void and every point in Q farther than e
    from its boundary is truly empty, coordinate-eroded OPEN Q is truly empty.
    The latter premise is stronger than material's one-way outer inclusion;
    one must not infer a real empty-space result from A subset M alone.
    Euclidean distance to an axis-box boundary is its minimum axis margin.
    """
    if direction not in ('material-outer', 'void-inner'):
        raise ValueError('offset-direction')
    if error_m is None:
        return {'status': 'UNKNOWN', 'box_m': None, 'reason': 'missing-real-error-premise'}
    e = q(error_m)
    if e < 0 or len(box_m) != 3:
        raise ValueError('offset-domain')
    boxes = [as_interval(v) for v in box_m]
    if any(b.lo >= b.hi for b in boxes):
        raise ValueError('nonempty-three-dimensional-box-required')
    signs = (-1, 1) if direction == 'material-outer' else (1, -1)
    ends = [(b.lo+signs[0]*e, b.hi+signs[1]*e) for b in boxes]
    if any(lo >= hi for lo, hi in ends):
        return {'status': 'UNKNOWN', 'box_m': None, 'reason': 'empty-eroded-void'}
    return {'status': 'PASS', 'scope': 'conditional box offset arithmetic only',
            'box_m': [[str(lo), str(hi)] for lo, hi in ends],
            'boundary': 'closed' if direction == 'material-outer' else 'open',
            'direction': direction, 'real_brep': 'UNKNOWN'}


def chain(entries, expected_ids, start_frame, end_frame):
    """Validate a declared affine path against an independently supplied inventory.

    Each entry has id, from_frame, to_frame, matrix, from_unit, to_unit. A unit
    conversion is a separate exact diagonal mm->m step. Other steps preserve
    units. Unique IDs and exact order catch omission and repeated application
    relative to the supplied inventory; its actual Document correspondence is
    not proven. Matrices are never coerced into exact rotations.
    """
    if expected_ids is None:
        return {'status': 'UNKNOWN', 'reason': 'missing-independent-path-inventory',
                'real_brep': 'UNKNOWN'}
    ids = [e['id'] for e in entries]
    if ids != expected_ids or len(ids) != len(set(ids)):
        return {'status': 'FAIL', 'reason': 'placement-order-omission-or-double-application',
                'real_brep': 'UNKNOWN'}
    result, frame, unit, scales = affine(IDENTITY), start_frame, 'mm', 0
    for entry in entries:
        if entry['from_frame'] != frame or entry['from_unit'] != unit:
            return {'status': 'FAIL', 'reason': 'frame-or-unit-chain-break', 'real_brep': 'UNKNOWN'}
        a = affine(entry['matrix'])
        if entry['from_unit'] != entry['to_unit']:
            target = [Interval.point(Fraction(v, 1000)) for v in IDENTITY]
            # Only the three diagonal linear coefficients are scaled; identity
            # translations are zero, so the same construction is exact.
            if (entry['from_unit'], entry['to_unit']) != ('mm', 'm') or a != target:
                return {'status': 'FAIL', 'reason': 'unit-conversion-must-be-exact-mm-to-m',
                        'real_brep': 'UNKNOWN'}
            scales += 1
        result = compose(a, result)
        frame, unit = entry['to_frame'], entry['to_unit']
    if frame != end_frame or unit != 'm' or scales != 1:
        return {'status': 'FAIL', 'reason': 'incomplete-path-or-unit-conversion-count',
                'real_brep': 'UNKNOWN'}
    return {'status': 'PASS', 'scope': 'declared path arithmetic, not Document equivalence',
            'matrix': [v.json() for v in result], 'real_brep': 'UNKNOWN'}


def translation_motion(interval_vectors_m, reference_m, extra_error_m=None):
    """All-position translation displacement, conditional on enclosed path.

    Fixed orientation/axis is a premise. The reference must be stated explicitly.
    L1 path displacement bounds Euclidean displacement; no endpoint sampling.
    Unknown state/rotation error means no finite motion certificate.
    """
    if extra_error_m is None:
        return {'status': 'UNKNOWN', 'motion_m': None, 'reason': 'unbounded-state-or-rotation-error'}
    if len(interval_vectors_m) != 3 or len(reference_m) != 3:
        raise ValueError('three-vector-required')
    e = q(extra_error_m)
    if e < 0:
        raise ValueError('negative-motion-error')
    delta = [as_interval(x)-q(r) for x, r in zip(interval_vectors_m, reference_m)]
    upper = sum((x.abs_upper() for x in delta), e)
    return {'status': 'PASS', 'scope': 'conditional fixed-orientation translation only',
            'motion_m': str(upper), 'reference_m': [str(q(r)) for r in reference_m],
            'real_brep': 'UNKNOWN'}


def distance_lower(model_lower_m, shape_a_m, shape_b_m, motion_a_m, motion_b_m):
    """Conditional candidate lower bound; nonpositive is UNKNOWN, not penetration."""
    values = [model_lower_m, shape_a_m, shape_b_m, motion_a_m, motion_b_m]
    if any(v is None for v in values):
        return {'status': 'UNKNOWN', 'lower_m': None, 'reason': 'missing-shape-or-motion-bound'}
    lower, ea, eb, da, db = map(q, values)
    if min(ea, eb, da, db) < 0:
        raise ValueError('negative-bound')
    result = lower-ea-eb-da-db
    return {'status': 'PASS' if result > 0 else 'UNKNOWN', 'lower_m': str(result),
            'scope': 'conditional distance arithmetic only', 'real_brep': 'UNKNOWN'}
