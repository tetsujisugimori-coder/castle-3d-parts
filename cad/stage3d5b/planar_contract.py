"""Exact conditional theorem for a restricted rectilinear boundary snapshot.

Input: schema ``rectilinear-boundary-v1``, unit ``m``, faces containing an id,
surface ``Plane``, axis 0/1/2, rational coordinate, outward normal_sign +/-1,
and wires. A wire has id, role outer/inner, curve_type ``Line`` and cyclic
vertices [x,y,z] (without repeating the first vertex). Integers and rational
strings are exact mathematical values; floats are rejected, not rounded.

All projected segments must be axis aligned, nonzero, simple and disjoint.
There is exactly one outer loop, with inner loops strictly inside it. Loops
are oriented in cyclic projected axes ((axis+1)%3,(axis+2)%3): outer signed
area has normal_sign; inner signed area has its opposite. An atomic grid is
derived from ALL vertex coordinates. Polygon winding is constant on each open
atomic rectangle, since every segment lies on grid lines. Thus evaluation at
its exact midpoint is a symbolic arrangement classification, not empirical
finite-point evidence about an arbitrary continuous BRep.

X-plane signed jumps derive occupancy from exterior zero. Every Y/Z jump and
all boundary patches must agree. Edge/vertex links enforce a connected closed
embedded 2-manifold, and occupied cells must be face connected. Internal sealed
cavities with disconnected boundary components are outside this shape class.
The resulting material
is the finite union of CLOSED occupied cells. Its complement is OPEN void;
boundary points belong to material. This proves a theorem about supplied exact
polygons, not extraction correctness, BRep trim equivalence, Location semantics
or a real-number enclosure. No input flag can promote real_brep UNKNOWN.
"""
from collections import Counter, defaultdict, deque
from fractions import Fraction
from itertools import product


def q(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        raise ValueError('exact-rational-required')
    return Fraction(value)


def _sign(x):
    return (x > 0) - (x < 0)


def _between(x, a, b):
    return min(a, b) <= x <= max(a, b)


def _intersect(a, b, c, d):
    """Inclusive intersection of axis-aligned 2D segments."""
    if a[0] == b[0] and c[0] == d[0]:
        return a[0] == c[0] and max(min(a[1], b[1]), min(c[1], d[1])) <= min(max(a[1], b[1]), max(c[1], d[1]))
    if a[1] == b[1] and c[1] == d[1]:
        return a[1] == c[1] and max(min(a[0], b[0]), min(c[0], d[0])) <= min(max(a[0], b[0]), max(c[0], d[0]))
    if a[1] == b[1]:
        a, b, c, d = c, d, a, b
    return _between(a[0], c[0], d[0]) and _between(c[1], a[1], b[1])


def _segments(loop):
    return list(zip(loop, loop[1:] + loop[:1]))


def _winding(loop, p):
    # Standard exact horizontal-ray signed winding. Callers exclude boundaries.
    x, y = p
    total = 0
    for a, b in _segments(loop):
        cross = (b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])
        if a[1] <= y < b[1] and cross > 0:
            total += 1
        elif b[1] <= y < a[1] and cross < 0:
            total -= 1
    return total


def _loop(points):
    if len(points) < 4 or len(set(points)) != len(points):
        raise ValueError('degenerate-or-repeated-wire-vertex')
    segs = _segments(points)
    for a, b in segs:
        if sum(x != y for x, y in zip(a, b)) != 1:
            raise ValueError('unsupported-nonrectilinear-or-zero-edge')
    # Adjacent collinear reversals overlap; same-direction redundant vertices
    # are allowed because native trim splits must not be silently dropped.
    for i, (a, b) in enumerate(segs):
        c = segs[(i + 1) % len(segs)][1]
        if ((a[0] == b[0] == c[0] and (b[1]-a[1])*(c[1]-b[1]) <= 0) or
                (a[1] == b[1] == c[1] and (b[0]-a[0])*(c[0]-b[0]) <= 0)):
            raise ValueError('adjacent-wire-backtracking')
        for j, (c, d) in enumerate(segs):
            if j <= i or j == i + 1 or (i == 0 and j == len(segs)-1):
                continue
            if _intersect(a, b, c, d):
                raise ValueError('self-intersecting-wire')
    area2 = sum(a[0]*b[1] - a[1]*b[0] for a, b in segs)
    if not area2:
        raise ValueError('zero-area-wire')
    return _sign(area2)


def _parse(d):
    if d['schema'] != 'rectilinear-boundary-v1' or d['unit'] != 'm':
        raise ValueError('schema-or-unit')
    faces = d['faces']
    if not isinstance(faces, list) or not faces:
        raise ValueError('missing-face-inventory')
    ids, wires_seen, parsed = set(), set(), []
    grid = [set(), set(), set()]
    for face in faces:
        fid = face['id']
        if not isinstance(fid, str) or not fid or fid in ids:
            raise ValueError('face-identity')
        ids.add(fid)
        axis, sign = face['axis'], face['normal_sign']
        if type(axis) is not int or axis not in (0, 1, 2) or type(sign) is not int or sign not in (-1, 1):
            raise ValueError('face-axis-or-orientation')
        if face['surface'] != 'Plane':
            raise ValueError('unsupported-surface')
        coordinate = q(face['coordinate'])
        uv = ((axis+1) % 3, (axis+2) % 3)
        loops, roles = [], []
        for wire in face['wires']:
            wid = wire['id']
            if not isinstance(wid, str) or not wid or wid in wires_seen:
                raise ValueError('wire-identity')
            wires_seen.add(wid)
            if wire['curve_type'] != 'Line':
                raise ValueError('unsupported-trim-curve')
            vertices = [tuple(map(q, v)) for v in wire['vertices']]
            if any(len(v) != 3 or v[axis] != coordinate for v in vertices):
                raise ValueError('vertex-plane-mismatch')
            loop = [tuple(v[k] for k in uv) for v in vertices]
            direction = _loop(loop)
            role = wire['role']
            if role not in ('outer', 'inner') or direction != sign * (1 if role == 'outer' else -1):
                raise ValueError('wire-role-or-orientation')
            loops.append(loop); roles.append(role)
            for v in vertices:
                for k in range(3):
                    grid[k].add(v[k])
        if roles.count('outer') != 1:
            raise ValueError('exactly-one-outer-trim-required')
        outer = loops[roles.index('outer')]
        for i, loop in enumerate(loops):
            for other in loops[i+1:]:
                if any(_intersect(a,b,c,e) for a,b in _segments(loop) for c,e in _segments(other)):
                    raise ValueError('touching-or-crossing-trims')
            if roles[i] == 'inner' and not _winding(outer, loop[0]):
                raise ValueError('inner-trim-outside-outer')
        # Nested/overlapping inner loops are not part of this shape class.
        holes = [loops[i] for i,r in enumerate(roles) if r == 'inner']
        if any(_winding(a, b[0]) or _winding(b, a[0]) for i,a in enumerate(holes) for b in holes[i+1:]):
            raise ValueError('nested-inner-trims')
        parsed.append((fid, axis, coordinate, sign, loops))
    if any(len(g) < 2 for g in grid):
        raise ValueError('zero-dimensional-boundary')
    return parsed, [sorted(g) for g in grid]


def _patches(parsed, grid):
    patches, owners = {}, defaultdict(list)
    for fid, axis, coordinate, sign, loops in parsed:
        uv = ((axis+1) % 3, (axis+2) % 3)
        k = grid[axis].index(coordinate)
        count = 0
        for i,j in product(range(len(grid[uv[0]])-1), range(len(grid[uv[1]])-1)):
            p = ((grid[uv[0]][i]+grid[uv[0]][i+1])/2, (grid[uv[1]][j]+grid[uv[1]][j+1])/2)
            w = sum(_winding(loop,p) for loop in loops)
            if not w:
                continue
            if w != sign:
                raise ValueError('polygon-cover-multiplicity-or-orientation')
            index = [None]*3; index[axis] = k; index[uv[0]] = i; index[uv[1]] = j
            key = (axis, *index)
            if key in patches:
                raise ValueError('duplicate-or-overlapping-face-patch')
            patches[key] = sign; owners[fid].append(key); count += 1
        if not count:
            raise ValueError('empty-face-trim')
    return patches, owners


def _occupancy(patches, grid):
    n = [len(g)-1 for g in grid]
    occupied = set()
    for j,k in product(range(n[1]),range(n[2])):
        value = 0
        for i in range(n[0]+1):
            value -= patches.get((0,i,j,k),0)
            if value not in (0,1):
                raise ValueError('negative-or-multiple-material-winding')
            if i < n[0] and value:
                occupied.add((i,j,k))
        if value:
            raise ValueError('open-boundary-x-exterior')
    if not occupied:
        raise ValueError('empty-material')
    expected = {}
    for cell in occupied:
        for a in range(3):
            for step in (-1,1):
                neighbor = list(cell); neighbor[a] += step
                if tuple(neighbor) not in occupied:
                    ix = list(cell); ix[a] += (step == 1)
                    expected[(a,*ix)] = step
    if patches != expected:
        raise ValueError('incomplete-or-inconsistent-all-axis-boundary')
    seen = {next(iter(occupied))}; todo = list(seen)
    while todo:
        cell = todo.pop()
        for a,step in product(range(3),(-1,1)):
            v = list(cell); v[a] += step; v = tuple(v)
            if v in occupied and v not in seen:
                seen.add(v); todo.append(v)
    if seen != occupied:
        raise ValueError('multiple-disconnected-material-components')
    return occupied


def _manifold(patches):
    edges = Counter(); links = defaultdict(list); edge_patches = defaultdict(list)
    for key in patches:
        axis, *ix = key; u,v = (axis+1)%3,(axis+2)%3
        corners = []
        for du,dv in ((0,0),(1,0),(1,1),(0,1)):
            c = ix.copy();c[u] += du;c[v] += dv;corners.append(tuple(c))
        for i,c in enumerate(corners):
            a,b = corners[i-1],corners[(i+1)%4]
            edge = tuple(sorted((c,b)))
            edges[edge] += 1; edge_patches[edge].append(key)
            rays = []
            for other in (a,b):
                k = next(k for k in range(3) if other[k] != c[k])
                rays.append((k,_sign(other[k]-c[k])))
            links[c].append(tuple(rays))
    if any(v != 2 for v in edges.values()):
        raise ValueError('nonmanifold-boundary-edge')
    adjacent = defaultdict(set)
    for a,b in edge_patches.values():
        adjacent[a].add(b);adjacent[b].add(a)
    reached = {next(iter(patches))}; todo = list(reached)
    while todo:
        for key in adjacent[todo.pop()]:
            if key not in reached:reached.add(key);todo.append(key)
    if len(reached) != len(patches):
        raise ValueError('disconnected-boundary-components-unsupported')
    for arcs in links.values():
        graph = defaultdict(list)
        for a,b in arcs:
            graph[a].append(b);graph[b].append(a)
        if any(len(ns) != 2 for ns in graph.values()):
            raise ValueError('nonmanifold-boundary-vertex-degree')
        seen={next(iter(graph))};todo=list(seen)
        while todo:
            for n in graph[todo.pop()]:
                if n not in seen:seen.add(n);todo.append(n)
        if len(seen) != len(graph):
            raise ValueError('nonmanifold-boundary-vertex-link')


def _box(cell, grid):
    return tuple(grid[a][cell[a]] for a in range(3)) + tuple(grid[a][cell[a]+1] for a in range(3))


def _analyze(d):
    parsed, grid = _parse(d)
    patches, owners = _patches(parsed, grid)
    occupied = _occupancy(patches,grid)
    _manifold(patches)
    return grid, occupied, patches, owners


def verify_boundary(d):
    """Return a conditional exact-set certificate; never a real BRep PASS."""
    try:
        grid, occupied, patches, owners = _analyze(d)
        return {'status':'PASS','scope':'exact supplied rectilinear boundary theorem only',
                'real_brep':'UNKNOWN','material_convention':'closed union of occupied cells; void is open complement',
                'face_count':len(owners),'atomic_boundary_patch_count':len(patches),
                'atomic_material_cell_count':len(occupied),
                'grid_m':[[str(v) for v in g] for g in grid],
                'exact_material_cells_m':[[str(v) for v in _box(c,grid)] for c in sorted(occupied)],
                'face_patch_inventory':{fid:[list(k) for k in ks] for fid,ks in owners.items()},
                'unproved_real_premises':['all-BRep-boundary-to-polygon-equivalence','certified-extraction-enclosure',
                                         'trim-and-orientation-semantics','serialized-to-world-transform-equivalence']}
    except (KeyError, ValueError, TypeError, IndexError, ZeroDivisionError) as e:
        return {'status':'FAIL','reason':str(e),'real_brep':'UNKNOWN'}


def _boxes(raw):
    boxes = [tuple(map(q,b)) for b in raw]
    if not boxes or any(len(b)!=6 or any(b[a]>=b[a+3] for a in range(3)) for b in boxes):
        raise ValueError('positive-closed-boxes-required')
    return boxes


def _contains_point(box, point):
    return all(box[a] <= point[a] <= box[a+3] for a in range(3))


def compare_cells(boundary, model_boxes):
    """Prove A subset M for exact boundary A and CLOSED model-box union M.

    The common coordinate arrangement covers every source interior cell;
    closure then proves inclusion of all boundary points in finite closed M.
    A violation is a mathematical containment FAIL, not proven real collision.
    """
    proof=verify_boundary(boundary)
    if proof['status']!='PASS':return proof
    try:
        source=_boxes(proof['exact_material_cells_m']);model=_boxes(model_boxes)
        grid=[sorted({b[a] for b in source+model}|{b[a+3] for b in source+model}) for a in range(3)]
        tested=0
        for ix in product(*(range(len(g)-1) for g in grid)):
            p=tuple((grid[a][ix[a]]+grid[a][ix[a]+1])/2 for a in range(3))
            if any(_contains_point(b,p) for b in source):
                tested+=1
                if not any(_contains_point(b,p) for b in model):
                    return {'status':'FAIL','reason':'mathematical-material-not-covered','witness_open_cell_midpoint_m':list(map(str,p)),'real_brep':'UNKNOWN'}
        return {'status':'PASS','scope':'exact conditional material A subset closed box-union M',
                'real_brep':'UNKNOWN','source_atomic_subcells_checked':tested,'boundary_proof':proof}
    except (ValueError,TypeError,IndexError,ZeroDivisionError) as e:
        return {'status':'FAIL','reason':str(e),'real_brep':'UNKNOWN'}


def compare_material(source_boundary, model_boundary):
    model=verify_boundary(model_boundary)
    return compare_cells(source_boundary,model['exact_material_cells_m']) if model['status']=='PASS' else model


def certify_void_box(boundary, box):
    """Closed query box wholly in OPEN complement: strict separation needed."""
    proof=verify_boundary(boundary)
    if proof['status']!='PASS':return proof
    try:
        query=_boxes([box])[0]
        material=_boxes(proof['exact_material_cells_m'])
        for b in material:
            if not any(query[a+3] < b[a] or b[a+3] < query[a] for a in range(3)):
                return {'status':'FAIL','reason':'closed-query-touches-or-intersects-material','real_brep':'UNKNOWN'}
        return {'status':'PASS','scope':'closed query subset exact OPEN void only','real_brep':'UNKNOWN'}
    except (ValueError,TypeError,IndexError,ZeroDivisionError) as e:
        return {'status':'FAIL','reason':str(e),'real_brep':'UNKNOWN'}


def classify_point(boundary, point):
    """Exact membership in closed material; every material wall is MATERIAL."""
    proof=verify_boundary(boundary)
    if proof['status']!='PASS':return proof
    try:
        if not isinstance(point,(list,tuple)) or len(point)!=3:
            raise ValueError('three-exact-point-coordinates-required')
        p=tuple(map(q,point))
        inside=any(_contains_point(b,p) for b in _boxes(proof['exact_material_cells_m']))
        return {'status':'PASS','classification':'MATERIAL' if inside else 'VOID',
                'scope':'exact supplied-set membership; boundary belongs to material','real_brep':'UNKNOWN'}
    except (ValueError,TypeError,IndexError,ZeroDivisionError) as e:
        return {'status':'FAIL','reason':str(e),'real_brep':'UNKNOWN'}
