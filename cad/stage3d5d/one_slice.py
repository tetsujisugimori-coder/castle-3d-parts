"""One-pose / one-leaf native diagnostic, not a real-CAD proof issuer.

Uses the pinned Stage 3-D-2 model and fixed FCStd without recompute or save.
OCCT boolean volumes/distances are observations. No value promotes actual
material/void containment or continuous motion to PASS.
"""
from fractions import Fraction as Q
from hashlib import sha256
from pathlib import Path
import json
import sys
import traceback
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
FCSTD = ROOT / 'cad/stage3c/generated/assembly.FCStd'
CONTRACT = ROOT / 'cad/stage3d2/contract.json'
FCSTD_SHA = 'c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a'
CONTRACT_SHA = '88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa'
PARTS = ('GATE_Bolt', 'GATE_BoltGuide_Left')
LEAF_LO, LEAF_HI = Q(0), Q(35, 32)
REF = (LEAF_LO + LEAF_HI) / 2


def hash_bytes(b):
    return sha256(b).hexdigest()


def target(contract):
    """Only the unchanged D2 first leaf; exact model arithmetic in mm."""
    if (contract.get('schema') != 'aabb-union-translation-v1' or
            contract.get('unit') != 'mm' or contract.get('parts') != list(PARTS) or
            contract.get('door_degrees') != '0' or
            list(map(Q, contract.get('range', []))) != [Q(0), Q(140)] or
            list(map(Q, contract.get('moving_velocity', []))) != [Q(1), Q(0), Q(0)] or
            list(map(Q, contract.get('obstacle_velocity', []))) != [Q(0)] * 3 or
            len(contract.get('obstacle_boxes', [])) != 4):
        raise ValueError('D2_TARGET_CHANGED')
    moving = tuple(map(Q, contract['moving_box']))
    obstacles = [tuple(map(Q, b)) for b in contract['obstacle_boxes']]
    if len(moving) != 6 or any(len(b) != 6 for b in obstacles):
        raise ValueError('INVALID_BOX')
    if any(any(b[i] >= b[i+3] for i in range(3)) for b in [moving, *obstacles]):
        raise ValueError('NONPOSITIVE_BOX')
    # Closed channel through the guide at the reference travel.
    # X extends 1mm beyond both guide end faces; Y/Z equal bolt cross section.
    x0 = min(b[0] for b in obstacles) - 1
    x1 = max(b[3] for b in obstacles) + 1
    channel = (x0, moving[1], moving[2], x1, moving[4], moving[5])
    # Exact separation for a closed channel against all closed model slabs.
    margins = [max([b[d]-channel[d+3] for d in range(3)] +
                   [channel[d]-b[d+3] for d in range(3)]) for b in obstacles]
    if min(margins) <= 0:
        raise ValueError('CHANNEL_NOT_STRICTLY_OUTSIDE_MODEL_MATERIAL')
    # 1D L1 displacement is a conservative Euclidean bound for translation.
    motion = max(REF - LEAF_LO, LEAF_HI - REF)
    clearance = min(margins) - motion
    return {
        'door_degrees': '0', 'leaf_ordinal': 0,
        'interval_mm': [str(LEAF_LO), str(LEAF_HI)],
        'reference_travel_mm': str(REF),
        'model_query_channel_mm': [str(v) for v in channel],
        'model_slab_separation_mm': [str(x) for x in margins],
        'conditional_model_clearance_lower_mm': str(clearance),
        'movement_bound_mm': str(motion),
        'model_certificate': 'PASS' if clearance > 0 else 'UNKNOWN',
        'real_cad_certificate': 'NOT_TESTED',
    }


def interpretation(observed):
    """Observation labels cannot authorize native-real claims."""
    def candidate(kind, value):
        if value is None:
            return 'OBSERVATION_UNAVAILABLE'
        if kind == 'residual':
            return 'POSITIVE_DIFFERENCE_OBSERVED' if value > 0 else 'NO_POSITIVE_DIFFERENCE_OBSERVED_NOT_PROVEN'
        return 'POSITIVE_DISTANCE_OBSERVED_NOT_CERTIFIED' if value > 0 else 'CONTACT_OR_ZERO_DISTANCE_OBSERVED'
    return {
        'material_outer_probe': {k: candidate('residual', observed.get(k))
                                 for k in ('bolt_outside_model_volume_mm3', 'guide_outside_model_volume_mm3')},
        'void_inner_probe': candidate('distance', observed.get('guide_to_closed_channel_distance_mm')),
        'material_outer_containment': 'UNKNOWN',
        'void_inner_containment': 'UNKNOWN',
        'native_real_interval': 'NOT_TESTED',
        'reason': 'NATIVE_BOOLEAN_AND_DISTANCE_ARE_NOT_CERTIFIED_SET_ENCLOSURES',
    }


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    source = FCSTD.read_bytes(); contract_raw = CONTRACT.read_bytes()
    if hash_bytes(source) != FCSTD_SHA or hash_bytes(contract_raw) != CONTRACT_SHA:
        raise ValueError('FIXED_INPUT_SHA_MISMATCH')
    contract = json.loads(contract_raw)
    if contract.get('sources') is None or any(hash_bytes((ROOT / p).read_bytes()) != h
                                                   for p, h in contract['sources'].items()):
        raise ValueError('D2_DEPENDENCY_SHA_MISMATCH')
    leaf = target(contract)
    sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib'])
    import FreeCAD as App
    import Part

    def box(b):
        return Part.makeBox(*[float(b[i+3]-b[i]) for i in range(3)],
                            App.Vector(*[float(b[i]) for i in range(3)]))
    raw = {}
    with zipfile.ZipFile(FCSTD) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())) or archive.testzip() is not None:
            raise ValueError('FCSTD_ARCHIVE_INVALID')
        doc = ET.fromstring(archive.read('Document.xml'))
        angle = doc.find("./ObjectData/Object[@name='Mechanism']/Properties/Property[@name='Angle']/Float")
        travel = doc.find("./ObjectData/Object[@name='LockMechanism']/Properties/Property[@name='BoltPosition']/Float")
        if angle is None or travel is None or Q(angle.attrib['value']) != 0 or Q(travel.attrib['value']) != 0:
            raise ValueError('SAVED_BASE_POSE_NOT_ZERO')
        for name in PARTS:
            raw[name] = archive.read(name+'.Shape.brp')
    native = {}
    for name in PARTS:
        s = Part.Shape()
        s.importBrepFromString(raw[name].decode('utf-8'))
        if name == PARTS[0]:
            s.translate(App.Vector(float(REF), 0, 0))
        native[name] = s
    moving = tuple(map(Q, contract['moving_box']))
    moved = tuple(v + REF if i in (0,3) else v for i,v in enumerate(moving))
    nominal_bolt = box(moved)
    channel = box(tuple(map(Q, leaf['model_query_channel_mm'])))

    # All actual faces/edges/wires/vertices are observed anew from the fixed
    # BRep at the reference pose. The exact proof applies to these represented
    # coefficients only and NEVER authorizes an OCCT-real safety claim.
    sys.path.insert(0, str(ROOT / 'cad/stage3d5b'))
    sys.path.insert(0, str(ROOT / 'cad/stage3d5d'))
    import planar_native
    from correspondence import correspondence, pair_gap
    exact = {}
    for name, shape in native.items():
        topology = planar_native.topology(shape)
        boxes_mm = [list(map(str, moved))] if name == PARTS[0] else contract['obstacle_boxes']
        query_mm = leaf['model_query_channel_mm'] if name == PARTS[1] else None
        candidate = correspondence(topology, boxes_mm, query_mm)
        native_observations = {
            'single_solid_observed': len(shape.Solids) == 1,
            'closed_observed': bool(shape.isClosed()),
            'valid_observed': bool(shape.isValid()),
        }
        exact[name] = {
            'source_brep_sha256': hash_bytes(raw[name]),
            'reference_pose_mm': str(REF) if name == PARTS[0] else '0',
            'native_observations_not_proof': native_observations,
            'full_topology_observation': topology,
            'conditional_exact_candidate': candidate,
        }
    candidates = {name: exact[name]['conditional_exact_candidate'] for name in PARTS}
    pair = pair_gap(candidates[PARTS[0]], candidates[PARTS[1]])
    (output / 'boundary-correspondence.json').write_text(
        json.dumps({'schema':'d5d-full-native-candidate-bridge-v1',
                    'fixed_fcstd_sha256':FCSTD_SHA, 'source_d2_sha256':CONTRACT_SHA,
                    'reference_pose_mm':str(REF), 'parts':exact,
                    'candidate_pair_distance':pair,
                    'native_set_equality':'UNKNOWN',
                    'native_material_outer':'UNKNOWN', 'native_void_inner':'UNKNOWN',
                    'native_full_interval':'NOT_TESTED',
                    'unproved':['pcurve-to-surface-to-edge continuous native-real equality',
                                'trim domains and OCCT interior orientation semantics',
                                'finite native-real error enclosure and world-state equivalence']},
                   indent=2, allow_nan=False)+'\n', encoding='utf-8')
    measured = {}
    errors = {}
    for name, shape in native.items():
        key = 'bolt' if name == PARTS[0] else 'guide'
        try:
            residual = shape.cut(nominal_bolt) if name == PARTS[0] else shape
            if name == PARTS[1]:
                for raw_box in contract['obstacle_boxes']:
                    residual = residual.cut(box(tuple(map(Q, raw_box))))
            measured[key+'_outside_model_volume_mm3'] = float(residual.Volume)
            measured[key+'_native_volume_mm3'] = float(shape.Volume)
            measured[key+'_is_valid_observed'] = bool(shape.isValid())
        except Exception as exc:
            measured[key+'_outside_model_volume_mm3'] = None
            errors[key+'_material_probe'] = type(exc).__name__ + ': ' + str(exc)
    try:
        measured['guide_to_closed_channel_distance_mm'] = float(native[PARTS[1]].distToShape(channel)[0])
        measured['guide_channel_common_volume_mm3'] = float(native[PARTS[1]].common(channel).Volume)
    except Exception as exc:
        measured['guide_to_closed_channel_distance_mm'] = None
        errors['void_probe'] = type(exc).__name__ + ': ' + str(exc)
    if (any(candidates[name]['status'] != 'PASS' or not all(
            exact[name]['native_observations_not_proof'].values()) for name in PARTS)
            or pair['status'] != 'PASS'):
        errors['exact_candidate_bridge'] = 'CANDIDATE_MISMATCH_OR_UNSUPPORTED_NATIVE_OBSERVATION'
    if FCSTD.read_bytes() != source or CONTRACT.read_bytes() != contract_raw:
        raise ValueError('PINNED_SOURCE_CHANGED_DURING_READ')
    report = {
        'schema': 'd5d-one-slice-native-observation-v1',
        'source_sha256': {'fcstd': FCSTD_SHA, 'contract': CONTRACT_SHA,
                          **{name+'.Shape.brp':hash_bytes(raw[name]) for name in PARTS}},
        'engine': {'freecad': App.Version(), 'occt': getattr(Part,'OCC_VERSION','UNKNOWN')},
        'operation': 'read-only BRep import; isolated translated bolt; no Document recompute/save',
        'target': leaf,
        'observed_native': measured, 'observation_errors': errors,
        'assessment': interpretation(measured),
        'represented_boundary_correspondence': {
            'scope': 'full native-derived rational candidate, NOT native-real set proof',
            'file': 'boundary-correspondence.json',
            'bolt_candidate': candidates[PARTS[0]]['status'],
            'guide_candidate': candidates[PARTS[1]]['status'],
            'bolt_D2_bidirectional': candidates[PARTS[0]].get('represented_set_equality'),
            'guide_D2_bidirectional': candidates[PARTS[1]].get('represented_set_equality'),
            'guide_strict_void': candidates[PARTS[1]].get('candidate_void_to_query'),
            'exact_pair': pair,
            'native_real_material': 'UNKNOWN', 'native_real_void': 'UNKNOWN',
            'native_all_states': 'NOT_TESTED'},
        'material_outer_required': 'real BRep subset proven outer candidate with finite error enclosure',
        'void_inner_required': 'closed query strictly inside actual open complement for all poses',
        'continuous_motion_required': 'certified state mapping, finite bounds and reference displacement',
        'real_cad_128': {'PASS':0, 'FAIL':0, 'UNKNOWN':0, 'NOT_TESTED':128},
        'warning': 'Zero cut volume or positive observed distance is not a mathematical containment proof.',
    }
    (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'reference_mm':str(REF),'conditional_clearance_mm':leaf['conditional_model_clearance_lower_mm'],
                      'native_real_interval':report['assessment']['native_real_interval'],
                      'diagnostic_errors':len(errors)}))
    return 0 if not errors else 2


if __name__ == '__main__':
    dest = Path(sys.argv[1])
    try:
        sys.exit(main(dest))
    except Exception:
        if dest.is_dir():
            (dest/'error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
