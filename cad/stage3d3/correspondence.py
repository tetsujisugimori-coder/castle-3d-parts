"""Identity/observation gate, not an imported-BRep containment theorem prover."""
import hashlib
import json
from pathlib import Path

D2 = Path(__file__).resolve().parents[1] / 'stage3d2/contract.json'
if hashlib.sha256(D2.read_bytes()).hexdigest() != '88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa':
    raise ValueError('D2_CONTRACT_HASH_MISMATCH')
SOURCES = json.loads(D2.read_text())['sources']
PARTS = ['GATE_Bolt', 'GATE_BoltGuide_Left']

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def evaluate(observation, reference):
    """Reference is read from the pinned original in this execution, never a proof."""
    reasons = []
    if (reference.get('sources') != SOURCES or reference.get('unit') != 'mm'
            or set(reference.get('parts', {})) != set(PARTS)):
        reasons.append('INVALID_REFERENCE')
    if observation.get('sources') != SOURCES:
        reasons.append('SOURCE_IDENTITY_MISMATCH')
    if observation.get('unit') != 'mm':
        reasons.append('UNIT_MISMATCH')
    if observation.get('coordinate_frame') != 'FreeCAD world; project m -> native mm x1000':
        reasons.append('COORDINATE_FRAME_MISMATCH')
    if observation.get('door_degrees') != 0 or observation.get('travel_mm') != [0, 140]:
        reasons.append('MOTION_CONTRACT_MISMATCH')
    if set(observation.get('parts', {})) != set(PARTS):
        reasons.append('PART_SET_MISMATCH')
    for part in PARTS:
        actual = observation.get('parts', {}).get(part)
        expected = reference.get('parts', {}).get(part)
        if not actual or not expected:
            continue
        if actual != expected:
            reasons.append('SHAPE_OR_PLACEMENT_CHANGED:' + part)
        if actual.get('valid') is not True or actual.get('solids') != 1:
            reasons.append('INVALID_OBSERVED_SOLID:' + part)
    # No caller supplied PASS/proof fields can establish a CAD theorem.
    return {
        'status': 'REJECTED' if reasons else 'UNKNOWN',
        'input_identity': 'PASS' if observation.get('sources') == SOURCES else 'FAIL',
        'observed_contract': 'FAIL' if reasons else 'PASS',
        'reasons': reasons or ['NO_CERTIFIED_BREP_CONTAINMENT_OR_VOID_LOWER_BOUND'],
        'shape_containment': 'UNKNOWN', 'placement_enclosure': 'UNKNOWN',
        'numerical_error_bound': 'UNKNOWN', 'continuous_motion_bound': 'UNKNOWN',
        'd2_cad_application': 'UNKNOWN', 'cad_intervals': {'PASS': 0, 'FAIL': 0, 'UNKNOWN': 128},
        'scope': 'fixed-input observational correspondence; no proof by numerical agreement',
    }
