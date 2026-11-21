"""Bound only what the fixed Guide Face 0 evidence can mathematically bound.

This is NOT a bound for OCCT's numerical classifier. In particular,
Precision::PConfusion(), Face tolerance and vertex/edge tolerance are not an
a priori enclosure of all arithmetic and algorithmic classification errors.
"""
from fractions import Fraction as Q
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE
from one_slice import FCSTD, CONTRACT
from verify_face0_uv import QUERIES, membership


def rational(x):
    if isinstance(x, bool) or type(x) not in (int, float, str, Q):
        raise ValueError("NON_NUMERIC_RECORDED_VALUE")
    if type(x) is float and not math.isfinite(x):
        raise ValueError("NONFINITE_RECORDED_VALUE")
    return Q(x)


def exact_binary64(x):
    v = rational(x)
    try:
        n = float(v)
    except (OverflowError, ValueError) as exc:
        raise ValueError("NOT_FINITE_BINARY64_REPRESENTABLE") from exc
    return math.isfinite(n) and Q(n) == v


def flatten(x):
    if isinstance(x, dict):
        for value in x.values():
            yield from flatten(value)
    elif isinstance(x, (list, tuple)):
        for value in x:
            yield from flatten(value)
    elif type(x) in (str, int, float, Q):
        yield x
    else:
        raise ValueError("UNSUPPORTED_RECORDED_COEFFICIENT")


def record_coefficients(face, native):
    """Only actual 8 stored-pcurve occurrences, plane and fixed native frame."""
    if face.get("face") != 0 or face.get("status") != "PASS" or len(face.get("wires", [])) != 2:
        raise ValueError("FACE_ZERO_NOT_PROVEN")
    values = list(flatten(face["plane"]))
    for w in face["wires"]:
        if len(w.get("uses", [])) != 4:
            raise ValueError("FACE_ZERO_NOT_EIGHT_USES")
        for use in w["uses"]:
            if use.get("represented_affine_link") != "PASS":
                raise ValueError("FACE_ZERO_AFFINE_LINK_UNVERIFIED")
            for field in ("pcurve", "curve", "pcurve_range", "curve_range", "directed_uv", "directed_3d"):
                values += list(flatten(use[field]))
            if "segment_intrinsic_range" in use:
                values += list(flatten(use["segment_intrinsic_range"]))
    values += list(flatten(native["surface_location"]))
    values += list(flatten(native["surface_frame_mm"]))
    values += list(flatten(native["uv_bounds"]))
    for s in native["samples"]:
        values += list(flatten(s["uv"]))
    if not values or not all(exact_binary64(v) for v in values):
        raise ValueError("BINARY64_INPUT_QUANTIZATION_NOT_ZERO")
    return len(values)


def finite_segments(face):
    edges = []
    for wire in face["wires"]:
        for use in wire["uses"]:
            a, b = tuple(tuple(rational(v) for v in p) for p in use["directed_uv"])
            if a == b or sum(a[i] != b[i] for i in (0, 1)) != 1:
                raise ValueError("NON_RECTILINEAR_OR_DEGENERATE_EDGE")
            edges.append((a,b))
    if len(edges) != 8:
        raise ValueError("EXPECTED_EIGHT_SEGMENTS")
    return edges


def distance_linf_to_segment(pt, seg):
    """Exact L-infinity distance to a closed horizontal/vertical segment."""
    p=tuple(rational(x) for x in pt)
    a,b=seg
    lo=(min(a[0],b[0]),min(a[1],b[1]))
    hi=(max(a[0],b[0]),max(a[1],b[1]))
    return max(max(lo[i]-p[i],p[i]-hi[i],Q(0)) for i in (0,1))


def mathematical_margin(point, edges):
    """Distance to the FULL ideal domain boundary; no OCCT call."""
    return min(distance_linf_to_segment(point,e) for e in edges)


def analyze(region, native, observed, trim):
    if (region.get("status") != "PASS"
            or region.get("represented_face_region_equivalence") != "PASS"
            or region.get("target",{}).get("face") != 0
            or region.get("target",{}).get("part") != GUIDE):
        raise ValueError("EARLIER_EXACT_FACE_REGION_NOT_PASS")
    if (observed.get("status") != "PASS"
            or observed.get("native_full_face_equality") != "UNKNOWN"
            or observed.get("native_metadata") != native):
        raise ValueError("NATIVE_FIVE_POINT_REPORT_NOT_IDENTICAL")
    if (native.get("occt") != "7.8.1" or native.get("face_index") != 0
            or native.get("sample_count") != 5 or len(native.get("samples",[])) != 5
            or native.get("natural_restriction") is not False):
        raise ValueError("FIXED_NATIVE_FACE_NOT_PROVEN")
    if (trim.get("source_fcstd_sha256") != FCSTD_SHA
            or trim.get("source_d2_sha256") != D2_SHA
            or trim.get("parts",{}).get(GUIDE,{}).get("status") != "PASS"):
        raise ValueError("FIXED_TRIM_INPUT_CHANGED")
    face=next((f for f in trim["parts"][GUIDE]["faces"] if f["face"] == 0),None)
    if face is None:
        raise ValueError("FIXED_FACE_MISSING")
    exact_count=record_coefficients(face,native)
    if (tuple(tuple(rational(x) for x in v) for v in region["plane_mm"])
            !=tuple(tuple(rational(x) for x in v) for v in native["surface_frame_mm"])):
        raise ValueError("NATIVE_FRAME_NOT_REPRESENTED_FRAME")
    u,v=tuple(tuple(rational(x) for x in vv) for vv in region["plane_mm"][1:])
    if sum(x*x for x in u)!=1 or sum(x*x for x in v)!=1 or sum(u[i]*v[i] for i in range(3))!=0:
        raise ValueError("NOT_UNIT_ISOMETRIC_SURFACE")
    segments=finite_segments(face)
    obs=[]
    for i,(name,point,expected) in enumerate(QUERIES):
        record=native["samples"][i]
        if (record.get("id")!=name or tuple(rational(x) for x in record["uv"])!=point
                or record.get("state")!=expected
                or membership(point,region["outer_uv_mm"],region["inner_uv_mm"])!=expected):
            raise ValueError("FIXED_NATIVE_OR_MODEL_POINT_CHANGED")
        margin=mathematical_margin(point,segments)
        obs.append({
            "id":name,
            "uv_mm":[str(Q(x)) for x in point],
            "state":expected,
            "exact_distance_to_model_boundary_Linf_mm":str(margin),
            "ideal_state_unchanged_for_query_coordinate_error_strictly_less_than_mm":
                str(margin) if margin>0 else None,
            "positive_robust_radius_exists":margin>0,
        })
    tol=rational(native["classifier_tolerance_uv"])
    face_tol=rational(native["face_tolerance_mm"])
    if tol<=0 or face_tol<0:
        raise ValueError("BAD_REPORTED_TOLERANCE")
    return {
        "schema":"d5d-guide-face0-conditional-error-bounds-v1",
        "status":"PASS",
        "scope":"exact BRep-recorded dyadic numbers and ideal ring classification robustness only",
        "recorded_binary64_input_count":exact_count,
        "recorded_binary64_input_quantization_error_upper_mm":"0",
        "ideal_UV_to_3D_distance_scale":"1",
        "native_classifier_parameter_tolerance_observed_exact":str(tol),
        "native_face_tolerance_observed_exact_mm":str(face_tol),
        "nominal_PConfusion_decimal":"1/1000000000",
        "nominal_Confusion_decimal_mm":"1/10000000",
        "input_classifier_tolerance_decimal_rounding_absolute_mm":
            str(abs(tol-Q(1,1000000000))),
        "input_face_tolerance_decimal_rounding_absolute_mm":
            str(abs(face_tol-Q(1,10000000))),
        "query_margins":obs,
        "native_classifier_total_rounding_error_upper_mm":None,
        "native_classifier_total_rounding_error_status":"UNKNOWN",
        "native_effective_tolerance_band_upper_mm":None,
        "native_effective_tolerance_band_status":"UNKNOWN",
        "native_real_face_all_point_equivalence":"UNKNOWN",
        "native_material_outer":"UNKNOWN",
        "native_void_inner":"UNKNOWN",
        "native_representative_interval":"NOT_TESTED",
        "explanation":"Input encoding bound 0 and ideal distance margins cannot bound OCCT intersection / transition / tolerance propagation. 1e-9 input tolerance is not a global error certificate; vertex/edge tolerance and numeric branches need independent audit.",
    }


def main(region_path, native_path, five_path, trim_path, output):
    output.mkdir(parents=True,exist_ok=False)
    fcstd=FCSTD.read_bytes()
    if sha256(fcstd).hexdigest()!=FCSTD_SHA or sha256(CONTRACT.read_bytes()).hexdigest()!=D2_SHA:
        raise ValueError("PINNED_CAD_OR_D2_INPUT_CHANGED")
    with ZipFile(FCSTD) as z:
        if sha256(z.read(GUIDE+".Shape.brp")).hexdigest()!=GUIDE_BREP_SHA:
            raise ValueError("FIXED_GUIDE_BREP_CHANGED")
    raw=[p.read_bytes() for p in (region_path,native_path,five_path,trim_path)]
    if sha256(raw[3]).hexdigest()!=TRIM_SHA:
        raise ValueError("UNCHANGED_72_FORMULA_SOURCE_MISMATCH")
    try:
        result=analyze(*(json.loads(s) for s in raw))
    except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError,OverflowError) as e:
        result={"status":"FAIL","reason":str(e),
                "native_classifier_total_rounding_error_status":"UNKNOWN",
                "native_real_face_all_point_equivalence":"UNKNOWN",
                "native_representative_interval":"NOT_TESTED"}
    result["inputs_sha256"]={key:sha256(content).hexdigest() for key,content in
                             zip(("face_region","native_raw","five_point_report","trim"),raw)}
    (output/"face0-error-bounds.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    return 0 if result["status"]=="PASS" else 2


if __name__=="__main__":
    if len(sys.argv)!=6:
        raise SystemExit("usage: face0_error_bounds.py REGION RAW_NATIVE FIVE_REPORT TRIM OUTPUT")
    sys.exit(main(*(Path(s) for s in sys.argv[1:])))
