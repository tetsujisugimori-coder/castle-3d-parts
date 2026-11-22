"""Negative controls for the fixed native tolerance audit. No OCCT needed."""
from copy import deepcopy
from fractions import Fraction as F
import json
import unittest

from face_region import GUIDE, GUIDE_BREP_SHA
from one_slice import CONTRACT
from verify_tolerance_audit import validate


def fixture():
    uses = [{"face": i // 6, "wire": 0, "edge": i % 24, "use": i % 6,
             "stored": True, "same_parameter": True, "same_range": True,
             "same_numeric_range": True, "degenerated": False,
             "surface_plane": True, "pcurve_line": True, "curve_line": True}
            for i in range(48)]
    # Use IDs match the original record, including all repeated edge
    # occurrences, without inventing native geometry data.
    native = {"schema": 1, "occt": "7.8.1",
              "counts": {"faces": 10, "edges": 24, "vertices": 16, "uses": 48},
              "face_tolerances_mm": [1e-7] * 10,
              "edge_tolerances_mm": [1e-7] * 24,
              "vertex_tolerances_mm": [1e-7] * 16,
              "uses": uses, "finite_total_operation_error_upper_mm": None,
              "native_full_q_void_inclusion": "UNKNOWN"}
    stored = {"parts": {GUIDE: [
        {"face": r["face"], "wire": r["wire"], "edge": r["edge"],
         "formula_use_order": r["use"], "status": "PASS"} for r in uses]}}
    trim = {"parts": {GUIDE: {"status": "PASS",
                             "faces": [{"face": i} for i in range(10)],
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

    def test_incomplete_or_duplicated_use_rejected(self):
        source = list(fixture())
        source[0]["uses"][1] = deepcopy(source[0]["uses"][0])
        with self.assertRaisesRegex(ValueError, "MISMATCH"):
            validate(*source)

    def test_nonfinite_negative_and_missing_tolerance_rejected(self):
        for value in (-1, float("nan"), float("inf")):
            source = list(fixture())
            source[0]["vertex_tolerances_mm"][0] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
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
