"""Negative controls for the fixed native tolerance audit. No OCCT needed."""
from copy import deepcopy
from fractions import Fraction as F
import json
import unittest

from face_region import GUIDE, GUIDE_BREP_SHA
from one_slice import CONTRACT
from verify_tolerance_audit import validate


def fixture():
    uses = []
    faces = []
    for face_index in range(10):
        wires = []
        for wire_index in range(2 if face_index in (0, 9) else 1):
            trim_uses = []
            for use_index in range(4):
                i = len(uses)
                edge = i % 24
                uses.append({
                    "face": face_index, "wire": wire_index, "edge": edge,
                    "use": use_index, "native_storage_use": use_index,
                    "stored": True, "same_parameter": True, "same_range": True,
                    "same_numeric_range": True, "degenerated": False,
                    "surface_plane": True, "pcurve_line": True, "curve_line": True,
                })
                trim_uses.append({
                    "edge": edge, "use": use_index, "orientation": "Forward",
                    "represented_affine_link": "PASS",
                    "pcurve": [[str(i), "0"], ["1", "0"]],
                    "curve": [[str(i), "0", "0"], ["1", "0", "0"]],
                    "pcurve_range": ["0", "1"], "curve_range": ["0", "1"],
                    "directed_uv": [[str(i), "0"], [str(i + 1), "0"]],
                    "directed_3d": [[str(i), "0", "0"], [str(i + 1), "0", "0"]],
                })
            wires.append({"wire": wire_index, "uses": trim_uses})
        faces.append({
            "face": face_index, "status": "PASS",
            "plane": [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]],
            "wires": wires,
        })
    native = {"schema": 1, "occt": "7.8.1",
              "counts": {"faces": 10, "edges": 24, "vertices": 16, "uses": 48},
              "face_tolerances_mm": [1e-7] * 10,
              "edge_tolerances_mm": [1e-7] * 24,
              "vertex_tolerances_mm": [1e-7] * 16,
              "uses": uses, "finite_total_operation_error_upper_mm": None,
              "native_full_q_void_inclusion": "UNKNOWN"}
    stored = {"parts": {GUIDE: [
        {"face": r["face"], "wire": r["wire"], "edge": r["edge"],
         "formula_use_order": r["use"], "native_storage_order": r["native_storage_use"],
         "native_ordered_use": r["use"], "status": "PASS"} for r in uses]}}
    trim = {"parts": {GUIDE: {"status": "PASS", "faces": faces,
                             "source_brep_sha256": GUIDE_BREP_SHA}}}
    sem = {"status": "PASS",
           "exact_real_oriented_boundary_all_point_equality": "PASS",
           "ideal_occt_brep_semantics_solid_equals_csg": "CONDITIONAL_PASS",
           "native_full_q_void_inclusion": "UNKNOWN"}
    plane = {"status": "PASS", "native_raw_frame_equal_saved_world_planes": "PASS",
             "model_boundary_distance_to_q_exact_mm": "1",
             "brep_extrema_total_error_status": "UNKNOWN",
             "max_euclidean_eval_roundoff_upper_exact_mm": "1/1000000000000"}
    through = {"status": "PASS", "exact_represented_boundary_disjoint": "PASS",
               "exact_d2_material_disjoint": "PASS",
               "native_full_q_void_inclusion": "UNKNOWN"}
    return native, stored, trim, sem, plane, through, json.loads(CONTRACT.read_text())


class ToleranceAuditContractTests(unittest.TestCase):
    def test_known_model_q_and_separate_unknown_native(self):
        report = validate(*fixture())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["q_center_to_negative_x_infinity_model_ray"], "PASS")
        self.assertEqual(report["q_all_points_ideal_occt_brep_void"], "CONDITIONAL_PASS")
        self.assertEqual(report["native_full_q_void_inclusion"], "UNKNOWN")
        self.assertIsNone(report["required_unknown_total_boundary_displacement_delta_mm"])
        self.assertEqual(F(report["conditional_direct_plane_evaluation_distance_lower_mm"]),
                         F(1) - F(1, 10**12))

    def test_false_stored_or_same_flags_rejected(self):
        for key in ("stored", "same_parameter", "same_range",
                    "same_numeric_range", "pcurve_line", "curve_line"):
            source = list(fixture())
            source[0]["uses"][0][key] = False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,
                     "NATIVE_CURVE_REPRESENTATION_NOT_VERIFIED"):
                validate(*source)

    def test_mutated_pcurve_coefficient_rejected_despite_pass_label(self):
        source = list(fixture())
        source[2]["parts"][GUIDE]["faces"][0]["wires"][0]["uses"][0]["pcurve"][0][0] = "999"
        with self.assertRaisesRegex(ValueError, "TRIM_PCURVE_3D_AFFINE_MISMATCH"):
            validate(*source)

    def test_native_storage_ordinal_999_rejected_despite_pass_labels(self):
        source = list(fixture())
        source[0]["uses"][0]["native_storage_use"] = 999
        with self.assertRaisesRegex(ValueError, "NATIVE_STORED_USE_ORDER_MISMATCH"):
            validate(*source)

    def test_normal_storage_order_can_differ_from_wire_use_order(self):
        source = list(fixture())
        # Real BRep storage can be a permutation of ordered edge uses.
        source[0]["uses"][0]["native_storage_use"] = 3
        source[0]["uses"][3]["native_storage_use"] = 0
        source[1]["parts"][GUIDE][0]["native_storage_order"] = 3
        source[1]["parts"][GUIDE][3]["native_storage_order"] = 0
        self.assertEqual(validate(*source)["status"], "PASS")

    def test_duplicate_native_storage_slot_rejected_even_if_stored_record_matches(self):
        source = list(fixture())
        source[0]["uses"][0]["native_storage_use"] = 1
        source[1]["parts"][GUIDE][0]["native_storage_order"] = 1
        with self.assertRaisesRegex(ValueError, "DUPLICATED_NATIVE_STORAGE_USE"):
            validate(*source)

    def test_incomplete_or_duplicated_use_rejected(self):
        source = list(fixture())
        source[0]["uses"][1] = deepcopy(source[0]["uses"][0])
        with self.assertRaisesRegex(ValueError, "DUPLICATED|MISMATCH"):
            validate(*source)

    def test_nonfinite_negative_and_missing_tolerance_rejected(self):
        for value in (-1, float("nan"), float("inf")):
            source = list(fixture())
            source[0]["vertex_tolerances_mm"][0] = value
            with self.subTest(value=repr(value)), self.assertRaises((ValueError, OverflowError)):
                validate(*source)
        source = list(fixture())
        source[0]["face_tolerances_mm"].pop()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_TOLERANCE"):
            validate(*source)

    def test_large_tolerance_is_not_promoted_to_error_bound(self):
        source = list(fixture())
        source[0]["edge_tolerances_mm"][1] = 2
        report = validate(*source)
        self.assertFalse(report["tolerance_smaller_than_model_clearance"])
        self.assertEqual(report["finite_total_boundary_displacement_bound"], "UNKNOWN")
        self.assertEqual(report["native_full_q_void_inclusion"], "UNKNOWN")

    def test_unfounded_native_promotion_rejected(self):
        for field, value in (("native_full_q_void_inclusion", "PASS"),
                             ("finite_total_operation_error_upper_mm", 0)):
            source = list(fixture())
            source[0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError,
                     "UNSUPPORTED_NATIVE_ERROR_PROMOTION"):
                validate(*source)

    def test_q_or_prior_semantic_mutation_rejected(self):
        source = list(fixture())
        source[6]["obstacle_boxes"][0][4] = "-115"
        with self.assertRaises(ValueError):
            validate(*source)
        source = list(fixture())
        source[3]["exact_real_oriented_boundary_all_point_equality"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "SEMANTIC_PRECONDITION"):
            validate(*source)


if __name__ == "__main__":
    unittest.main()
