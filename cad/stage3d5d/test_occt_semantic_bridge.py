"""Exact symbolic partition tests, no native OCCT execution and no new UV samples."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from occt_semantic_bridge import analytic_d2_boundary,equality_certificate,contains,atoms_1d
from test_through_q import d2


class ExactTrimToCSGBoundaryTests(unittest.TestCase):
    def test_boundary_of_existing_four_boxes_all_point_symbolic(self):
        facets=analytic_d2_boundary(d2())
        self.assertEqual(len(facets),16)
        atoms,boundary,axes=equality_certificate(facets,facets)
        self.assertEqual(axes,[5,9,9])
        self.assertEqual(atoms,405)
        self.assertGreater(boundary,0)
        self.assertTrue(all(sum(x*x for x in normal)==1 for box,normal in facets))

    def test_missing_extra_or_misoriented_face_fails(self):
        original=analytic_d2_boundary(d2())
        faults=[]
        faults.append(original[:-1])
        flipped=deepcopy(original)
        box,_=flipped[5]
        flipped[5]=(box,(F(1),F(0),F(0)))
        faults.append(flipped)
        shifted=deepcopy(original)
        box,normal=shifted[0]
        b=list(box)
        b[1]+=1
        shifted[0]=(tuple(b),normal)
        faults.append(shifted)
        with_excess=deepcopy(original)
        with_excess.append(((F(-150),F(-90),F(1000),F(-150),F(-80),F(1030)),
                            (F(1),F(0),F(0))))
        faults.append(with_excess)
        for n,bad in enumerate(faults):
            with self.subTest(fault=n),self.assertRaisesRegex(
                    ValueError,'ORIENTED_BOUNDARY_ATOM_MISMATCH'):
                equality_certificate(bad,original)

    def test_closed_hole_boundary_is_kept_but_open_hole_removed(self):
        expected=analytic_d2_boundary(d2())
        # End annulus excludes the open central opening at its middle.
        self.assertFalse(any(contains(box,(F(-200),F(-105),F(1020)))
                             for box,normal in expected))
        # Inner material wall remains part of the boundary.
        self.assertTrue(any(contains(box,(F(-190),F(-116),F(1020)))
                            for box,normal in expected))
        self.assertTrue(any(contains(box,(F(-180),F(-116),F(1020)))
                            for box,normal in expected))

    def test_d2_hole_or_material_forgery_is_rejected(self):
        for field,value in [('moving_box',None),('obstacle_boxes',None)]:
            obj=d2()
            if field=='moving_box':
                obj['moving_box'][1]='-116'
            else:
                obj['obstacle_boxes'][0][4]='-115'
            with self.subTest(field=field),self.assertRaises(ValueError):
                analytic_d2_boundary(obj)

    def test_atoms_are_point_and_open_interval_partition(self):
        self.assertEqual(atoms_1d([F(1),F(3)]),
                         [F(0),F(1),F(2),F(3),F(4)])

if __name__=='__main__':
    unittest.main()
