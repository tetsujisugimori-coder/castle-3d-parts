"""Exact affine checks on *exposed* Plane/Line coefficients, not all OCCT real sets."""
from collections import Counter
from fractions import Fraction as Q


def vector(v):
    return tuple(Q(x) for x in v)


def vector2(v):
    return Q(v.x), Q(v.y)


def add(x, y):
    return tuple(a + b for a, b in zip(x, y, strict=True))


def scale(k, v):
    return tuple(k * x for x in v)


def affine_link(plane, uv, curve, uv_range, curve_range):
    """All t, by two exact coefficients; never infer from sampled points."""
    origin, u, v = plane
    offset, rate = uv
    if (uv_range != curve_range or len(uv_range) != 2 or
            uv_range[0] >= uv_range[1] or not any(rate) or not any(curve[1])):
        return False
    return (add(origin, add(scale(offset[0], u), scale(offset[1], v))),
            add(scale(rate[0], u), scale(rate[1], v))) == curve


def directed_loop(segments):
    """Find the cycle in native oriented uses, not inferred endpoint order."""
    starts = {a: b for a, b in segments}
    if len(starts) != len(segments) or not starts:
        raise ValueError('NON_UNIQUE_OR_EMPTY_ORIENTED_START')
    out = [segments[0][0]]
    for _ in range(len(segments) - 1):
        nxt = starts.get(out[-1])
        if nxt is None or nxt in out:
            raise ValueError('TRIM_NOT_ONE_ORIENTED_LOOP')
        out.append(nxt)
    if starts.get(out[-1]) != out[0]:
        raise ValueError('TRIM_NOT_CLOSED')
    return out


def crossing_count(poly, p):
    """Exact odd-even check at a probe point off the polygon boundary."""
    u, v = p
    return sum((a[1] > v) != (b[1] > v) and
               u < a[0] + (v-a[1]) * (b[0]-a[0]) / (b[1]-a[1])
               for a, b in zip(poly, poly[1:] + poly[:1]))


def check_planar_trim(outer, holes):
    # A closed polygon cycle alone need not be simple or properly nested.
    def segments(poly):
        return list(zip(poly, poly[1:]+poly[:1]))

    def intersects(s, t):
        return all(max(min(s[0][k],s[1][k]),min(t[0][k],t[1][k])) <=
                   min(max(s[0][k],s[1][k]),max(t[0][k],t[1][k])) for k in (0,1))

    loops=[outer,*holes]
    for i, poly in enumerate(loops):
        edges=segments(poly)
        for a,x in enumerate(edges):
            for b,y in enumerate(edges[:a]):
                if a-b in (1,len(edges)-1):
                    # Consecutive reversed collinear edges overlap.
                    if sum(min(max(x[0][k],x[1][k]),max(y[0][k],y[1][k])) >
                           max(min(x[0][k],x[1][k]),min(y[0][k],y[1][k])) for k in (0,1)):
                        raise ValueError('ADJACENT_TRIM_OVERLAP')
                elif intersects(x,y):
                    raise ValueError('SELF_INTERSECTING_TRIM')
            if any(intersects(x,y) for other in loops[:i] for y in segments(other)):
                raise ValueError('INTERSECTING_TRIM_LOOPS')
        if i and (crossing_count(outer,poly[0])%2!=1 or any(
                crossing_count(other,poly[0])%2 or crossing_count(poly,other[0])%2
                for other in loops[1:i])):
            raise ValueError('HOLE_NOT_STRICTLY_NESTED_OR_DISJOINT')


def material_side(plane, normal, loops, boxes):
    """Check represented candidate on every in-trim open grid cell's two sides."""
    o, u, v = plane
    # Supported fixed scope: unit Cartesian signed frame only.
    axes = []
    for basis in (u, v, normal):
        nz = [i for i, x in enumerate(basis) if x]
        if len(nz) != 1 or abs(basis[nz[0]]) != 1:
            raise ValueError('NON_CARTESIAN_FRAME')
        axes.append(nz[0])
    if len(set(axes)) != 3:
        raise ValueError('FRAME_AXES_NOT_DISTINCT')
    cols = []
    for axis, basis, k in zip(axes[:2], (u, v), (0, 1)):
        coords = {p[k] for poly in loops for p in poly}
        coords.update((b[j]-o[axis])/basis[axis] for b in boxes for j in (axis, axis+3))
        cols.append(sorted(coords))
    axis = axes[2]
    gaps = [abs(b[j]-o[axis]) for b in boxes for j in (axis, axis+3) if b[j] != o[axis]]
    eps = min(gaps)/2 if gaps else Q(1)

    def inside(p):
        return any(all(b[k] < p[k] < b[k+3] for k in range(3)) for b in boxes)

    checks = []
    for a,b in zip(cols[0], cols[0][1:]):
        for c,d in zip(cols[1], cols[1][1:]):
            x,y = (a+b)/2, (c+d)/2
            if sum(crossing_count(poly, (x,y)) for poly in loops) % 2 == 0:
                continue
            p = add(o, add(scale(x,u), scale(y,v)))
            lower = inside(add(p,scale(-eps,normal)))
            upper = inside(add(p,scale(eps,normal)))
            checks.append({'uv_cell': [a,b,c,d], 'inward_candidate_material':lower,
                           'outward_candidate_material':upper})
    return {'status':'PASS' if checks and all(x['inward_candidate_material'] and
                    not x['outward_candidate_material'] for x in checks) else 'FAIL',
            'normal_probe_distance_mm':eps, 'open_cell_checks': checks}


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def orientation_sign(orientation):
    return {'Forward': 1, 'Reversed': -1}[orientation]


def placement(obj):
    m = obj.Placement.toMatrix()
    return [[Q(getattr(m, f'A{i}{j}')) for j in range(1,5)] for i in range(1,5)]


def observe(shape, boxes_mm, index_same):
    """Collect every face/wire/edge use at the caller's fixed read-only pose."""
    result = {'shape_location':placement(shape), 'faces':[], 'errors':[],
              'native_pcurve_storage_provenance':'UNKNOWN_API_MAY_PROJECT_PLANAR_CURVE',
              'coefficient_frame':'FreeCAD world-exposed Curve/Surface; placement recorded, not reapplied',
              'shells':[{'orientation':s.Orientation,'closed_observed':bool(s.isClosed())}
                        for s in shape.Shells],
              'native_material_outer':'UNKNOWN', 'native_void_inner':'UNKNOWN'}
    boxes = [vector(b) for b in boxes_mm]
    all_edges = shape.Edges
    shells = shape.Shells
    result['solid_orientations_observed']=[s.Orientation for s in shape.Solids]
    if len(shells)!=1 or len(shape.Solids)!=1 or not shells[0].isClosed():
        result['errors'].append({'reason':'UNSUPPORTED_SHELL_OR_SOLID_INVENTORY'})
    else:
        expected=Counter((index_same(f,shape.Faces),f.Orientation) for f in shells[0].Faces)
        if expected!=Counter((i,f.Orientation) for i,f in enumerate(shape.Faces)):
            result['errors'].append({'reason':'SHELL_FACE_OCCURRENCE_MISMATCH'})
    census = Counter()
    directed_census = Counter()
    for fi, face in enumerate(shape.Faces):
        item = {'face':fi,'orientation':face.Orientation,'location':placement(face),'wires':[]}
        result['faces'].append(item)
        try:
            surface=face.Surface
            if type(surface).__name__ != 'Plane':
                raise ValueError('UNSUPPORTED_SURFACE')
            plane=vector(surface.Position),vector(surface.getDN(0,0,1,0)),vector(surface.getDN(0,0,0,1))
            normal=scale(orientation_sign(face.Orientation),cross(plane[1],plane[2]))
            item.update(plane=plane,normal=normal,uv_bounds=vector(face.ParameterRange))
            if not any(normal) or normal != vector(face.normalAt(0,0)):
                raise ValueError('ORIENTED_NORMAL_MISMATCH')
            if plane[0] != vector(face.valueAt(0,0)):
                raise ValueError('EXPOSED_SURFACE_LOCATION_MISMATCH')
            loops=[]
            face_edges=[]
            for wi, wire in enumerate(face.Wires):
                row={'wire':wi,'role':'outer' if wire.isSame(face.OuterWire) else 'inner',
                     'orientation':wire.Orientation,'location':placement(wire),'uses':[]}
                item['wires'].append(row)
                segments = []
                for ei, edge in enumerate(wire.OrderedEdges):
                    identity=index_same(edge,all_edges);census[identity]+=1;face_edges.append(identity)
                    use={'use':ei,'edge':identity,'orientation':edge.Orientation,'location':placement(edge)}
                    row['uses'].append(use)
                    pc, a, b = face.curveOnSurface(edge)
                    c3 = edge.Curve
                    use.update(pcurve_type=type(pc).__name__,curve_type=type(c3).__name__)
                    if type(pc).__name__ not in ('Line2d','Line2dSegment') or type(c3).__name__ != 'Line' or edge.Degenerated:
                        raise ValueError('UNSUPPORTED_CURVE_USE')
                    uvrange, c3range = vector((a,b)),vector(edge.ParameterRange)
                    if type(pc).__name__=='Line2d':
                        uv=vector2(pc.Location),vector2(pc.Direction)
                    else:
                        intrinsic=vector((pc.FirstParameter,pc.LastParameter))
                        if intrinsic != uvrange or intrinsic[0]>=intrinsic[1]:
                            raise ValueError('SEGMENT_RANGE_MISMATCH')
                        ends=(vector2(pc.StartPoint),vector2(pc.EndPoint))
                        rate=scale(1/(intrinsic[1]-intrinsic[0]),add(ends[1],scale(-1,ends[0])))
                        uv=add(ends[0],scale(-intrinsic[0],rate)),rate
                        use.update(segment_intrinsic_range=intrinsic,segment_native_endpoints=ends)
                    curve=vector(c3.Location),vector(c3.Direction)
                    use.update(pcurve=uv,curve=curve,pcurve_range=uvrange,curve_range=c3range)
                    if not affine_link(plane,uv,curve,uvrange,c3range):
                        raise ValueError('AFFINE_LINK_MISMATCH')
                    end3 = [add(curve[0],scale(t,curve[1])) for t in c3range]
                    if end3 != [vector(edge.valueAt(float(t))) for t in c3range] or set(end3) != {vector(v.Point) for v in edge.Vertexes}:
                        raise ValueError('EDGE_LOCATION_OR_VERTEX_MISMATCH')
                    uv_end=[add(uv[0],scale(t,uv[1])) for t in uvrange]
                    if uv_end != [vector2(pc.value(float(t))) for t in uvrange]:
                        raise ValueError('PCURVE_PARAMETER_ENDPOINT_MISMATCH')
                    if sum(x!=y for x,y in zip(*uv_end))!=1:
                        raise ValueError('NON_RECTILINEAR_TRIM_SEGMENT')
                    if orientation_sign(edge.Orientation)<0:
                        uv_end.reverse();end3.reverse()
                    directed_census[identity,tuple(end3)]+=1
                    segments.append(tuple(uv_end));use.update(directed_uv=uv_end,directed_3d=end3, represented_affine_link='PASS')
                poly = directed_loop(segments)
                area2=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))
                row.update(directed_loop=poly,signed_area2_mm2=area2)
                # OrderedEdges retains on-face occurrence directions; the
                # surface's winding is opposed by an inner wire.
                wanted=orientation_sign(face.Orientation)*(1 if row['role']=='outer' else -1)
                if not area2 or (area2>0)!=(wanted>0):
                    raise ValueError('TRIM_WINDING_MISMATCH')
                loops.append(poly)
            if (sum(x['role']=='outer' for x in item['wires'])!=1 or
                    Counter(face_edges)!=Counter(index_same(e,all_edges) for e in face.Edges)):
                raise ValueError('FACE_TRIM_COVERAGE')
            check_planar_trim(next(x['directed_loop'] for x in item['wires'] if x['role']=='outer'),
                              [x['directed_loop'] for x in item['wires'] if x['role']=='inner'])
            item['represented_trim_polygon']='PASS'
            item['represented_material_side']=material_side(plane,normal,loops,boxes)
            if item['represented_material_side']['status']!='PASS':
                raise ValueError('CANDIDATE_MATERIAL_SIDE_MISMATCH')
        except (AttributeError, TypeError, ValueError, KeyError, RuntimeError, IndexError) as exc:
            item['status']='INCOMPLETE_OR_MISMATCH'
            result['errors'].append({'face':fi,'reason':str(exc)})
        else:
            item['status']='PASS'
    result['edge_use_count']=sum(census.values())
    if set(census)!=set(range(len(all_edges))) or any(n!=2 for n in census.values()):
        result['errors'].append({'reason':'GLOBAL_EDGE_USE_COVERAGE'})
    if any(n!=1 or directed_census.get((i,(b,a)))!=1 for (i,(a,b)),n in directed_census.items()):
        result['errors'].append({'reason':'GLOBAL_DIRECTED_EDGE_PAIR_MISMATCH'})
    result['status']='PASS' if result['faces'] and not result['errors'] else 'INCOMPLETE_OR_MISMATCH'
    return result
