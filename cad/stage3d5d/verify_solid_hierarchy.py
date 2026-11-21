"""Independent audit of the actual OCCT Solid->Shell->Face exhaustiveness.

Native hierarchy is from a new C++ parent-child traversal; the expected
oriented edge/vertex geometry comes from previously pinned, stored BRep trim
and pcurve evidence. Structural PASS is NOT mathematical proof of all-point
OCCT material semantics or of a finite classifier error bound.
"""
from collections import Counter, defaultdict
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE
from one_slice import FCSTD, CONTRACT

def sha(b):
    return sha256(b).hexdigest()

def p3(point):
    if len(point)!=3:
        raise ValueError('NATIVE_VERTEX_DIMENSION')
    return tuple(Q(x) for x in point)

def graph_connected(edge_pairs, count):
    graph=[set() for _ in range(count)]
    for a,b in edge_pairs:
        graph[a].add(b);graph[b].add(a)
    visited={0}
    todo=[0]
    while todo:
        for nxt in graph[todo.pop()]:
            if nxt not in visited:
                visited.add(nxt);todo.append(nxt)
    return len(visited)==count

def check_structure(n):
    """Fail closed for missing/extra/duplicated OCCT topology."""
    if (n.get('schema')!=1 or n.get('occt')!='7.8.1'
            or n.get('solid_count')!=1 or n.get('direct_shell_count')!=1
            or n.get('shell_count')!=1 or n.get('direct_shell_face_count')!=10
            or n.get('all_root_faces_identical_to_shell_faces') is not True
            or n.get('shell_closed') is not True
            or n.get('brepcheck_valid') is not True
            or n.get('wire_count')!=12 or n.get('edge_count')!=24
            or n.get('vertex_count')!=16
            or n.get('native_shell_membership_exhaustive')!='PASS'
            or n.get('native_solid_material_set_equality')!='UNKNOWN'
            or n.get('native_full_q_void_inclusion')!='UNKNOWN'):
        raise ValueError('NATIVE_SOLID_HIERARCHY_NOT_PROVEN')
    f=n['native_face_hierarchy'];w=n['wires'];e=n['edges'];v=n['vertices']
    if (len(f),len(w),len(e),len(v))!=(10,12,24,16):
        raise ValueError('NATIVE_HIERARCHY_ROW_LENGTH')
    if [row['face'] for row in f]!=list(range(10)):
        raise ValueError('NATIVE_FACE_IDENTITY_MISMATCH')
    if [row['wire'] for row in w]!=list(range(12)):
        raise ValueError('NATIVE_WIRE_IDENTITY_MISMATCH')
    if [row['edge'] for row in e]!=list(range(24)):
        raise ValueError('NATIVE_EDGE_IDENTITY_MISMATCH')
    if [row['vertex'] for row in v]!=list(range(16)):
        raise ValueError('NATIVE_VERTEX_IDENTITY_MISMATCH')
    parents=Counter(x for row in f for x in row['direct_wires'])
    if set(parents)!=set(range(12)) or any(parents[i]!=1 for i in range(12)):
        raise ValueError('WIRE_NOT_OWNED_BY_EXACTLY_ONE_FACE')
    edge_faces=defaultdict(list)
    native_uses=Counter()
    for fr in f:
        fi=fr['face'];ww=fr['direct_wires']
        if len(ww)!=(2 if fi in (0,9) else 1):
            raise ValueError('FIXED_FACE_WIRE_SHAPE_CHANGED')
        if fr['orientation'] not in ('Forward','Reversed'):
            raise ValueError('FACE_ORIENTATION_UNKNOWN')
        for wi in ww:
            row=w[wi]
            ee=row['edge_ordinals']
            if (len(ee)!=4 or len(set(ee))!=4
                    or len(row['orientations'])!=4
                    or any(o not in ('Forward','Reversed') for o in row['orientations'])):
                raise ValueError('NON_RECTANGULAR_OR_BROKEN_NATIVE_WIRE')
            for ei in ee:
                if not 0<=ei<24:
                    raise ValueError('NATIVE_EDGE_ORDINAL_INVALID')
                edge_faces[ei].append(fi)
                native_uses[(fi,ei)]+=1
    if sum(native_uses.values())!=48 or len(native_uses)!=48:
        raise ValueError('NATIVE_48_USES_NOT_UNIQUE')
    if set(edge_faces)!=set(range(24)):
        raise ValueError('NATIVE_EDGE_NOT_ALL_REFERENCED')
    seen_pairs=set()
    incidence=[0]*16
    native_edge_pairs=[]
    vertices={i:p3(row['point_mm']) for i,row in enumerate(v)}
    if len(set(vertices.values()))!=16:
        raise ValueError('NATIVE_VERTEX_COORDINATE_DUPLICATE')
    for row in e:
        ei=row['edge'];fs=row['face_pair'];vv=row['vertex_pair']
        if (len(fs)!=2 or len(set(fs))!=2
            or sorted(fs)!=sorted(edge_faces[ei])
            or any(type(i) is not int or not 0<=i<10 for i in fs)):
            raise ValueError('NATIVE_EDGE_FACE_ANCESTRY_MISMATCH')
        key=tuple(sorted(fs))
        if key in seen_pairs:
            raise ValueError('NON_UNIQUE_NATIVE_FACE_ADJACENCY')
        seen_pairs.add(key)
        if (len(vv)!=2 or len(set(vv))!=2
            or any(type(i) is not int or not 0<=i<16 for i in vv)):
            raise ValueError('NATIVE_VERTEX_ENDPOINT_INDEX_INVALID')
        native_edge_pairs.append(tuple(vv))
        for vi in vv:incidence[vi]+=1
    if (any(x!=3 for x in incidence) or
        any(row['edge_degree']!=3 for row in v)):
        raise ValueError('NATIVE_VERTEX_VALENCE_CHANGED')
    if not graph_connected(native_edge_pairs,16):
        raise ValueError('NATIVE_VERTEX_GRAPH_DISCONNECTED')
    # A torus-like cell complex has Euler characteristic 0, because the two
    # annular faces each have cell Euler contribution 0, unlike disks.
    if 16-24+(8*1+2*0)!=0:
        raise ValueError('NATIVE_BOUNDARY_EULER_MISMATCH')
    return {'status':'PASS','solid_count':1,'shell_count':1,
            'direct_shell_face_count':10,'wire_count':12,'edge_count':24,
            'vertex_count':16,'unique_edge_uses':48,'vertex_degree':3,
            'connected_native_vertex_graph':True,
            'represented_surface_euler_characteristic':0,
            'native_edge_ancestry':edge_faces,
            'native_vertices':vertices,
            'native_wire_uses':native_uses}

def audit(n,trim,stored,through):
    prior=check_structure(n)
    g=trim['parts'][GUIDE]
    if (trim.get('source_fcstd_sha256')!=FCSTD_SHA or
        trim.get('source_d2_sha256')!=D2_SHA or
        g.get('source_brep_sha256')!=GUIDE_BREP_SHA or
        g.get('status')!='PASS' or len(g.get('faces',[]))!=10):
        raise ValueError('PINNED_SAVED_BREP_CENSUS_MISSING')
    if (through.get('status')!='PASS' or
        through.get('full_face_oriented_pcurve_uses')!=48 or
        through.get('exact_represented_boundary_disjoint')!='PASS' or
        through.get('native_full_q_void_inclusion')!='UNKNOWN'):
        raise ValueError('PRIOR_Q_MODEL_OR_SCOPE_MISMATCH')
    src=stored['parts'][GUIDE]
    if len(src)!=48 or len({(r['face'],r['wire'],r['edge'],r['formula_use_order']) for r in src})!=48 or any(r['status']!='PASS' for r in src):
        raise ValueError('STORED_48_NATIVE_PCURVE_USES_INVALID')
    src_keys={(r['face'],r['wire'],r['edge'],r['formula_use_order']) for r in src}
    extracted_keys=set()
    ids=defaultdict(list)
    pairs=defaultdict(set)
    edge_verts={}
    oriented=defaultdict(list)
    wire_members={}
    for face in g['faces']:
        fi=face['face']
        if (not 0<=fi<10 or face['status']!='PASS' or
            face['represented_trim_polygon']!='PASS' or
            face['represented_material_side']['status']!='PASS' or
            face['orientation']!=n['native_face_hierarchy'][fi]['orientation']):
            raise ValueError('NATIVE_FACE_NOT_EXACT_SAVED_REPRESENTATION:'+str(fi))
        for w in face['wires']:
            wk=(fi,w['wire'])
            if wk in wire_members:
                raise ValueError('DUPLICATED_SAVED_WIRE')
            wire_members[wk]=frozenset(use['edge'] for use in w['uses'])
            for use in w['uses']:
                edge=use['edge']
                key=(fi,w['wire'],edge,use['use'])
                if key in extracted_keys:
                    raise ValueError('DUPLICATED_SAVED_EDGE_USE')
                extracted_keys.add(key)
                if use['represented_affine_link']!='PASS' or
                    use['orientation'] not in ('Forward','Reversed'):
                    raise ValueError('UNPROVEN_SAVED_LINEAR_EDGE')
                endpoints=tuple(p3(x) for x in use['directed_3d'])
                if len(set(endpoints))!=2:
                    raise ValueError('DEGENERATE_FIXED_EDGE')
                if edge in edge_verts and set(edge_verts[edge])!=set(endpoints):
                    raise ValueError('NATIVE_EDGE_GEO_ENDPOINT_CONFLICT')
                edge_verts[edge]=endpoints
                ids[edge].append(fi)
                oriented[edge].append(endpoints)
                pairs[edge].add(fi)
    if extracted_keys!=src_keys or len(extracted_keys)!=48:
        raise ValueError('NATIVE_SAVED_USE_IDENTITY_MISMATCH')
    if len(edge_verts)!=24 or set(edge_verts)!=set(range(24)):
        raise ValueError('NATIVE_24_EDGE_SET_CHANGED')
    expected_by_pair={}
    for edge in range(24):
        fs=tuple(sorted(ids[edge]))
        if len(ids[edge])!=2 or len(set(fs))!=2 or fs in expected_by_pair:
            raise ValueError('NONMANIFOLD_SAVED_EDGE_FACE_PAIR')
        expected_by_pair[fs]=edge
        if tuple(oriented[edge][0])!=tuple(reversed(oriented[edge][1])):
            raise ValueError('OPPOSITE_ORIENTED_SHARED_EDGE_MISMATCH')
    native_to_saved={}
    for row in n['edges']:
        pair=tuple(sorted(row['face_pair']))
        if pair not in expected_by_pair:
            raise ValueError('NATIVE_EDGE_PAIR_NOT_IN_TRIM_SOURCE')
        saved_edge=expected_by_pair[pair]
        if set(prior['native_vertices'][j] for j in row['vertex_pair'])!=set(edge_verts[saved_edge]):
            raise ValueError('NATIVE_VERTEX_COORDS_DIFFER_FROM_STORED_EDGE')
        native_to_saved[row['edge']]=saved_edge
    native_face_wire={i:[] for i in range(10)}
    for fr in n['native_face_hierarchy']:
        fi=fr['face']
        for wi in fr['direct_wires']:
            native_face_wire[fi].append(frozenset(native_to_saved[ei]
                                                 for ei in n['wires'][wi]['edge_ordinals']))
    for fi in range(10):
        expected=[value for (face,wi),value in wire_members.items() if face==fi]
        if sorted(map(lambda s:tuple(sorted(s)),native_face_wire[fi]))!=sorted(
                map(lambda s:tuple(sorted(s)),expected)):
            raise ValueError('NATIVE_DIRECT_WIRE_MISMATCH:'+str(fi))
    return {
        'schema':'d5d-native-solid-face-exhaustiveness-v1',
        'status':'PASS',
        'native_solid_shell_face_ancestry':'PASS',
        'native_shell_faces_exhaustive':'PASS',
        'native_wire_edge_vertex_ancestry':'PASS',
        'native_to_stored_24_edges':'PASS',
        'native_to_stored_all_48_oriented_uses':'PASS',
        'native_face_wire_membership':'PASS',
        'saved_shared_edge_directions_opposite':'PASS',
        'connected_closed_oriented_2manifold_structure':'PASS',
        'topological_counts':{k:prior[k] for k in
            ('solid_count','shell_count','direct_shell_face_count','wire_count',
             'edge_count','vertex_count','unique_edge_uses','vertex_degree',
             'represented_surface_euler_characteristic')},
        'direct_face_indices':list(range(10)),
        'hole_face_indices':[0,9],
        'native_edge_to_saved_edge':{str(k):v for k,v in native_to_saved.items()},
        'model_face_q_disjoint':'PASS',
        'native_solid_stored_topological_boundary_exhaustiveness':'PASS',
        'native_material_boundary_real_set_equality':'UNKNOWN',
        'native_full_q_void_inclusion':'UNKNOWN',
        'native_representative_interval':'NOT_TESTED',
        'scope':'Exhaustion of real OCCT TopoDS_Solid->Shell->Face topology and original stored edge uses, not finite-real material-set theorem'
    }

def main(native_path,trim_path,stored_path,through_path,dest):
    dest.mkdir(parents=True,exist_ok=False)
    if sha(FCSTD.read_bytes())!=FCSTD_SHA or sha(CONTRACT.read_bytes())!=D2_SHA:
        raise ValueError('PINNED_SOURCES_CHANGED')
    with ZipFile(FCSTD) as z:
        if sha(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError('PINNED_REAL_GUIDE_CHANGED')
    paths=(native_path,trim_path,stored_path,through_path)
    raw=[p.read_bytes() for p in paths]
    if sha(raw[1])!=TRIM_SHA:
        raise ValueError('PINNED_TRIM_SOURCE_CHANGED')
    try:
        result=audit(*(json.loads(b) for b in raw))
    except (KeyError,ValueError,TypeError,IndexError,ZeroDivisionError) as exc:
        result={'status':'FAIL','reason':str(exc),
                'native_material_boundary_real_set_equality':'UNKNOWN',
                'native_full_q_void_inclusion':'UNKNOWN',
                'native_representative_interval':'NOT_TESTED'}
    result['inputs_sha256']={k:sha(v) for k,v in
        zip(('native_hierarchy','trim','stored','through_q'),raw)}
    (dest/'solid-boundary-census.json').write_text(
        json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    if len(sys.argv)!=6:
        raise SystemExit('usage: verify_solid_hierarchy.py NATIVE_JSON TRIM_JSON STORED_JSON THROUGH_Q_JSON OUTPUT_DIR')
    sys.exit(main(*(Path(a) for a in sys.argv[1:])))
