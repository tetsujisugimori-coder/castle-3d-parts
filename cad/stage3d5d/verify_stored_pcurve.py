"""Join OCCT's same-process provenance to the unchanged FreeCAD 72-formula record."""
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from one_slice import CONTRACT_SHA, FCSTD, FCSTD_SHA, PARTS, REF

FORMULAS_SHA256 = '412e4488136ecb28a59a616c4d33d010ffaf75ff4e3ab962bfcf138920f9afe3'
BREP_SHA256 = dict(zip(PARTS, (
    '45ee396f5ac16f70d3eba4ab8ab21df86811c7757d4279ff4a37c2973d87c820',
    '043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261',
)))
PILOT = (0, 0, 0)  # Face, Wire, global Edge ID; unique non-seam Plane/Line use.
USE_COUNTS = dict(zip(PARTS, (24, 48)))
LOCATIONS = ('face_topological_location', 'wire_topological_location', 'edge_topological_location')


def digest(data):
    return sha256(data).hexdigest()


def exact(value):
    if isinstance(value, list):
        return tuple(map(exact, value))
    if type(value) not in (str, int, float):
        raise ValueError('NON_NUMERIC_COEFFICIENT')
    return Q(value)


def placement(value):
    t = exact(value)
    if len(t) != 4 or any(len(row) != 4 for row in t) or t[3] != (0, 0, 0, 1):
        raise ValueError('NOT_HOMOGENEOUS_LOCATION')
    return t


def compose_location(outer, inner):
    a, b = placement(outer), placement(inner)
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)) for i in range(4))


def identity(row):
    k = tuple(row[n] for n in ('face', 'wire', 'edge'))
    if any(type(n) is not int or n < 0 for n in k):
        raise ValueError('BAD_OCCURRENCE_INDEX')
    return k


def expected_formulas(record):
    if (record['source_fcstd_sha256'] != FCSTD_SHA or record['source_d2_sha256'] != CONTRACT_SHA
            or record['reference_pose_mm'] != str(REF) or set(record['parts']) != set(PARTS)):
        raise ValueError('FORMULA_SOURCE_OR_POSE_MISMATCH')
    out = {}
    for name in PARTS:
        part = record['parts'][name]
        if part['status'] != 'PASS' or part['source_brep_sha256'] != BREP_SHA256[name]:
            raise ValueError('FORMULA_PART_MISMATCH')
        rows = {}
        for face in part['faces']:
            for wire in face['wires']:
                for use in wire['uses']:
                    row = {**use, 'face': face['face'], 'wire': wire['wire'],
                           'face_orientation': face['orientation'], 'wire_orientation': wire['orientation'],
                           'plane': face['plane'], LOCATIONS[0]: face['location'],
                           LOCATIONS[1]: wire['location'], LOCATIONS[2]: use['location']}
                    k = identity(row)
                    if k in rows or use['represented_affine_link'] != 'PASS':
                        raise ValueError('FORMULA_OCCURRENCE_NOT_UNIQUE_OR_NOT_PROVEN')
                    del row['location']
                    rows[k] = row
        if len(rows) != USE_COUNTS[name]:
            raise ValueError('FORMULA_CENSUS_MISMATCH')
        out[name] = rows
    return out


def verdict(row, expected):
    def done(status, reason):
        return {'status': status, 'reason': reason}

    if not isinstance(row, dict):
        return done('UNKNOWN', 'NATIVE_OCCURRENCE_UNAVAILABLE')
    try:
        if identity(row) != identity(expected):
            return done('FAIL', 'FACE_WIRE_EDGE_MISMATCH')
        if any(row[k] != expected[k] for k in ('orientation', 'face_orientation', 'wire_orientation')):
            return done('FAIL', 'ORIENTATION_MISMATCH')
        if row.get('seam') is not False:
            return done('UNKNOWN', 'SEAM_OR_UNAVAILABLE')
        if row.get('stored') is False:
            return done('FAIL', 'GENERATED_OR_NO_STORED_PCURVE')
        if row.get('stored') is not True:
            return done('UNKNOWN', 'STORAGE_FLAG_UNAVAILABLE')
        if row.get('indexed_matches') != 1 or row.get('surface_location_candidate_count') != 1 or row.get('selected_2d_matches') != 1 or row.get('matching_3d_count') != 1:
            return done('UNKNOWN', 'STORED_HANDLE_SURFACE_LOCATION_NOT_UNIQUE')
        flags = [row.get(k) for k in ('same_parameter', 'same_range')]
        if any(v is False for v in flags):
            return done('FAIL', 'NATIVE_SAME_FLAG_FALSE')
        if any(v is not True for v in flags):
            return done('UNKNOWN', 'NATIVE_SAME_FLAG_UNAVAILABLE')
        pc_type = {'Geom2d_Line': 'Line2d', 'Geom2d_TrimmedCurve': 'Line2dSegment'}.get(row.get('pcurve_type'))
        if pc_type is None or row.get('curve_type') != 'Geom_Line' or row.get('surface_type') != 'Geom_Plane':
            return done('UNKNOWN', 'UNSUPPORTED_CURVE_OR_SURFACE')
        if (pc_type != expected['pcurve_type'] or row.get('status') != 'CAPTURED'
                or row.get('degenerated') is not False or any(type(row.get(k)) is not int or row[k] < 1
                    for k in ('selected_2d_rep_ordinal', 'selected_3d_rep_ordinal', 'indexed_tool_rank'))):
            return done('UNKNOWN', 'NATIVE_REPRESENTATION_NOT_VERIFIED')
        if any(exact(row[k]) != exact(expected[k]) for k in LOCATIONS):
            return done('FAIL', 'TOPOLOGICAL_LOCATION_MISMATCH')
        if (placement(row['surface_location']) != compose_location(row[LOCATIONS[2]], row['relative_rep_2d_location'])
                or placement(row['edge_location']) != compose_location(row[LOCATIONS[2]], row['relative_rep_3d_location'])):
            return done('FAIL', 'GEOMETRY_LOCATION_MISMATCH')
        if pc_type == 'Line2dSegment' and exact(row['pcurve_intrinsic_range']) != exact(expected['segment_intrinsic_range']):
            return done('FAIL', 'TRIM_INTRINSIC_RANGE_MISMATCH')
        if exact(row['indexed_range']) != exact(row['pcurve_range']):
            return done('FAIL', 'NATIVE_STORED_RANGE_MISMATCH')
        if any(exact(row[k]) != exact(expected[k]) for k in ('pcurve_range', 'curve_range')):
            return done('FAIL', 'FORMULA_RANGE_MISMATCH')
        if any(exact(row[k]) != exact(expected[k]) for k in ('plane', 'curve', 'pcurve')):
            return done('FAIL', 'FORMULA_COEFFICIENT_MISMATCH')
        if row.get('ordered_matches') != 1 or type(row.get('ordered_use')) is not int or type(row['use']) is not int or row['use'] < 0:
            return done('UNKNOWN', 'NATIVE_USE_ORDER_UNAVAILABLE')
        if row['ordered_use'] != expected['use']:
            return done('FAIL', 'ORIENTED_WIRE_USE_ORDER_MISMATCH')
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return done('UNKNOWN', 'NATIVE_METADATA_UNAVAILABLE')
    return done('PASS', 'SAME_PROCESS_STORED_HANDLE_AND_OLD_FORMULA_OCCURRENCE')


def controls(normal, expected):
    """Change only copied observations or expected records, never the BRep."""
    shifted_surface = [line[:] for line in normal['surface_location']]
    shifted_surface[0][3] += 1
    scenarios = [
        ('stored-absent', {'stored': False, 'indexed_matches': 0}, {}, 'FAIL'),
        ('generated-but-coefficients-identical', {'stored': False}, {}, 'FAIL'),
        ('range-mismatch', {'pcurve_range': [1, 39]}, {}, 'FAIL'),
        ('location-mismatch', {LOCATIONS[2]: [[0] * 4] * 4}, {}, 'FAIL'),
        ('different-face-use', {}, {'edge': expected['edge']+1}, 'FAIL'),
        ('reversed-usage', {'orientation': 'Reversed'}, {}, 'FAIL'),
        ('wrong-wire-order', {'ordered_use': expected['use']+1}, {}, 'FAIL'),
        ('surface-location-mismatch', {'surface_location': shifted_surface}, {}, 'FAIL'),
        ('same-parameter-false', {'same_parameter': False}, {}, 'FAIL'),
        ('same-range-unavailable', {'same_range': None}, {}, 'UNKNOWN'),
        ('ambiguous-surface-reps', {'surface_location_candidate_count': 2}, {}, 'UNKNOWN'),
        ('unknown-seam', {'seam': None}, {}, 'UNKNOWN'),
    ]
    return [{'case': 'normal', 'expected': 'PASS', **verdict(normal, expected)}] + [
        {'case': case, 'expected': want, **verdict({**normal, **bad}, {**expected, **different})}
        for case, bad, different, want in scenarios
    ]


def occt_libs(paths):
    found = {}
    for name in paths:
        path = Path(name).resolve(strict=True)
        if not re.fullmatch(r'libTK\w+\.so\.7\.8\.1', path.name):
            continue
        found[str(path)] = digest(path.read_bytes())
    return found


def runtime(binary):
    sys.path.extend(['/usr/lib/freecad-python3/lib', '/usr/lib/freecad/lib'])
    import FreeCAD
    import Part
    maps = Path('/proc/self/maps').read_text().splitlines()
    freecad = occt_libs({line.split()[-1] for line in maps if '/libTK' in line})
    ldd = subprocess.run(['ldd', str(binary)], capture_output=True, text=True, check=True, timeout=10)
    native = occt_libs(re.findall(r'=> (/[\w./+-]+\.so\.7\.8(?:\.1)?) ', ldd.stdout))
    abi = subprocess.run(['file', '-L', str(binary), Part.__file__], capture_output=True, text=True, check=True, timeout=10)
    mandatory = {'libTKBRep.so.7.8.1', 'libTKMath.so.7.8.1', 'libTKernel.so.7.8.1'}
    if (Part.OCC_VERSION != '7.8.1' or not mandatory <= {Path(p).name for p in native}
            or any(freecad.get(path) != hash_ for path, hash_ in native.items())):
        raise ValueError('NATIVE_AND_FREECAD_OCCT_BUILD_NOT_IDENTIFIED_AS_SAME')
    return {'freecad_version': FreeCAD.Version(), 'part_module': Part.__file__,
            'part_module_sha256': digest(Path(Part.__file__).read_bytes()), 'occt_version': Part.OCC_VERSION,
            'native_binary_sha256': digest(binary.read_bytes()), 'abi': abi.stdout,
            'same_resolved_runtime_libraries': native, 'freecad_other_loaded_occt_libraries': {
                p: h for p,h in freecad.items() if p not in native}, 'native_ldd': re.sub(r' \(0x[0-9a-fA-F]+\)', '', ldd.stdout)}


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def native_read(binary, brep, part, mode, output, build):
    dx = str(float(REF)) if part == PARTS[0] else '0'
    command = [str(binary), str(brep), mode, dx]
    run = subprocess.run(command, capture_output=True, timeout=30)
    label = f'{part}-{mode}'
    (output / (label+'.stdout.json')).write_bytes(run.stdout)
    (output / (label+'.stderr.txt')).write_bytes(run.stderr)
    save(output / (label+'.process.json'), {'command': command, 'returncode': run.returncode,
                                         'part': part, 'brep_sha256': digest(brep.read_bytes())})
    if run.returncode not in (0, 2):
        raise ValueError('NATIVE_EXECUTION_ERROR:'+label)
    record = json.loads(run.stdout)
    if record['mode'] != mode or record['schema'] != 1 or record['occt'] != '7.8.1' or record['use_count'] != len(record['uses']):
        raise ValueError('NATIVE_MODE_MISMATCH:'+label)
    mapped = occt_libs(record['loaded_occt_libraries'])
    if mapped != build['same_resolved_runtime_libraries']:
        raise ValueError('NATIVE_ACTUAL_OCCT_MAPPING_DIFFERS_FROM_FREECAD:'+label)
    return record['uses'], run.returncode


def join_all(rows, expected):
    selection = {}
    order_keys = set()
    for row in rows:
        k = identity(row)
        order_k = (row['face'], row['wire'], row.get('use'))
        if k in selection or order_k in order_keys or k not in expected:
            raise ValueError('NATIVE_CENSUS_EXTRA_DUPLICATE_OR_REUSED_ORDER')
        selection[k] = row
        order_keys.add(order_k)
    return [{'face': k[0], 'wire': k[1], 'edge': k[2], 'formula_use_order': f['use'],
             'native_storage_order': selection.get(k, {}).get('use'),
             'native_ordered_use': selection.get(k, {}).get('ordered_use'), 'orientation': f['orientation'],
             **verdict(selection.get(k), f)} for k,f in expected.items()]


def main(binary, oldtrim, output, work):
    binary = binary.resolve(strict=True)
    output.mkdir()
    work.mkdir()
    build = runtime(binary)
    save(output/'runtime.json', build)
    old = oldtrim.read_bytes()
    if digest(old) != FORMULAS_SHA256:
        raise ValueError('NOT_ORIGINAL_72_FORMULAS')
    oldjson = json.loads(old)
    expected = expected_formulas(oldjson)
    fcstd = FCSTD.read_bytes()
    if digest(fcstd) != FCSTD_SHA:
        raise ValueError('PINNED_FCSTD_MISMATCH')
    paths = {}
    with ZipFile(FCSTD) as zipf:
        for name in PARTS:
            path = work/(name+'.Shape.brp')
            data = zipf.read(path.name)
            if digest(data) != BREP_SHA256[name]:
                raise ValueError('PINNED_BREP_MISMATCH')
            path.write_bytes(data)
            paths[name] = path
    uses, pilot_exit = native_read(binary, paths[PARTS[0]], PARTS[0], 'pilot', output, build)
    if len(uses) != 1:
        raise ValueError('PILOT_DID_NOT_RECORD_EXACTLY_ONE_USE')
    pilot = uses[0]
    pilot_formula = expected[PARTS[0]][PILOT]
    pilot_result = verdict(pilot, pilot_formula)
    tests = controls(pilot, pilot_formula) if pilot_result['status'] == 'PASS' else []
    command = [str(binary), '--projected-control']
    projected = subprocess.run(command, capture_output=True, timeout=30)
    (output/'generated-control.stdout.json').write_bytes(projected.stdout)
    (output/'generated-control.stderr.txt').write_bytes(projected.stderr)
    save(output/'generated-control.process.json', {'command': command, 'returncode': projected.returncode})
    generated = json.loads(projected.stdout)
    generated_refusal = (projected.returncode == 0 and generated['schema'] == 1
                         and generated['mode'] == 'projected-control' and generated['occt'] == '7.8.1'
                         and generated['pcurve_present'] is True and generated['stored'] is False
                         and generated['expected_refusal'] is True)
    gate = pilot_exit == 0 and generated_refusal and bool(tests) and all(v['status'] == v['expected'] for v in tests)
    save(output/'pilot.json', {'part': PARTS[0], 'reason':'fixed simple non-seam Line2d on planar Bolt',
                              'formula_sha256': FORMULAS_SHA256, 'formula': pilot_formula, 'native': pilot,
                              'result': pilot_result, 'generated_control_refused': generated_refusal, 'synthetic_controls': tests, 'expansion_permitted': gate})
    report = {'scope': 'same-build stored pcurve occurrence correspondence only',
              'formula_sha256': FORMULAS_SHA256, 'brep_sha256': BREP_SHA256, 'pilot': pilot_result,
              'expansion_permitted': gate, 'parts': {}, 'native_material_outer':'UNKNOWN',
              'native_void_inner':'UNKNOWN', 'finite_real_error':'UNKNOWN',
              'native_all_states':'UNKNOWN', 'representative_real_interval':'NOT_TESTED'}
    if not gate:
        for name, expected_rows in expected.items():
            report['parts'][name] = [dict(face=k[0], wire=k[1], edge=k[2], status='NOT_TESTED')
                                     for k in expected_rows]
        save(output/'stored-pcurve-report.json', report)
        return 2
    native_exits = {}
    for name in PARTS:
        uses, native_exits[name] = native_read(binary, paths[name], name, 'all', output, build)
        report['parts'][name] = join_all(uses, expected[name])
    report['native_expansion_exit_codes'] = native_exits
    if FCSTD.read_bytes() != fcstd or any(digest(paths[n].read_bytes()) != h for n,h in BREP_SHA256.items()):
        raise ValueError('INPUT_BYTES_CHANGED')
    save(output/'stored-pcurve-report.json', report)
    return 0 if not any(native_exits.values()) and all(r['status'] == 'PASS' for part in report['parts'].values() for r in part) else 2


if __name__ == '__main__':
    sys.exit(main(*(Path(s) for s in sys.argv[1:])))
