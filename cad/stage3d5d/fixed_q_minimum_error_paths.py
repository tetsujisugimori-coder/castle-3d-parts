"""Fixed Guide Q: prove exact disjointness by axis separations, not classifiers.

The only *additional* finite-precision obligation for a perturbed material
boundary is a one-sided enclosure of ALL actual boundary points by known
trimmed patches. OCCT tolerances are not such an enclosure.
"""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import json
import sys
from zipfile import ZipFile

from face_region import FCSTD_SHA, D2_SHA, GUIDE_BREP_SHA, TRIM_SHA, GUIDE
from one_slice import FCSTD, CONTRACT
from through_q import exact_q, face_rects, gap_sq

CENTER = (F(-190), F(-105), F(1020))


def ray_patch_gap_sq(rect, center=CENTER):
    """Exact distance^2 from a closed AABB to R={x<=cx,y=cy,z=cz}.

    The x distance is max(xmin-cx,0); the ray is unbounded to -infinity.
    A planar rectangle is represented as a degenerate 3D AABB.
    """
    if len(rect) != 6 or any(rect[i] > rect[i + 3] for i in range(3)):
        raise ValueError("BAD_RECTANGLE")
    if len(center) != 3:
        raise ValueError("BAD_RAY_CENTER")
    c = tuple(F(v) for v in center)
    xgap = max(F(rect[0]) - c[0], F(0))
    yz = [max(F(rect[i]) - c[i], c[i] - F(rect[i + 3]), F(0)) for i in (1, 2)]
    return xgap * xgap + sum(v * v for v in yz)


def gates(trim, semantic, tolerance, through, plane, contract):
    guide = trim.get("parts", {}).get(GUIDE, {})
    if (trim.get("source_fcstd_sha256") != FCSTD_SHA
            or trim.get("source_d2_sha256") != D2_SHA
            or guide.get("source_brep_sha256") != GUIDE_BREP_SHA
            or guide.get("status") != "PASS"
            or len(guide.get("faces", [])) != 10):
        raise ValueError("UNPINNED_FULL_FACE_TRIM")
    if (semantic.get("status") != "PASS"
            or semantic.get("exact_real_oriented_boundary_all_point_equality") != "PASS"
            or semantic.get("native_48_edge_use_to_saved_pcurve") != "PASS"
            or semantic.get("native_10_faces_shell_exhaustive") != "PASS"
            or semantic.get("ideal_occt_brep_semantics_solid_equals_csg") != "CONDITIONAL_PASS"
            or semantic.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("PRIOR_EXACT_SEMANTICS_NOT_ESTABLISHED")
    if (tolerance.get("status") != "PASS"
            or tolerance.get("stored_pcurve_to_3d_curve_48_occurrences") != "PASS"
            or tolerance.get("same_parameter_same_range_and_exact_affine_join") != "PASS"
            or tolerance.get("world_location_and_plane_frame") != "PASS"
            or tolerance.get("tolerances_are_total_operation_error_bounds") is not False
            or tolerance.get("finite_total_boundary_displacement_bound") != "UNKNOWN"
            or tolerance.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("NATIVE_TOLERANCE_SCOPE_NOT_ESTABLISHED")
    if (through.get("status") != "PASS"
            or through.get("exact_represented_boundary_disjoint") != "PASS"
            or through.get("exact_represented_boundary_min_distance_sq_mm2") != "1"
            or through.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("PRIOR_Q_GEOMETRY_NOT_ESTABLISHED")
    if (plane.get("status") != "PASS"
            or plane.get("native_raw_frame_equal_saved_world_planes") != "PASS"
            or plane.get("brep_extrema_total_error_status") != "UNKNOWN"
            or plane.get("native_full_q_void_inclusion") != "UNKNOWN"):
        raise ValueError("NATIVE_PLANE_SCOPE_CHANGED")
    q, _ = exact_q(contract)
    if q != tuple(map(F, (-201, -115, 1000, -179, -95, 1040))):
        raise ValueError("FIXED_QUERY_CHANGED")
    if not all(q[i] <= CENTER[i] <= q[i + 3] for i in range(3)):
        raise ValueError("CENTER_OUTSIDE_Q")
    pieces = []
    uses = []
    for face in guide["faces"]:
        rects, occs = face_rects(face)
        pieces.extend((face["face"], rect) for rect in rects)
        uses.extend(occs)
    if (len(pieces) != 16 or len(uses) != 48 or len(set(uses)) != 48
            or [sum(fi == i for fi, _ in pieces) for i in range(10)]
            != [4, 1, 1, 1, 1, 1, 1, 1, 1, 4]):
        raise ValueError("FULL_TEN_FACE_PARTITION_CHANGED")
    byface = {}
    for fi, rect in pieces:
        q_gap = gap_sq(rect, q)
        ray_gap = ray_patch_gap_sq(rect)
        if min(q_gap, ray_gap) <= 0:
            raise ValueError("Q_OR_EXTERIOR_RAY_INTERSECTS_FACE:" + str(fi))
        pair = byface.setdefault(fi, [q_gap, ray_gap])
        pair[0] = min(pair[0], q_gap)
        pair[1] = min(pair[1], ray_gap)
    total_q = min(v[0] for v in byface.values())
    total_ray = min(v[1] for v in byface.values())
    if total_q != 1 or total_ray != 1:
        raise ValueError("FIXED_CLEARANCE_NOT_ONE_MM")
    faces = []
    for i in range(10):
        qsq, raysq = byface[i]
        # A certified per-face displacement bound delta_i would be sufficient
        # if delta_i^2 < this threshold for EVERY material boundary face.
        # We DO NOT certify or synthesize any such numerical displacement.
        faces.append({"face": i, "piece_count": sum(fi == i for fi, _ in pieces),
                      "q_gap_squared_exact_mm2": str(qsq),
                      "exterior_ray_gap_squared_exact_mm2": str(raysq),
                      "required_delta_i_squared_strictly_less_than_mm2": str(min(qsq, raysq)),
                      "certified_native_delta_i_mm": None})
    return {
        "schema": "d5d-fixed-q-minimum-error-obligations-v1",
        "status": "PASS",
        "target": "fixed Guide BRep, Q and negative-x exterior half-ray",
        "exact_trimmed_face_count": 10,
        "exact_closed_patch_count": 16,
        "stored_oriented_uses": len(uses),
        "q_to_exact_boundary_min_squared_mm2": str(total_q),
        "ray_to_exact_boundary_min_squared_mm2": str(total_ray),
        "q_and_exterior_ray_exact_disjoint": "PASS",
        "per_face_strict_displacement_thresholds": faces,
        "strict_uniform_sufficient_delta_mm": "delta < 1 mm",
        "required_for_exacter_brep_geometric_q_nonintersection": [
            "complete oriented Solid/Shell/Face/Wire/Edge topology",
            "stored 48 pcurves, finite parameter domains, continuous affine 2D-3D line equality",
            "exact native world Location/Plane coefficients and true trimmed regions",
            "exact Q and negative-x exterior ray separations from every represented face",
            "regular-closed bounded material side of the one oriented closed shell"
        ],
        "only_additional_condition_for_perturbed_native_material_boundary": (
            "Every actual boundary point belongs to one of the verified face "
            "enclosures with its certified displacement delta_i strictly below "
            "the corresponding Q/ray minimum separation; no extra unaccounted "
            "boundary components; material remains bounded and regular closed."
        ),
        "not_required_for_classifier_independent_geometry": [
            "BRepExtrema minimizer convergence and its return-value error",
            "all-point FaceClassifier and SolidClassifier numerical IN/OUT/ON correctness",
            "arbitrary pcurve intersection/point-query ray selection",
            "all-point OCCT Boolean-volume residuals",
            "full operation-by-operation runtime error audit of APIs not used",
            "Bolt motion interval, other angles, 128 representative intervals"
        ],
        "required_if_trusting_numeric_API_results": [
            "separate algorithm-specific enclosure only for the chosen API and query"
        ],
        "observed_tolerance_not_total_delta": True,
        "plain_d0_evaluation_bound_not_total_delta": True,
        "native_global_or_per_face_boundary_delta_certified": "UNKNOWN",
        "native_q_all_point_geometric_nonintersection_with_finite_error": "UNKNOWN",
        "ideal_brep_semantic_q_all_point_void": "CONDITIONAL_PASS",
        "native_solidclassifier_all_point_equivalence": "UNKNOWN",
        "native_representative_interval": "NOT_TESTED",
        "scope": "Exact rational Q and half-ray separation plus minimal proof-path classification; not new numerical error guarantees"
    }


def run(trim_path, semantic_path, tolerance_path, through_path, plane_path, dest):
    dest.mkdir(parents=True, exist_ok=False)
    if sha256(FCSTD.read_bytes()).hexdigest() != FCSTD_SHA or sha256(CONTRACT.read_bytes()).hexdigest() != D2_SHA:
        raise ValueError("FIXED_SOURCE_CHANGED")
    with ZipFile(FCSTD) as z:
        if sha256(z.read(GUIDE + ".Shape.brp")).hexdigest() != GUIDE_BREP_SHA:
            raise ValueError("FIXED_GUIDE_BREP_CHANGED")
    paths = [trim_path, semantic_path, tolerance_path, through_path, plane_path]
    originals = [p.read_bytes() for p in paths]
    if sha256(originals[0]).hexdigest() != TRIM_SHA:
        raise ValueError("UNCHANGED_NATIVE_TRIM_CHANGED")
    try:
        receipt = gates(*(json.loads(b) for b in originals), json.loads(CONTRACT.read_text(encoding="utf-8")))
    except (ValueError, TypeError, KeyError, IndexError, ZeroDivisionError) as exc:
        receipt = {"status": "FAIL", "reason": str(exc),
                   "native_q_all_point_geometric_nonintersection_with_finite_error": "UNKNOWN",
                   "native_representative_interval": "NOT_TESTED"}
    receipt["inputs_sha256"] = {k: sha256(b).hexdigest() for k, b in zip(
        ("trim", "semantic", "tolerance", "through_q", "plane"), originals)}
    (dest / "narrow-error-paths.json").write_text(json.dumps(
        receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"],
                      "native_q": receipt["native_q_all_point_geometric_nonintersection_with_finite_error"]}))
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    if len(sys.argv) != 7:
        raise SystemExit("usage: fixed_q_minimum_error_paths.py TRIM SEMANTIC TOLERANCE THROUGH PLANE OUTPUT")
    sys.exit(run(*(Path(x) for x in sys.argv[1:])))
