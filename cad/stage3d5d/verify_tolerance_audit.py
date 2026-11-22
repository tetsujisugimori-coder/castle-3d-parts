"""Read-only native tolerance audit; it never treats OCCT tolerances as error bounds.

Only a validated total geometric displacement enclosure delta < 1 mm could
convert the model's 1 mm margin into a finite-error nonintersection certificate.
"""
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE
from trim_correspondence import affine_link
from one_slice import FCSTD, CONTRACT
from through_q import exact_q


def nonnegative(recorded):
    if type(recorded) not in (float, int, str):
        raise ValueError("NON_NUMERIC_NATIVE_TOLERANCE")
    value = F(recorded)
    if value < 0:
        raise ValueError("NEGATIVE_NATIVE_TOLERANCE")
    return value



def verified_trim_curve_uses(faces):
    """Recompute each recorded 2D->3D affine identity; never trust PASS labels."""
    keys = set()
    for face_index, face in enumerate(faces):
        if face.get("face") != face_index or face.get("status") != "PASS":
            raise ValueError("TRIM_FACE_IDENTITY_OR_STATUS_CHANGED")
        try:
            plane = tuple(tuple(F(x) for x in axis) for axis in face["plane"])
            if len(plane) != 3 or any(len(axis) != 3 for axis in plane):
                raise ValueError("INVALID_TRIM_PLANE")
            for wire_index, wire in enumerate(face["wires"]):
                if wire.get("wire") != wire_index:
                    raise ValueError("TRIM_WIRE_IDENTITY_CHANGED")
                for use in wire["uses"]:
                    key = (face_index, wire_index, use["edge"], use["use"])
                    if (any(type(k) is not int or k < 0 for k in key)
                            or key in keys):
                        raise ValueError("DUPLICATE_OR_INVALID_TRIM_USE")
                    keys.add(key)
                    if use.get("represented_affine_link") != "PASS":
                        raise ValueError("TRIM_AFFINE_LABEL_NOT_PASS")
                    pc = tuple(tuple(F(x) for x in axis) for axis in use["pcurve"])
                    curve = tuple(tuple(F(x) for x in axis) for axis in use["curve"])
                    prange = tuple(F(x) for x in use["pcurve_range"])
                    crange = tuple(F(x) for x in use["curve_range"])
                    if (len(pc) != 2 or any(len(axis) != 2 for axis in pc)
                            or len(curve) != 2 or any(len(axis) != 3 for axis in curve)
                            or not affine_link(plane, pc, curve, prange, crange)):
                        raise ValueError("TRIM_PCURVE_3D_AFFINE_MISMATCH")
                    # Cross-check directed endpoint witnesses as well as coefficients.
                    a, b = prange
                    uv = [tuple(pc[0][i] + t * pc[1][i] for i in range(2))
                          for t in (a, b)]
                    xyz = [tuple(curve[0][i] + t * curve[1][i] for i in range(3))
                           for t in (a, b)]
                    ori = use["orientation"]
                    if ori == "Reversed":
                        uv.reverse()
                        xyz.reverse()
                    elif ori != "Forward":
                        raise ValueError("UNSUPPORTED_TRIM_EDGE_ORIENTATION")
                    if (uv != [tuple(F(x) for x in pair) for pair in use["directed_uv"]]
                            or xyz != [tuple(F(x) for x in point) for point in use["directed_3d"]]):
                        raise ValueError("TRIM_DIRECTED_ENDPOINTS_MISMATCH")
        except (KeyError, TypeError, IndexError, ZeroDivisionError, OverflowError) as exc:
            raise ValueError("INCOMPLETE_TRIM_AFFINE_SOURCE") from exc
    if len(keys) != 48:
        raise ValueError("INCOMPLETE_TRIM_48_USE_CENSUS")
    return keys


def validate(native, stored, trim, semantic, plane, through, contract):
    counts = native.get("counts")
    if (native.get("schema") != 1 or native.get("occt") != "7.8.1"
            or counts != {"faces": 10, "edges": 24, "vertices": 16, "uses": 48}):
        raise ValueError("NATIVE_CENSUS_CHANGED")
    tolerances = {}
    for kind, size in (("face", 10), ("edge", 24), ("vertex", 16)):
        data = native.get(kind + "_tolerances_mm", [])
        if not isinstance(data, list) or len(data) != size:
            raise ValueError("INCOMPLETE_TOLERANCE_INVENTORY:" + kind)
        tolerances[kind] = list(map(nonnegative, data))
    if (native.get("finite_total_operation_error_upper_mm") is not None
            or native.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("UNSUPPORTED_NATIVE_ERROR_PROMOTION")
    g = trim.get("parts", {}).get(GUIDE, {})
    if (g.get("status") != "PASS" or len(g.get("faces", [])) != 10
            or g.get("source_brep_sha256") != GUIDE_BREP_SHA):
        raise ValueError("UNPINNED_GUIDE_TRIM_INPUT")
    stored_rows = stored.get("parts", {}).get(GUIDE, [])
    if len(stored_rows) != 48 or any(row.get("status") != "PASS" for row in stored_rows):
        raise ValueError("STORED_PCURVE_PROOF_NOT_PASS")
    recorded_keys = [(r["face"], r["wire"], r["edge"], r["formula_use_order"])
                     for r in stored_rows]
    if len(set(recorded_keys)) != 48:
        raise ValueError("DUPLICATED_ORIGINAL_CURVE_USE")
    trim_keys = verified_trim_curve_uses(g["faces"])
    if trim_keys != set(recorded_keys):
        raise ValueError("TRIM_TO_STORED_48_USE_MISMATCH")
    stored_by_key = dict(zip(recorded_keys, stored_rows))
    uses = native.get("uses")
    if not isinstance(uses, list) or len(uses) != 48:
        raise ValueError("INCOMPLETE_NATIVE_USE_INVENTORY")
    use_keys = []
    for r in uses:
        key = (r["face"], r["wire"], r["edge"], r["use"])
        if any(type(n) is not int or n < 0 for n in key):
            raise ValueError("NONINTEGER_USE_ID")
        if key[0] >= 10 or key[2] >= 24:
            raise ValueError("OUT_OF_RANGE_USE_ID")
        original = stored_by_key.get(key)
        if original is None:
            raise ValueError("NATIVE_USE_MISSING_FROM_STORED_RECORD")
        # Ordered wire use and raw TopoDS storage order are NOT interchangeable.
        if (type(r.get("native_storage_use")) is not int
                or not 0 <= r["native_storage_use"] < 4
                or type(original.get("native_storage_order")) is not int
                or original["native_storage_order"] != r["native_storage_use"]
                or original.get("native_ordered_use") != r["use"]):
            raise ValueError("NATIVE_STORED_USE_ORDER_MISMATCH")
        for field in ("stored", "same_parameter", "same_range", "same_numeric_range",
                      "surface_plane", "pcurve_line", "curve_line"):
            if r.get(field) is not True:
                raise ValueError("NATIVE_CURVE_REPRESENTATION_NOT_VERIFIED:" + field)
        if r.get("degenerated") is not False:
            raise ValueError("DEGENERATED_NATIVE_EDGE")
        use_keys.append(key)
    if len(set(use_keys)) != 48 or set(use_keys) != set(recorded_keys):
        raise ValueError("NATIVE_OR_STORED_48_USE_MISMATCH")
    if (semantic.get("status") != "PASS"
            or semantic.get("exact_real_oriented_boundary_all_point_equality") != "PASS"
            or semantic.get("ideal_occt_brep_semantics_solid_equals_csg") != "CONDITIONAL_PASS"
            or semantic.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("EXACT_SOLID_SEMANTIC_PRECONDITION_MISSING")
    if (plane.get("status") != "PASS"
            or plane.get("native_raw_frame_equal_saved_world_planes") != "PASS"
            or plane.get("model_boundary_distance_to_q_exact_mm") != "1"
            or plane.get("brep_extrema_total_error_status") != "UNKNOWN"):
        raise ValueError("PLANE_FRAME_OR_LIMITATION_MISSING")
    if (through.get("status") != "PASS"
            or through.get("exact_represented_boundary_disjoint") != "PASS"
            or through.get("exact_d2_material_disjoint") != "PASS"
            or through.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("THROUGH_Q_PRECONDITION_MISSING")
    q, boxes = exact_q(contract)
    if tuple(q) != tuple(F(n) for n in (-201, -115, 1000, -179, -95, 1040)):
        raise ValueError("FIXED_Q_CHANGED")
    # Y,Z of the entire Q rectangle remain in the rectangular void for
    # any X; the center ray extends to x=-infinity without hitting D2 M.
    if any(not (q[1] > b[4] or q[4] < b[1] or
                q[2] > b[5] or q[5] < b[2]) for b in boxes):
        raise ValueError("Q_CROSS_SECTION_NOT_FREE_OF_D2")
    d0_error = nonnegative(plane["max_euclidean_eval_roundoff_upper_exact_mm"])
    if d0_error >= 1:
        raise ValueError("PLANE_EVALUATION_LOST_POSITIVE_CLEARANCE")
    max_tol = max(x for values in tolerances.values() for x in values)
    return {
        "schema": "d5d-guide-native-tolerance-and-q-scope-v1",
        "status": "PASS",
        "scope": "native tolerance inventory / 48-use representation join / conditional ideal Q proof",
        "occt": "7.8.1",
        "native_face_tolerances_mm": [str(x) for x in tolerances["face"]],
        "native_edge_tolerances_mm": [str(x) for x in tolerances["edge"]],
        "native_vertex_tolerances_mm": [str(x) for x in tolerances["vertex"]],
        "max_observed_native_tolerance_mm": str(max_tol),
        "tolerance_smaller_than_model_clearance": max_tol < F(1),
        "tolerances_are_total_operation_error_bounds": False,
        "stored_pcurve_to_3d_curve_48_occurrences": "PASS",
        "same_parameter_same_range_and_exact_affine_join": "PASS",
        "world_location_and_plane_frame": "PASS",
        "known_direct_plane_evaluation_error_upper_mm": str(d0_error),
        "conditional_direct_plane_evaluation_distance_lower_mm": str(F(1) - d0_error),
        "model_boundary_to_q_distance_mm": "1",
        "required_unknown_total_boundary_displacement_delta_mm": None,
        "sufficient_condition_for_nonintersection": "certified total boundary displacement delta < 1 mm",
        "finite_total_boundary_displacement_bound": "UNKNOWN",
        "finite_real_native_q_nonintersection": "UNKNOWN",
        "q_model_cross_section_disjoint_from_all_four_boxes": "PASS",
        "q_center_to_negative_x_infinity_model_ray": "PASS",
        "q_all_points_ideal_csg_void": "PASS",
        "q_all_points_ideal_occt_brep_void": "CONDITIONAL_PASS",
        "native_solidclassifier_all_point_equivalence": "UNKNOWN",
        "native_full_q_void_inclusion": "UNKNOWN",
        "native_representative_interval": "NOT_TESTED",
        "unbounded_numeric_paths": [
            "pcurve parameter generation and curve evaluation rounding beyond stored-coefficient affine model",
            "numerical trim classification near wires and vertices",
            "finite tolerance propagation and solid/face classifier ray intersections",
            "global finite-error enclosure of native material boundary relative to the ideal oriented shell"
        ],
        "interpretation": "Tolerance values describe BRep representation consistency. They cannot be subtracted from the 1 mm gap as though they bounded all OCCT arithmetic. The exact D2/ideal BRep complement and exterior ray are classifier-independent only under the recorded ideal semantic conditions."
    }


def run(native_path, stored_path, trim_path, semantic_path, plane_path, through_path, output):
    output.mkdir(parents=True, exist_ok=False)
    if sha256(FCSTD.read_bytes()).hexdigest() != FCSTD_SHA:
        raise ValueError("SOURCE_FCSTD_CHANGED")
    if sha256(CONTRACT.read_bytes()).hexdigest() != D2_SHA:
        raise ValueError("SOURCE_D2_CHANGED")
    with ZipFile(FCSTD) as z:
        if sha256(z.read(GUIDE + ".Shape.brp")).hexdigest() != GUIDE_BREP_SHA:
            raise ValueError("SOURCE_GUIDE_BREP_CHANGED")
    paths = (native_path, stored_path, trim_path, semantic_path, plane_path, through_path)
    contents = [p.read_bytes() for p in paths]
    if sha256(contents[2]).hexdigest() != TRIM_SHA:
        raise ValueError("PINNED_TRIM_SOURCE_SHA_CHANGED")
    try:
        report = validate(*(json.loads(raw) for raw in contents),
                          json.loads(CONTRACT.read_text(encoding="utf-8")))
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, ZeroDivisionError) as e:
        report = {"status": "FAIL", "reason": str(e),
                  "native_full_q_void_inclusion": "UNKNOWN",
                  "native_representative_interval": "NOT_TESTED"}
    report["inputs_sha256"] = dict(zip(("native_tolerances", "stored_pcurve", "trim",
                                        "semantic_bridge", "plane_roundoff", "through_q"),
                                       (sha256(s).hexdigest() for s in contents)))
    (output / "native-tolerance-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "max_native_tolerance_mm": report.get("max_observed_native_tolerance_mm"),
                      "finite_native_q": report["native_full_q_void_inclusion"]}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    if len(sys.argv) != 8:
        raise SystemExit("usage: verify_tolerance_audit.py NATIVE STORED TRIM SEMANTIC PLANE THROUGH OUT")
    sys.exit(run(*(Path(p) for p in sys.argv[1:])))
