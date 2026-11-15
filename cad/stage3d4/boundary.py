"""Exact, bounded orthogonal cell-boundary checker; NOT a BRep converter.

Input coordinates denote exact rationals by contract, not rounded CAD observations.
Material is the bounded regular closed union of reconstructed cells.  All supplied
rectangles must equal its oriented boundary.  This theorem concerns that exact
representation only; it grants no authority to arbitrary exported BRep numbers.
"""
from fractions import Fraction as Q
from itertools import product
import hashlib
import json

VERSION = 'rational-orthogonal-boundary-v1'
MAX_FACES = 512
MAX_CELLS = 4096


def rational(value):
    if type(value) not in (str, int):
        raise ValueError('EXACT_RATIONAL_REQUIRED')
    try:
        result = Q(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError('INVALID_RATIONAL') from None
    if result.numerator.bit_length() > 256 or result.denominator.bit_length() > 256:
        raise ValueError('RATIONAL_BUDGET')
    return result


def box(value):
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError('BOX_REQUIRED')
    b = list(map(rational, value))
    if any(b[i] >= b[i + 3] for i in range(3)):
        raise ValueError('DEGENERATE_BOX')
    return b


def _axes(axis):
    return [i for i in range(3) if i != axis]


def _face_cells(face, grid):
    axis, c, u, v, sign = face
    a, b = _axes(axis)
    for i in range(grid[a].index(u[0]), grid[a].index(u[1])):
        for j in range(grid[b].index(v[0]), grid[b].index(v[1])):
            yield axis, grid[axis].index(c), i, j, sign


def _boundary(cells):
    faces = set()
    for cell in cells:
        for axis in range(3):
            a, b = _axes(axis)
            for sign in (-1, 1):
                neighbor = list(cell)
                neighbor[axis] += sign
                if tuple(neighbor) not in cells:
                    plane = cell[axis] + (1 if sign == 1 else 0)
                    faces.add((axis, plane, cell[a], cell[b], sign))
    return faces


def _face_vertices(face):
    axis, plane, i, j, _ = face
    a, b = _axes(axis)
    vertices = []
    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
        p = [0, 0, 0]
        p[axis], p[a], p[b] = plane, i + di, j + dj
        vertices.append(tuple(p))
    return vertices


def _manifold(faces, cells):
    # A single material component, not two objects silently combined.
    remaining = set(cells)
    queue = [remaining.pop()]
    while queue:
        c = queue.pop()
        for axis, sign in product(range(3), (-1, 1)):
            n = list(c); n[axis] += sign; n = tuple(n)
            if n in remaining:
                remaining.remove(n); queue.append(n)
    if remaining:
        raise ValueError('DISCONNECTED_MATERIAL')
    edges, vertices = {}, {}
    for f in faces:
        vs = _face_vertices(f)
        for v in vs:
            vertices.setdefault(v, set()).add(f)
        for i in range(4):
            edge = tuple(sorted((vs[i], vs[(i + 1) % 4])))
            edges.setdefault(edge, set()).add(f)
    if any(len(fs) != 2 for fs in edges.values()):
        raise ValueError('NONMANIFOLD_EDGE')
    # Each vertex link must be one connected cycle (all degrees already two).
    for vertex, incident in vertices.items():
        neighbors = {f: set() for f in incident}
        for edge, fs in edges.items():
            if vertex in edge:
                a, b = tuple(fs); neighbors[a].add(b); neighbors[b].add(a)
        reached = {next(iter(incident))}; queue = list(reached)
        while queue:
            f = queue.pop()
            for n in neighbors[f] - reached:
                reached.add(n); queue.append(n)
        if reached != incident:
            raise ValueError('NONMANIFOLD_VERTEX')


def verify_boundary(data):
    if not isinstance(data, dict) or set(data) != {'schema', 'unit', 'faces'}:
        raise ValueError('BOUNDARY_SCHEMA_FIELDS')
    if data['schema'] != VERSION or data['unit'] != 'mm':
        raise ValueError('BOUNDARY_SCHEMA_OR_UNIT')
    raw = data['faces']
    if not isinstance(raw, list) or not 6 <= len(raw) <= MAX_FACES:
        raise ValueError('FACE_COUNT')
    parsed, grid = [], [set(), set(), set()]
    for f in raw:
        if not isinstance(f, dict) or set(f) != {'axis', 'coordinate', 'u', 'v', 'normal'}:
            raise ValueError('RECTANGLE_FIELDS')
        axis, sign = f['axis'], f['normal']
        if type(axis) is not int or axis not in range(3) or type(sign) is not int or sign not in (-1, 1):
            raise ValueError('AXIS_OR_ORIENTATION')
        c = rational(f['coordinate'])
        ranges = []
        for name in ('u', 'v'):
            if not isinstance(f[name], list) or len(f[name]) != 2:
                raise ValueError('RECTANGLE_RANGE')
            lo, hi = map(rational, f[name])
            if lo >= hi:
                raise ValueError('DEGENERATE_FACE')
            ranges.append((lo, hi))
        a, b = _axes(axis)
        grid[axis].add(c); grid[a].update(ranges[0]); grid[b].update(ranges[1])
        parsed.append((axis, c, *ranges, sign))
    grid = [sorted(g) for g in grid]
    sizes = [len(g) - 1 for g in grid]
    if min(sizes) < 1 or sizes[0] * sizes[1] * sizes[2] > MAX_CELLS:
        raise ValueError('GRID_BUDGET_OR_DEGENERACY')
    supplied, locations = set(), set()
    for face in parsed:
        for f in _face_cells(face, grid):
            if f[:-1] in locations:
                raise ValueError('OVERLAPPING_OR_DUPLICATE_FACE')
            locations.add(f[:-1]); supplied.add(f)
    cells = set()
    for y, z in product(range(sizes[1]), range(sizes[2])):
        occupancy = 0
        for x in range(sizes[0] + 1):
            for sign in (-1, 1):
                if (0, x, y, z, sign) in supplied:
                    occupancy -= sign
            if occupancy not in (0, 1):
                raise ValueError('WINDING_ORIENTATION')
            if x < sizes[0] and occupancy:
                cells.add((x, y, z))
        if occupancy:
            raise ValueError('OPEN_BOUNDARY')
    if not cells:
        raise ValueError('EMPTY_MATERIAL')
    expected = _boundary(cells)
    if expected != supplied:
        raise ValueError('BOUNDARY_INCIDENCE_MISMATCH')
    _manifold(expected, cells)
    boxes = [[str(grid[i][c[i]]) for i in range(3)] +
             [str(grid[i][c[i] + 1]) for i in range(3)] for c in sorted(cells)]
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'version': VERSION, 'scope': 'exact rational boundary representation ONLY',
            'unit': 'mm', 'input_sha256': hashlib.sha256(canonical).hexdigest(),
            'oriented_closed_boundary': 'PASS', 'material_outer_cells': boxes,
            'material_cell_count': len(boxes), 'elementary_boundary_faces': len(expected),
            'arithmetic_error_mm': '0',
            'arithmetic_error_reason': 'exact rational operations on exact input representation, NOT BRep error',
            'native_brep_correspondence': 'UNKNOWN', 'cad_application': 'UNKNOWN'}


def from_boxes(values):
    """Synthetic/exact-model generator. Its output must pass verify_boundary."""
    bs = [box(b) for b in values]
    if not bs:
        raise ValueError('EMPTY_MATERIAL')
    grid = [sorted({b[i] for b in bs} | {b[i + 3] for b in bs}) for i in range(3)]
    sizes = [len(g) - 1 for g in grid]
    if sizes[0] * sizes[1] * sizes[2] > MAX_CELLS:
        raise ValueError('GRID_BUDGET_OR_DEGENERACY')
    cells = set()
    for c in product(*(range(n) for n in sizes)):
        if any(all(b[i] <= grid[i][c[i]] and grid[i][c[i] + 1] <= b[i + 3] for i in range(3)) for b in bs):
            cells.add(c)
    faces = []
    for axis, plane, i, j, sign in sorted(_boundary(cells)):
        a, b = _axes(axis)
        faces.append({'axis': axis, 'coordinate': str(grid[axis][plane]),
                      'u': [str(grid[a][i]), str(grid[a][i + 1])],
                      'v': [str(grid[b][j]), str(grid[b][j + 1])], 'normal': sign})
    return {'schema': VERSION, 'unit': 'mm', 'faces': faces}


def verify_void(data, candidate):
    """Closed candidate box must have strictly positive separation from material.

    Equality is UNKNOWN: a closed void certificate never includes material faces.
    """
    result = verify_boundary(data)
    hole = box(candidate)
    cells = [box(b) for b in result['material_outer_cells']]
    separation_squared = min(sum(max(b[i] - hole[i + 3], hole[i] - b[i + 3], Q(0)) ** 2
                                 for i in range(3)) for b in cells)
    return {'scope': result['scope'], 'status': 'PASS' if separation_squared > 0 else 'UNKNOWN',
            'reason': 'STRICTLY_SEPARATED_FROM_ALL_MATERIAL_CELLS' if separation_squared > 0 else 'TOUCHING_OR_OVERLAPPING_MATERIAL',
            'minimum_squared_separation_mm2': str(separation_squared),
            'native_brep_correspondence': 'UNKNOWN'}


def enclose(data, step, claimed_max_coordinate_error=None):
    """Outward coordinate rounding; recompute error, never trust a declaration."""
    result = verify_boundary(data)
    step = rational(step)
    if step <= 0:
        raise ValueError('POSITIVE_ROUNDING_STEP')
    output, error = [], Q(0)
    for raw in result['material_outer_cells']:
        b = box(raw)
        lo = [(b[i] // step) * step for i in range(3)]
        hi = [-((-b[i + 3]) // step) * step for i in range(3)]
        error = max(error, *(b[i] - lo[i] for i in range(3)), *(hi[i] - b[i + 3] for i in range(3)))
        output.append(list(map(str, lo + hi)))
    if claimed_max_coordinate_error is not None and rational(claimed_max_coordinate_error) < error:
        raise ValueError('UNDERSTATED_ROUNDING_ERROR')
    return {'scope': result['scope'], 'outer_cells': output,
            'max_coordinate_error_mm': str(error), 'rounding': 'floor minima / ceil maxima',
            'native_brep_correspondence': 'UNKNOWN'}


def pair_relation(first, second):
    """Exact model relation, not a collision conclusion about enclosed CAD."""
    a, b = verify_boundary(first), verify_boundary(second)
    aa, bb = [box(x) for x in a['material_outer_cells']], [box(x) for x in b['material_outer_cells']]
    penetration = any(all(min(x[i + 3], y[i + 3]) > max(x[i], y[i]) for i in range(3)) for x in aa for y in bb)
    sq = min(sum(max(x[i] - y[i + 3], y[i] - x[i + 3], Q(0)) ** 2 for i in range(3)) for x in aa for y in bb)
    return {'scope': 'exact rational model only; enclosure overlap is not CAD collision proof',
            'relation': 'PENETRATION' if penetration else 'CONTACT' if sq == 0 else 'SEPARATE',
            'minimum_squared_distance_mm2': str(sq), 'cad_status': 'UNKNOWN'}
