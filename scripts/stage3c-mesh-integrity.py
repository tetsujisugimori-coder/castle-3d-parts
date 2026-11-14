"""Geometric triangle comparison, allowing glTF vertex splits and reordering."""
from collections import Counter, defaultdict
from itertools import product
import math


def compare_mesh(expected_vertices, expected_faces, actual_vertices, actual_faces,
                 tolerance=1e-5):
    assert isinstance(tolerance,(int,float)) and not isinstance(tolerance,bool)
    assert math.isfinite(tolerance) and 0<tolerance<=1e-5, 'mesh tolerance'
    def vertices(values):
        assert isinstance(values,(list,tuple)) and values, 'missing vertices'
        for v in values:
            assert len(v)==3 and all(isinstance(x,(int,float)) and not isinstance(x,bool)
                                    and math.isfinite(x) for x in v), 'vertex coordinates'
        return [tuple(v) for v in values]
    expected=vertices(expected_vertices);actual=vertices(actual_vertices)
    # Seams can contain the same CAD point with double-rounding noise. glTF
    # float32 merges these. Weld only to a fixed representative, never by an
    # unbounded chain of neighbours, at <=1nm and far below the fit tolerance.
    weld=min(1e-9,tolerance/1000)
    unique=[];exact={};weld_cells=defaultdict(list);expected_map=[];max_weld=0.0
    def bucket(point,size):return tuple(math.floor(x/size) for x in point)
    offsets=list(product((-1,0,1),repeat=3))
    for point in expected:
        if point in exact:
            expected_map.append(exact[point]);continue
        here=bucket(point,weld)
        candidates=[i for offset in offsets
                    for i in weld_cells.get(tuple(a+b for a,b in zip(here,offset)),())]
        distances=[(sum((a-b)**2 for a,b in zip(point,unique[i])),i) for i in candidates]
        nearest=min(distances) if distances else (math.inf,-1)
        if nearest[0]<=weld*weld:
            index=nearest[1];max_weld=max(max_weld,math.sqrt(nearest[0]))
        else:
            index=len(unique);unique.append(point);weld_cells[here].append(index)
        exact[point]=index;expected_map.append(index)
    def cell(point):return bucket(point,tolerance)
    cells=defaultdict(list)
    for i,p in enumerate(unique):cells[cell(p)].append(i)
    mapping=[];maximum=0.0
    for point in actual:
        here=cell(point)
        candidates=[i for offset in offsets
                    for i in cells.get(tuple(a+b for a,b in zip(here,offset)),())]
        assert candidates, 'unexpected mesh vertex'
        distances=[(sum((a-b)**2 for a,b in zip(point,unique[i])),i) for i in candidates]
        distance,index=min(distances)
        assert distance<=tolerance*tolerance, 'mesh vertex moved'
        mapping.append(index);maximum=max(maximum,math.sqrt(distance))
    assert set(mapping)==set(range(len(unique))), 'source vertex missing'
    def triangles(faces, remap):
        assert isinstance(faces,(list,tuple)) and faces, 'missing triangle faces'
        keys=[]
        for f in faces:
            assert len(f)==3 and all(isinstance(i,int) and not isinstance(i,bool)
                                    and 0<=i<len(remap) for i in f), 'triangle indices'
            a,b,c=(remap[i] for i in f)
            assert len({a,b,c})==3, 'degenerate triangle'
            # Cyclic index rotations are equivalent; reversed winding is not.
            keys.append(min((a,b,c),(b,c,a),(c,a,b)))
        return Counter(keys)
    expected_triangles=triangles(expected_faces,expected_map)
    actual_triangles=triangles(actual_faces,mapping)
    assert expected_triangles==actual_triangles, 'triangle coverage/winding mismatch'
    return {'status':'PASS','unique_vertices':len(unique),'actual_vertices':len(actual),
            'triangles':sum(expected_triangles.values()),'maximum_vertex_error_m':maximum,
            'tolerance_m':tolerance,'vertex_splits_and_reordering_allowed':True,
            'source_exact_unique_vertices':len(exact),'source_weld_tolerance_m':weld,
            'maximum_source_weld_distance_m':max_weld}
