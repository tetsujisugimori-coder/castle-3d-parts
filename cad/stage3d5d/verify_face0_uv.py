"""Read-only five-point OCCT FaceClassifier bridge for fixed Guide Face 0.

A successful bridge confirms only the listed five finite classifier outputs
and related Face metadata. It does not assert all-point native face equality.
"""
from fractions import Fraction as Q
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, GUIDE
from one_slice import FCSTD, CONTRACT


QUERIES = (
    ('face_interior', (5, -20), 'IN'),
    ('hole_interior', (20, -20), 'OUT'),
    ('inner_boundary', (9, -20), 'ON'),
    ('outer_boundary', (0, -20), 'ON'),
    ('face_exterior', (-1, -20), 'OUT'),
)


def digest(data):
    return sha256(data).hexdigest()


def exact(v):
    if type(v) not in (int, float, str):
        raise ValueError('NON_NUMERIC_NATIVE_VALUE')
    if type(v) is float and not math.isfinite(v):
        raise ValueError('NON_FINITE_NATIVE_VALUE')
    return Q(v)


def bounds(rect):
    if set(rect) != {'low', 'high'}:
        raise ValueError('INVALID_REGION_RECT')
    return tuple(exact(x) for x in rect['low']), tuple(exact(x) for x in rect['high'])


def membership(point, outer, hole):
    o0,o1=bounds(outer);h0,h1=bounds(hole)
    u,v=map(Q,point)
    if not(o0[0] <= u <= o1[0] and o0[1] <= v <= o1[1]):
        return 'OUT'
    if h0[0] < u < h1[0] and h0[1] < v < h1[1]:
        return 'OUT'
    if (u in (o0[0],o1[0]) and o0[1] <= v <= o1[1]
            or v in (o0[1],o1[1]) and o0[0] <= u <= o1[0]
            or u in (h0[0],h1[0]) and h0[1] <= v <= h1[1]
            or v in (h0[1],h1[1]) and h0[0] <= u <= h1[0]):
        return 'ON'
    return 'IN'


def validate(native, region):
    """Classify exact five coordinates using independently calculated D values."""
    base = {'status':'FAIL','native_full_face_equality':'UNKNOWN',
            'native_material_outer':'UNKNOWN','native_void_inner':'UNKNOWN',
            'native_representative_interval':'NOT_TESTED',
            'scope':'finite OCCT FaceClassifier on fixed face, not a full-set proof'}
    try:
        if (region.get('status')!='PASS' or
                region.get('represented_face_region_equivalence')!='PASS' or
                region.get('target',{}).get('face')!=0 or
                region.get('target',{}).get('part')!=GUIDE or
                region.get('target',{}).get('saved_pcurve_uses')!=8):
            raise ValueError('PRIOR_FACE_REGION_NOT_PROVEN')
        outer,inner=region['outer_uv_mm'],region['inner_uv_mm']
        expected = [membership(pt,outer,inner) for _,pt,_ in QUERIES]
        if expected != [x[2] for x in QUERIES]:
            raise ValueError('RATIONAL_FACE_REGION_QUERIES_CHANGED')
        if (native.get('schema')!=1 or native.get('occt')!='7.8.1' or
                native.get('face_index')!=0 or native.get('face_count')!=10 or
                native.get('wire_count')!=2 or native.get('orientation')!='Reversed' or
                native.get('native_full_face_equality')!='UNKNOWN'):
            raise ValueError('NATIVE_FACE_IDENTITY_OR_SCOPE_MISMATCH')
        if native.get('natural_restriction') is not False:
            raise ValueError('NATIVE_NATURAL_RESTRICTION_NOT_FALSE')
        if native.get('surface_type')!='Geom_Plane':
            raise ValueError('UNSUPPORTED_NATIVE_SURFACE')
        tol,uv_tol=exact(native['face_tolerance_mm']),exact(native['classifier_tolerance_uv'])
        if tol < 0 or uv_tol <= 0:
            raise ValueError('BAD_NATIVE_FACE_TOLERANCES')
        if tuple(map(exact,native['uv_bounds']))!=(Q(0),Q(60),Q(-130),Q(0)):
            raise ValueError('NATIVE_UV_BOUNDS_NOT_MATCHED')
        plane=tuple(tuple(map(exact,axis)) for axis in native['surface_frame_mm'])
        prior=tuple(tuple(Q(v) for v in axis) for axis in region['plane_mm'])
        if plane!=prior:
            raise ValueError('NATIVE_SURFACE_FRAME_NOT_MATCHED')
        loc=native['surface_location']
        if (len(loc)!=4 or any(len(row)!=4 for row in loc) or
                tuple(map(exact,loc[3]))!=(0,0,0,1)):
            raise ValueError('INVALID_NATIVE_SURFACE_LOCATION')
        if native.get('sample_count')!=len(QUERIES) or len(native.get('samples',[]))!=len(QUERIES):
            raise ValueError('NOT_EXACTLY_FIVE_NATIVE_CLASSIFICATIONS')
        got=[]
        for row, (name,pt,expect) in zip(native['samples'], QUERIES):
            if (row.get('id')!=name or tuple(map(exact,row['uv']))!=pt or
                    row.get('state') not in ('IN','OUT','ON','UNKNOWN')):
                raise ValueError('NATIVE_QUERY_ID_OR_COORDINATE_MISMATCH')
            got.append({'name':name,'uv':[str(v) for v in pt],
                        'mathematical_region_state':expect,
                        'native_classifier_state':row['state'],
                        'matches':row['state']==expect})
        if not all(x['matches'] for x in got):
            return {**base,'reason':'FIVE_POINT_CLASSIFICATION_MISMATCH',
                    'observations':got,'natural_restriction':native['natural_restriction'],
                    'face_tolerance_mm_observed':str(tol),
                    'classifier_tolerance_uv_observed':str(uv_tol)}
        return {**base,'status':'PASS','reason':'FIVE_FIXED_OCCT_UV_STATES_MATCH_MODEL',
                'observations':got,'natural_restriction':False,
                'face_tolerance_mm_observed':str(tol),
                'classifier_tolerance_uv_observed':str(uv_tol),
                'uv_bounds_mm':[str(x) for x in native['uv_bounds']],
                'native_surface_frame_mm':[[str(x) for x in axis] for axis in plane]}
    except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError) as exc:
        return {**base,'reason':str(exc)}


def main(binary, brep, region_path, output):
    output.mkdir(parents=True, exist_ok=False)
    if (digest(FCSTD.read_bytes())!=FCSTD_SHA or
            digest(CONTRACT.read_bytes())!=D2_SHA or
            digest(brep.read_bytes())!=GUIDE_BREP_SHA):
        raise ValueError('PINNED_GUIDE_SOURCE_SHA_MISMATCH')
    with ZipFile(FCSTD) as z:
        if digest(z.read(GUIDE+'.Shape.brp'))!=GUIDE_BREP_SHA:
            raise ValueError('FCSTD_EMBEDDED_GUIDE_SHA_MISMATCH')
    region_raw=region_path.read_bytes()
    region=json.loads(region_raw)
    p=subprocess.run([str(binary),str(brep)],capture_output=True,check=False,timeout=30)
    (output/'native-face0.stdout.json').write_bytes(p.stdout)
    (output/'native-face0.stderr.txt').write_bytes(p.stderr)
    try:
        native=json.loads(p.stdout) if p.returncode==0 else {}
    except (ValueError,UnicodeError):
        native={}
    assessment=validate(native,region)
    assessment.update({
        'schema':'d5d-guide-face0-uv-direct-classification-v1',
        'native_exit':p.returncode,
        'input_sha256':{'fcstd':FCSTD_SHA,'d2':D2_SHA,'guide_brep':GUIDE_BREP_SHA,
                        'face_region':digest(region_raw),'native_binary':digest(binary.read_bytes())},
        'native_metadata':native,
    })
    (output/'face0-uv-report.json').write_text(json.dumps(assessment,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return 0 if p.returncode==0 and assessment['status']=='PASS' else 2


if __name__=='__main__':
    if len(sys.argv)!=5:
        raise SystemExit('usage: verify_face0_uv.py NATIVE_BINARY GUIDEBREP FACE_REGION_JSON OUTPUT_DIR')
    sys.exit(main(*(Path(v) for v in sys.argv[1:])))
