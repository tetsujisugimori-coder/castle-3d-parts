"""Read-only native observations from fixed FCStd-embedded BRep bytes.

No Document is opened, recomputed, repaired, placed or saved. The embedded
TopoShape is imported with its serialized Location; XML Placement is recorded,
never applied again. Values returned by OCCT are observations, not interval
enclosures. This program cannot issue a BRep inclusion or motion PASS.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET
import zipfile
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[2]
PARTS = ('GATE_Bolt', 'GATE_BoltGuide_Left')
FCSTD = ROOT / 'cad/stage3c/generated/assembly.FCStd'
FCSTD_PIN = 'c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a'
LEGACY_FCSTD = '4597bee609eb4f3e262a60c8989f1cfb0ba90081408b4c3f0703c2ae8fd911a2'
CONTRACT = ROOT / 'cad/stage3d2/contract.json'
CONTRACT_PIN = '88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def point(v):
    return [v.x, v.y, v.z]


def placement(p):
    return {'base_mm_observed': point(p.Base),
            'quaternion_xyzw_observed': list(p.Rotation.Q),
            'matrix_observed': list(p.toMatrix().A)}


def optional(ob, name, errors, label):
    """Record API availability errors instead of silently inventing parameters."""
    try:
        value = getattr(ob, name)
        if all(hasattr(value, k) for k in ('x', 'y', 'z')):
            return point(value)
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return list(value)
        return str(value)
    except Exception as error:
        errors.append({'field': label + '.' + name, 'error': type(error).__name__ + ': ' + str(error)})
        return None


def edge_record(edge, errors):
    record = {'curve_type': type(edge.Curve).__name__, 'orientation': edge.Orientation,
              'vertices_mm_observed': [point(v.Point) for v in edge.Vertexes],
              'parameter_range_observed': [edge.FirstParameter, edge.LastParameter],
              'length_mm_observed': edge.Length, 'tolerance_max_mm_observed': edge.getTolerance(1)}
    if record['curve_type'] in ('Circle', 'Ellipse'):
        record['center_mm_observed'] = optional(edge.Curve, 'Center', errors, 'edge.curve')
        record['axis_observed'] = optional(edge.Curve, 'Axis', errors, 'edge.curve')
        record['radius_mm_observed'] = optional(edge.Curve, 'Radius', errors, 'edge.curve')
    return record


def describe(shape):
    errors, faces = [], []
    for index, face in enumerate(shape.Faces, 1):
        surface = face.Surface
        uv = list(face.ParameterRange)
        sample_u, sample_v = (uv[0] + uv[1]) / 2, (uv[2] + uv[3]) / 2
        wires = []
        for wire in face.Wires:
            try:
                role = 'outer' if wire.isSame(face.OuterWire) else 'inner-trim-candidate'
            except Exception as error:
                role = 'UNKNOWN'
                errors.append({'field': 'wire.outer-role', 'error': str(error)})
            wires.append({'role_observed': role, 'orientation': wire.Orientation,
                          'closed_observed': wire.isClosed(),
                          'edges': [edge_record(edge, errors) for edge in wire.OrderedEdges]})
        parameters = {key: optional(surface, key, errors, 'surface')
                      for key in ('Position', 'Axis')}
        if type(surface).__name__ in ('Cylinder', 'Cone', 'Sphere', 'Toroid'):
            parameters['Radius'] = optional(surface, 'Radius', errors, 'surface')
        descriptor = {'surface_type': type(surface).__name__, 'orientation': face.Orientation,
                      'surface_parameters_observed': parameters, 'uv_range_observed': uv,
                      'normal_at_uv_midpoint_observed': point(face.normalAt(sample_u, sample_v)),
                      'normal_sample_uv': [sample_u, sample_v],
                      'area_mm2_observed': face.Area,
                      'tolerance_max_mm_observed': face.getTolerance(1), 'wires': wires,
                      'vertices_mm_observed': sorted(point(v.Point) for v in face.Vertexes)}
        faces.append({'lookup_index': index, 'descriptor_sha256': digest(canonical(descriptor)),
                      'identity_scope': 'this fixed input and extraction; not a persistent Face number',
                      **descriptor})
    serialized = shape.exportBrepToString().encode()
    face_types = sorted(set(face['surface_type'] for face in faces))
    circles = [{'face_descriptor_sha256': face['descriptor_sha256'], 'wire_index': wi,
                'edge_index': ei, 'curve_type': edge['curve_type']}
               for face in faces for wi, wire in enumerate(face['wires'])
               for ei, edge in enumerate(wire['edges']) if edge['curve_type'] == 'Circle']
    inner_trims = [{'face_descriptor_sha256': face['descriptor_sha256'], 'wire_index': wi,
                    'status': 'OBSERVED_TRIM_ONLY; throughness and void inclusion UNKNOWN'}
                   for face in faces for wi, wire in enumerate(face['wires'])
                   if wire['role_observed'] == 'inner-trim-candidate']
    return {'valid_observed': shape.isValid(), 'closed_observed': shape.isClosed(),
            'solid_count': len(shape.Solids), 'shell_count': len(shape.Shells),
            'face_count': len(shape.Faces), 'wire_count': len(shape.Wires),
            'edge_count': len(shape.Edges), 'vertex_count': len(shape.Vertexes),
            'solid_orientations': [s.Orientation for s in shape.Solids],
            'shell_orientations': [s.Orientation for s in shape.Shells],
            'shape_placement_observed': placement(shape.Placement),
            'bounds_mm_observed': [getattr(shape.BoundBox, key) for key in
                                   ('XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax')],
            'volume_mm3_observed': shape.Volume,
            'tolerance_min_mm_observed': shape.getTolerance(-1),
            'tolerance_max_mm_observed': shape.getTolerance(1),
            'kernel_serialized_sha256': digest(serialized), 'kernel_serialized_bytes': len(serialized),
            'surface_types_observed': face_types, 'faces': faces,
            'cylindrical_face_candidates': [f['descriptor_sha256'] for f in faces if f['surface_type'] == 'Cylinder'],
            'circular_edge_candidates': circles, 'inner_trim_candidates': inner_trims,
            'unsupported_surface_types': [kind for kind in face_types if kind != 'Plane'],
            'parameter_extraction_errors': errors,
            'guarantees': {key: 'UNKNOWN' for key in
                           ('solid_inclusion', 'hole_void_inclusion', 'placement_error',
                            'numeric_error', 'continuous_motion')}}


def xml_object(doc, name):
    node = doc.find("./ObjectData/Object[@name='" + name + "']")
    if node is None:
        raise ValueError('OBJECT_MISSING:' + name)
    properties = {p.attrib['name']: ET.tostring(p, encoding='unicode')
                  for p in node.findall('./Properties/Property')}
    shape = node.find("./Properties/Property[@name='Shape']/Part")
    raw_placement = node.find("./Properties/Property[@name='Placement']/PropertyPlacement")
    return {'object_id': name, 'shape_ref': None if shape is None else shape.attrib['file'],
            'placement_xml': None if raw_placement is None else raw_placement.attrib,
            'selected_properties_xml': {key: properties[key] for key in
                                        ('PartID', 'Shape', 'Placement', 'ExpressionEngine') if key in properties}}


def nominal_boundaries(contract):
    sys.path.insert(0, str(ROOT / 'cad/stage3d4'))
    from boundary import from_boxes
    return {PARTS[0]: from_boxes([contract['moving_box']]),
            PARTS[1]: from_boxes(contract['obstacle_boxes'])}


def correspondence(observation, nominal):
    """Only nominal plane candidates; never promote observations to exact values."""
    rows = []
    for face in observation['faces']:
        candidates = []
        vertices = face['vertices_mm_observed']
        if face['surface_type'] == 'Plane' and vertices:
            for i, rectangle in enumerate(nominal['faces']):
                axis = rectangle['axis']
                # Equality of observed decimals is merely a candidate filter.
                # It proves neither extraction error nor trim/Solid inclusion.
                if all(Fraction(str(v[axis])) == Fraction(rectangle['coordinate']) for v in vertices):
                    candidates.append({'model_face_id': 'D4-rectangle-' + str(i),
                                       'model_face': rectangle})
        rows.append({'brep_face_descriptor_sha256': face['descriptor_sha256'],
                     'lookup_index': face['lookup_index'], 'candidate_model_faces': candidates,
                     'candidate_basis': 'observed planar vertex coordinate equals nominal plane coordinate only',
                     'trim_coverage': 'UNKNOWN', 'normal_relation': 'UNKNOWN',
                     'solid_side': 'UNKNOWN', 'relation': 'NOT_PROVEN',
                     'unresolved': ['no extraction-error enclosure', 'no all-trim correspondence proof',
                                    'no solid topology-to-set inclusion theorem']})
    return rows


def run(out):
    sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib'])
    import FreeCAD as A
    import Part
    source_bytes = FCSTD.read_bytes()
    contract_bytes = CONTRACT.read_bytes()
    if digest(source_bytes) != FCSTD_PIN or digest(contract_bytes) != CONTRACT_PIN:
        raise ValueError('PINNED_MAIN_INPUT_MISMATCH')
    contract = json.loads(contract_bytes)
    source_hashes = {name: digest((ROOT / name).read_bytes()) for name in contract['sources']}
    if source_hashes != contract['sources']:
        raise ValueError('D2_SOURCE_SET_MISMATCH')
    nominal = nominal_boundaries(contract)
    (out / 'nominal-d4-boundaries.json').write_text(json.dumps(nominal, indent=2), encoding='utf-8')
    records, raw_shapes, archive_entries = {}, {}, []
    with zipfile.ZipFile(FCSTD) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or archive.testzip() is not None:
            raise ValueError('ARCHIVE_STRUCTURE_OR_CRC')
        for info in archive.infolist():
            data = archive.read(info.filename)
            archive_entries.append({'name': info.filename, 'size_bytes': len(data),
                                    'sha256': digest(data), 'crc32': f'{info.CRC:08x}'})
        doc = ET.fromstring(archive.read('Document.xml'))
        angle = doc.find("./ObjectData/Object[@name='Mechanism']/Properties/Property[@name='Angle']/Float")
        travel = doc.find("./ObjectData/Object[@name='LockMechanism']/Properties/Property[@name='BoltPosition']/Float")
        if angle is None or travel is None or Fraction(angle.attrib['value']) != 0 or Fraction(travel.attrib['value']) != 0:
            raise ValueError('SAVED_BASE_POSE_NOT_ZERO')
        for name in PARTS:
            meta = xml_object(doc, name)
            if meta['shape_ref'] != name + '.Shape.brp' or meta['placement_xml'] is None:
                raise ValueError('SHAPE_REFERENCE_OR_PLACEMENT:' + name)
            raw = archive.read(meta['shape_ref'])
            (out / (name + '.original.brp')).write_bytes(raw)
            shape = Part.Shape()
            shape.importBrepFromString(raw.decode('utf-8'))
            raw_shapes[name] = raw
            description = describe(shape)
            before = shape.exportBrepToString().encode()
            # Re-describe the same untouched shape to check observation does
            # not mutate its in-memory representation. This is not a proof.
            after_description = describe(shape)
            after = shape.exportBrepToString().encode()
            if before != after or description != after_description:
                raise ValueError('EXTRACTION_MUTATED_IMPORTED_SHAPE:' + name)
            (out / (name + '.kernel-export.brep')).write_bytes(before)
            records[name] = {'xml': meta, 'archive_brep_sha256': digest(raw),
                             'archive_brep_bytes': len(raw), 'observation': description,
                             'kernel_before_after_equal': True,
                             'raw_vs_kernel_bytes_equal': raw == before,
                             'coordinate_rule': 'import serialized Shape Location once; XML Placement never reapplied',
                             'coordinate_interpretation_proof': 'UNKNOWN',
                             'correspondence': correspondence(description, nominal[name])}

    def clone(name):
        s = Part.Shape()
        s.importBrepFromString(raw_shapes[name].decode('utf-8'))
        return s

    poses = []
    for distance in (0, 70, 140):
        b, g = clone(PARTS[0]), clone(PARTS[1])
        b.translate(A.Vector(distance, 0, 0))
        pose_dir = out / ('derived-pose-' + str(distance)); pose_dir.mkdir()
        for name, shape in zip(PARTS, (b, g)):
            (pose_dir / (name + '.brep')).write_bytes(shape.exportBrepToString().encode())
        poses.append({'travel_mm': distance, 'door_degrees': 0,
                      'kind': 'derived isolated Shape translation from saved-zero BRep, not native Document recompute',
                      'distance_mm_observed': b.distToShape(g)[0],
                      'parts': {name: describe(s) for name, s in zip(PARTS, (b, g))},
                      'continuous_safety': 'UNKNOWN', 'state_pipeline_equivalence': 'UNKNOWN'})

    mutations = []
    for case in ('orientation-reversed', 'translation-shift', 'missing-face-open-shell'):
        s = clone(PARTS[0])
        if case == 'orientation-reversed':
            s.reverse()
        elif case == 'translation-shift':
            s.translate(A.Vector(0, 1, 0))
        else:
            s = Part.makeShell(s.Faces[:-1])
        raw = s.exportBrepToString().encode()
        (out / (case + '.brep')).write_bytes(raw)
        description = describe(s)
        if digest(raw) == records[PARTS[0]]['observation']['kernel_serialized_sha256']:
            raise AssertionError('NATIVE_MUTATION_NOT_CHANGED:' + case)
        mutations.append({'case': case, 'kind': 'isolated native Shape mutation; original bytes untouched',
                          'part': PARTS[0], 'observation': description,
                          'fixed_input_match': 'REJECTED_CHANGED_BREP', 'inclusion': 'UNKNOWN'})

    if FCSTD.read_bytes() != source_bytes or CONTRACT.read_bytes() != contract_bytes:
        raise AssertionError('SOURCE_BYTES_CHANGED')
    if {name: digest((ROOT / name).read_bytes()) for name in source_hashes} != source_hashes:
        raise AssertionError('SOURCE_SET_CHANGED')
    result = {'schema': 'stage3d5b-native-observations-v1',
              'FreeCAD_version': A.Version(), 'OCCT_version': getattr(Part, 'OCC_VERSION', 'UNKNOWN'),
              'execution_subject': 'CI Python process with FreeCAD/OCCT modules; not GUI/manual execution',
              'source_fcstd': {'path': str(FCSTD.relative_to(ROOT)), 'sha256': FCSTD_PIN, 'size_bytes': len(source_bytes)},
              'legacy_fcstd_sha256': LEGACY_FCSTD, 'legacy_input_reused': False,
              'source_set_before': source_hashes, 'source_set_after': source_hashes,
              'archive_entries': archive_entries, 'archive_crc': 'PASS', 'document_opened': False,
              'document_recomputed': False, 'document_saved': False, 'repair_applied': False,
              'unit': 'mm', 'metres_conversion': 'divide observed lengths by 1000; no certified extraction enclosure',
              'records': records, 'derived_poses': poses, 'isolated_native_faults': mutations,
              'material_outer_containment': 'UNKNOWN', 'hole_inner_containment': 'UNKNOWN',
              'finite_error_bounds_m': {key: None for key in ('geometry', 'brep_tolerance_relation', 'extraction',
                                                           'transform', 'rounding', 'pose', 'motion')},
              'continuous_motion': 'NOT_TESTED',
              'current_run_cad_intervals': {'PASS': 0, 'FAIL': 0, 'UNKNOWN': 0, 'NOT_TESTED': 128},
              'prior_D4_real_CAD': {'origin': 'separate historical stage', 'UNKNOWN': 128},
              'warning': 'All numeric geometry and topology results are observations. No BRep inclusion or finite-error proof.'}
    (out / 'native.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('Read fixed main FCStd BRep members; native observations recorded; real inclusion UNKNOWN', flush=True)


if __name__ == '__main__':
    target = Path(sys.argv[1])
    created = False
    try:
        target.mkdir(parents=True, exist_ok=False)
        created = True
        run(target)
    except BaseException:
        error = traceback.format_exc()
        # Never overwrite an existing result directory on an accidental rerun.
        if created and target.is_dir() and not (target / 'error.txt').exists():
            (target / 'error.txt').write_text(error, encoding='utf-8')
        os.write(2, error.encode('utf-8'))
        os._exit(1)
    os._exit(0)
