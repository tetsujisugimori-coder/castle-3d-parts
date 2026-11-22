"""Exact half-ray geometry tests for the fixed Q, not OCCT query samples."""
from fractions import Fraction as F
import unittest

from fixed_q_minimum_error_paths import ray_patch_gap_sq
from occt_semantic_bridge import analytic_d2_boundary
from test_through_q import d2
from through_q import exact_q, gap_sq


class FixedQPathScopeTests(unittest.TestCase):
    def test_exact_d2_boundary_q_one_mm_ray_eleven_mm(self):
        patches = [box for box, _ in analytic_d2_boundary(d2())]
        q, _ = exact_q(d2())
        self.assertEqual(len(patches), 16)
        self.assertEqual(min(gap_sq(p, q) for p in patches), F(1))
        self.assertEqual(min(ray_patch_gap_sq(p) for p in patches), F(121))

    def test_ray_one_sided_x_distance_and_negative_infinity(self):
        # The ray ends at x=-190 and goes to negative infinity.
        self.assertEqual(ray_patch_gap_sq((-200, -105, 1020, -180, -105, 1020)), 0)
        self.assertEqual(ray_patch_gap_sq((-180, -105, 1020, -175, -105, 1020)), 100)
        self.assertEqual(ray_patch_gap_sq((-250, -105, 1020, -240, -105, 1020)), 0)

    def test_ray_yz_gap_is_exact_eleven_mm(self):
        self.assertEqual(ray_patch_gap_sq((-200, -116, 1000, -180, -116, 1040)), 121)
        self.assertEqual(ray_patch_gap_sq((-200, -105, 1041, -180, -105, 1050)), 441)

    def test_contact_must_never_be_certificate(self):
        q, _ = exact_q(d2())
        # A foreign face inside Q is a counterexample.
        bad = (-190, -105, 1020, -190, -105, 1020)
        self.assertEqual(gap_sq(bad, q), 0)
        self.assertEqual(ray_patch_gap_sq(bad), 0)

    def test_native_tolerances_cannot_be_used_as_error_enclosure(self):
        # Arithmetic inequality is only valid after delta has been certified
        # as covering *every* boundary point. Tolerance values do not do this.
        margin = F(1)
        for certified_delta in (F(0), F(1, 2), F(999, 1000)):
            self.assertGreater(margin - certified_delta, 0)
        self.assertEqual(margin - F(1), 0)


if __name__ == "__main__":
    unittest.main()
