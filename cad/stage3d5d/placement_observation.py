"""Compare the saved Shape, Document and reported World at three leaf states.

Only exact comparisons of represented coefficients/vertices are performed.
Finite samples cannot prove the native continuous state function.
"""
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from one_slice import FCSTD, FCSTD_SHA, LEAF_LO, LEAF_HI, PARTS, REF, ROOT

sys.path[:0] = [str(ROOT / 'cad' / d) for d in ('stage3d5b', 'stage3c')]
from native import placement
from state import transition
from transform_bounds import IDENTITY, compose


def matrix(p):
    return tuple(Q(x) for x in p['matrix_observed'][:12])


def compose_exact(outer, inner):
    return tuple(x.lo for x in compose(outer, inner))


def vertices(shape):
    return sorted(tuple(Q(x) for x in (v.Point.x, v.Point.y, v.Point.z))
                  for v in shape.Vertexes)


def shift(points, dx):
    return sorted((p[0] + dx, *p[1:]) for p in points)


def inventory(doc, name, stored, t):
    obj = doc.getObject(name)
    obj_place = placement(obj.Placement)
    world = placement(obj.getGlobalPlacement())
    shape_place = placement(obj.Shape.Placement)
    parents = []
    seen = {obj.Name}
    parent = obj.getParentGeoFeatureGroup()
    path = tuple(IDENTITY)
    while parent is not None:
        if parent.Name in seen:
            raise ValueError('PARENT_CYCLE')
        seen.add(parent.Name)
        p = placement(parent.Placement)
        path = compose_exact(matrix(p), path)
        parents.append({'name': parent.Name, 'placement': p})
        parent = parent.getParentGeoFeatureGroup()
    serialized = placement(stored.Placement)
    delta = t if name == PARTS[0] else Q(0)
    expected = list(matrix(serialized))
    expected[3] += delta
    doc_points = vertices(obj.Shape)
    return {
        'object': name, 'parent_chain_nearest_first': parents,
        'saved_shape_location': serialized, 'object_placement': obj_place,
        'document_shape_location': shape_place, 'api_global_placement': world,
        'shape_placement_expression': [list(e) for e in obj.ExpressionEngine if 'Placement' in e[0]],
        'represented_checks': {
            'object_and_shape_matrix_equal': matrix(obj_place) == matrix(shape_place),
            'parent_times_object_equals_api_global': compose_exact(path, matrix(obj_place)) == matrix(world),
            'document_shape_matrix_equals_saved_plus_nominal_delta': tuple(expected) == matrix(shape_place),
            'document_vertices_equal_saved_plus_nominal_delta': doc_points == shift(vertices(stored), delta),
        },
        'document_vertex_coordinates_exact_ieee_mm': [[str(v) for v in p] for p in doc_points],
    }


CHECKS = frozenset((
    'object_and_shape_matrix_equal',
    'parent_times_object_equals_api_global',
    'document_shape_matrix_equals_saved_plus_nominal_delta',
    'document_vertices_equal_saved_plus_nominal_delta',
))


def sampled_gate(cases):
    if [c['requested_mm'] for c in cases] != list(map(str, (LEAF_LO, REF, LEAF_HI))):
        return 'FAIL'
    for c in cases:
        if (c['represented_bolt_mm'] != c['requested_mm'] or c['angle_degrees'] != '0'
                or [p['object'] for p in c['parts']] != list(PARTS)):
            return 'FAIL'
        for p in c['parts']:
            observed = p['represented_checks']
            if set(observed) != CHECKS or any(value is not True for value in observed.values()):
                return 'FAIL'
    return 'PASS'


def main(out, work):
    sys.path[:0] = ['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib']
    import FreeCAD as A
    import Part
    orig = FCSTD.read_bytes()
    if sha256(orig).hexdigest() != FCSTD_SHA:
        raise ValueError('PINNED_FCSTD_MISMATCH')
    # Only the byte-identical isolated input is opened/recomputed; neither file is saved.
    out.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=False)
    scratch = work / 'transient'
    scratch.mkdir()
    isolated = work / 'assembly.FCStd'
    isolated.write_bytes(orig)
    with ZipFile(isolated) as archive:
        raw = {name: archive.read(name + '.Shape.brp') for name in PARTS}
    stored = {}
    for name, b in raw.items():
        shape = Part.Shape()
        shape.importBrepFromString(b.decode('utf-8'))
        stored[name] = shape
    doc = A.newDocument('D5DIsolatedLeaf')
    cases = []
    try:
        doc.TransientDir = str(scratch.resolve()) + '/'
        doc.FileName = str(isolated.resolve())
        doc.restore()
        for obj in doc.Objects:
            if 'KeepUpdated' in obj.PropertiesList:
                obj.KeepUpdated = False
        for t in (LEAF_LO, REF, LEAF_HI):
            transition(doc, 0, float(t / 1000))
            actual = Q(doc.getObject('LockMechanism').BoltPosition.Value)
            angle = Q(doc.getObject('Mechanism').Angle.Value)
            if actual != t or angle != 0:
                raise ValueError('DOCUMENT_STATE_INPUT_NOT_REPRESENTED_AS_TARGET')
            cases.append({'requested_mm': str(t), 'represented_bolt_mm': str(actual), 'angle_degrees': str(angle),
                          'parts': [inventory(doc, name, stored[name], t) for name in PARTS]})
    finally:
        A.closeDocument(doc.Name)
        if not isolated.is_file() or isolated.read_bytes() != orig or FCSTD.read_bytes() != orig:
            raise ValueError('FCSTD_OR_ISOLATED_BYTES_CHANGED')
    result = {'schema': 'd5d-isolated-leaf-placement-observation-v1',
              'freecad': A.Version(), 'occt': Part.OCC_VERSION,
              'fcstd_sha256': FCSTD_SHA,
              'brep_sha256': {key: sha256(value).hexdigest() for key, value in raw.items()},
              'sampled_cases': cases, 'represented_sampled_checks': sampled_gate(cases),
              'native_real_world_equivalence': 'UNKNOWN',
              'all_state_equivalence': 'UNKNOWN', 'continuous_motion': 'NOT_TESTED'}
    (out / 'placement.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    # Never include FreeCAD transient/embedded data in the evidence bundle.
    return 0 if result['represented_sampled_checks'] == 'PASS' else 2


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
