"""Fixed Guide orientation census and bounded native point-classifier comparison.

All reported PASS claims are finite recorded occurrences or rational D2-model
facts. Neither finite classifiers nor a closed shell prove OCCT material/void
inclusion for every real point. Native set claims must remain UNKNOWN.
"""
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from one_slice import CONTRACT, CONTRACT_SHA, FCSTD, FCSTD_SHA, PARTS


def sha(data):
    return sha256(data).hexdigest()


def rational_point(c):
    return tuple(F(v) for v in c)


def in_closed(b, p):
    return all(b[i] <= p[i] <= b[i + 3] for i in range(3))


def expected_samples(contract):
    """One specific D2 Guide. All points are exact integers and off boundary."""
    b = [rational_point(q) for q in contract['obstacle_boxes']]
    if len(b) != 4 or contract['parts'] != list(PARTS):
        raise ValueError('UNEXPECTED_D2_GUIDE')
    bottom_y, upper_y, floor_z, roof_z = b
    x0, x1 = bottom_y[0], bottom_y[3]
    if not all(q[0] == x0 and q[3] == x1 for q in b):
        raise ValueError('GUIDE_X_RANGE_CHANGED')
    yl, yh, zl, zh = bottom_y[4], upper_y[1], floor_z[5], roof_z[2]
    mid = lambda a, c: (a + c) / 2
    xm, ym, zm = mid(x0, x1), mid(yl, yh), mid(zl, zh)
    def row(label, x, y, z, group):
        p = (x, y, z)
        # Intentionally no points on any model boundary: ON cannot establish
        # strict empty-space membership under kernel tolerances.
        if any(in_closed(q, p) and any(p[i] in (q[i], q[i+3]) for i in range(3)) for q in b):
            raise ValueError('SAMPLE_TOUCHES_MATERIAL_BOUNDARY')
        state = 'IN' if any(all(q[i] < p[i] < q[i+3] for i in range(3)) for q in b) else 'OUT'
        if not all(v.denominator == 1 for v in p):
            raise ValueError('SAMPLE_NOT_EXACT_BINARY_INTEGER')
        return {'id': label, 'point_mm_exact': [str(v) for v in p], 'expected': state, 'role': group}
    rows = [
        row('material_lower_y',xm,yl-1,zm,'closed_material'),
        row('void_near_lower_y',xm,yl+1,zm,'open_void'),
        row('void_center',xm,ym,zm,'open_void'),
        row('void_near_upper_y',xm,yh-1,zm,'open_void'),
        row('material_upper_y',xm,yh+1,zm,'closed_material'),
        row('material_floor',xm,ym,zl-1,'closed_material'),
        row('void_near_floor',xm,ym,zl+1,'open_void'),
        row('void_near_roof',xm,ym,zh-1,'open_void'),
        row('material_roof',xm,ym,zh+1,'closed_material'),
        row('through_end_negative_x',x0-1,ym,zm,'open_void'),
        row('through_end_positive_x',x1+1,ym,zm,'open_void'),
        row('exterior_outer',xm,bottom_y[1]-1,zm,'external_void'),
    ]
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('DUPLICATED_SAMPLE_IDS')
    return rows


def guide_census(trim, stored):
    if (trim.get('status') != 'PASS' or trim.get('edge_use_count') != 48
        or len(trim.get('faces', [])) != 10
        or not isinstance(stored, list) or len(stored) != 48):
        return {'status':'FAIL','reason':'MISSING_GUIDE_BOUNDARY_OR_STORED_PCURVES'}
    occurrences = set()
    roles = {'outer': 0, 'inner': 0}
    for face in trim['faces']:
        if face.get('status') != 'PASS' or face.get('represented_material_side', {}).get('status') != 'PASS':
            return {'status':'FAIL','reason':'FACE_SIDE_OR_TRIM_UNVERIFIED'}
        if not isinstance(face.get('wires'), list):
            return {'status':'FAIL','reason':'WIRE_INVENTORY_UNAVAILABLE'}
        for wire in face['wires']:
            if wire.get('role') not in roles:
                return {'status':'FAIL','reason':'UNKNOWN_WIRE_ROLE'}
            roles[wire['role']] += 1
            for use in wire.get('uses', []):
                key = (face['face'], wire['wire'], use['edge'], use['use'])
                if key in occurrences:
                    return {'status':'FAIL','reason':'DUPLICATE_ORIENTED_USE'}
                occurrences.add(key)
    stored_keys = set()
    for r in stored:
        if r.get('status') != 'PASS':
            return {'status':'FAIL','reason':'UNPROVEN_SAVED_PCURVE_USE'}
        key=(r.get('face'),r.get('wire'),r.get('edge'),r.get('formula_use_order'))
        if key in stored_keys:
            return {'status':'FAIL','reason':'DUPLICATE_SAVED_USE'}
        stored_keys.add(key)
    if len(occurrences) != 48 or roles != {'outer': 10, 'inner': 2} or occurrences != stored_keys:
        return {'status':'FAIL','reason':'NATIVE_GUIDE_ORIENTED_USE_OR_HOLE_CENSUS'}
    return {'status':'PASS','face_count':10,'wire_roles':roles,'stored_use_count':48,
            'scope':'native-derived oriented trim occurrences, not OCCT occupancy theorem'}


def validate_classification(rows, native):
    if (native.get('schema') != 1 or native.get('occt') != '7.8.1'
        or native.get('solid_count') != 1 or native.get('valid_observed') is not True
        or native.get('sample_count') != len(rows)
        or native.get('native_material_outer') != 'UNKNOWN'
        or native.get('native_void_inner') != 'UNKNOWN'):
        return {'status':'FAIL','reason':'NATIVE_CLASSIFIER_METADATA_INCOMPLETE'}
    seen = {}
    for sample in native.get('samples', []):
        key=sample.get('id')
        if key in seen or key not in {r['id'] for r in rows}:
            return {'status':'FAIL','reason':'DUPLICATE_OR_UNEXPECTED_POINT'}
        seen[key]=sample
    if set(seen) != {r['id'] for r in rows}:
        return {'status':'FAIL','reason':'SAMPLED_REGION_NOT_FULLY_OBSERVED'}
    checks = []
    for r in rows:
        n = seen[r['id']]
        # Coordinates from binary are observed floats; exact integer points
        # are all exactly representable and checked after serialization.
        if tuple(F(x) for x in n.get('point_mm', [])) != tuple(F(x) for x in r['point_mm_exact']):
            return {'status':'FAIL','reason':'OBSERVED_POINT_DIFFERENT_FROM_REQUEST'}
        observed=n.get('state')
        if observed not in ('IN','OUT','ON','UNKNOWN') or observed != r['expected']:
            return {'status':'FAIL','reason':'NATIVE_POINT_CLASSIFICATION_MISMATCH',
                    'id':r['id'],'expected':r['expected'],'observed':observed}
        checks.append({**r,'observed':observed})
    return {'status':'PASS','sample_count':len(checks),'samples':checks,
            'scope':'finite off-boundary OCCT classifier observation only'}


def assess(census, samples, candidate, stored):
    """All native real-set claims are fixed UNKNOWN, independent of inputs."""
    candidate_ok = (candidate.get('status') == 'PASS'
                    and candidate.get('represented_set_equality') == 'PASS'
                    and candidate.get('candidate_void_to_query',{}).get('status') == 'PASS')
    return {'status':'PASS' if census.get('status') == samples.get('status') == 'PASS'
                       and candidate_ok and len(stored) == 48 else 'FAIL',
            'oriented_boundary':census,'selected_region':samples,
            'exact_candidate_closed_material':'PASS' if candidate_ok else 'FAIL',
            'exact_candidate_open_void':'PASS' if candidate_ok else 'FAIL',
            'native_material_outer':'UNKNOWN','native_void_inner':'UNKNOWN',
            'native_all_point_occupancy':'UNKNOWN',
            'finite_real_error':'UNKNOWN','all_state_equivalence':'UNKNOWN',
            'native_representative_interval':'NOT_TESTED',
            'reason':'SAMPLED_NATIVE_CLASSIFIER_AND_EXACT_RATIONAL_CANDIDATE_ARE_NOT_ALL_POINT_OCCT_SET_EQUIVALENCE'}


def main(binary, brep, trim_file, stored_file, candidate_file, out):
    out.mkdir(parents=True, exist_ok=False)
    source=FCSTD.read_bytes()
    cbytes=CONTRACT.read_bytes()
    if sha(source)!=FCSTD_SHA or sha(cbytes)!=CONTRACT_SHA:
        raise ValueError('PINNED_INPUT_CHANGED')
    contract=json.loads(cbytes)
    with __import__('zipfile').ZipFile(FCSTD) as z:
        original=z.read('GATE_BoltGuide_Left.Shape.brp')
    if sha(original) != sha(brep.read_bytes()):
        raise ValueError('GUIDE_BREP_NOT_PINNED_RAW_INPUT')
    t=json.loads(trim_file.read_bytes())['parts'][PARTS[1]]
    stored=json.loads(stored_file.read_bytes())['parts'][PARTS[1]]
    candidate=json.loads(candidate_file.read_bytes())['parts'][PARTS[1]]['conditional_exact_candidate']
    census=guide_census(t,stored)
    points=expected_samples(contract)
    sample_input=out/'sample-requests.tsv'
    sample_input.write_text(''.join(r['id']+' '+' '.join(r['point_mm_exact'])+'\n' for r in points),encoding='ascii')
    p=subprocess.run([str(binary),str(brep),str(sample_input)],stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,timeout=45,check=False)
    (out/'occt-classifier.stdout.json').write_bytes(p.stdout)
    (out/'occt-classifier.stderr.txt').write_bytes(p.stderr)
    native=json.loads(p.stdout) if p.returncode in (0,2) and p.stdout else {}
    classification=validate_classification(points,native)
    result=assess(census,classification,candidate,stored)
    result.update({'schema':'d5d-guide-solid-observation-v1',
                   'input_brep_sha256':sha(original),
                   'classifier_binary_sha256':sha(binary.read_bytes()),
                   'native_exit':p.returncode,
                   'input_sha256':sha(sample_input.read_bytes()),
                   'source_trim_sha256':sha(trim_file.read_bytes()),
                   'source_stored_sha256':sha(stored_file.read_bytes()),
                   'source_candidate_sha256':sha(candidate_file.read_bytes()),
                   'sampling_tolerance_mm_observed':native.get('classifier_tolerance_mm')})
    (out/'guide-solid.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',
                                      encoding='utf-8')
    return 0 if p.returncode == 0 and result['status'] == 'PASS' else 2


if __name__=='__main__':
    sys.exit(main(*(Path(s) for s in sys.argv[1:])))
