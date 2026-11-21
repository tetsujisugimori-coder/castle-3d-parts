from fractions import Fraction as Q
import unittest
from trim_correspondence import affine_link, directed_loop, check_planar_trim, material_side

class TrimTests(unittest.TestCase):
    plane = ((4,5,6), (1,0,0), (0,1,0))
    uv = ((2,3),(0,1))
    curve = ((6,8,6),(0,1,0))
    def test_exact_affine_nonzero_parameter(self):
        self.assertTrue(affine_link(self.plane,self.uv,self.curve,(7,9),(7,9)))
    def test_mismatched_parameter_domain(self):
        self.assertFalse(affine_link(self.plane,self.uv,self.curve,(7,9),(8,9)))
    def test_slope_and_offset_faults_no_snapping(self):
        for bad in (((6,8+Q(1,2**52),6),(0,1,0)),((6,8,6),(0,2,0))):
            self.assertFalse(affine_link(self.plane,self.uv,bad,(7,9),(7,9)))
    def test_directed_wire_not_unordered_edge_set(self):
        self.assertEqual(directed_loop([(1,2),(3,1),(2,3)]),[1,2,3])
        with self.assertRaises(ValueError):
            directed_loop([(1,2),(3,1),(3,2)])
    def test_outer_and_hole_scope(self):
        outer=[(0,0),(4,0),(4,4),(0,4)]
        check_planar_trim(outer,[[(1,1),(1,2),(2,2),(2,1)]])
        with self.assertRaises(ValueError):
            check_planar_trim(outer,[[(3,1),(3,2),(5,2),(5,1)]])
        with self.assertRaises(ValueError):
            check_planar_trim(outer,[[(5,1),(5,2),(6,2),(6,1)]])
    def test_material_side_reversal_or_absence(self):
        plane=((Q(0),Q(0),Q(0)),(1,0,0),(0,1,0))
        loop=[[(0,0),(2,0),(2,2),(0,2)]]
        boxes=[(0,0,-2,2,2,0)]
        self.assertEqual(material_side(plane,(0,0,1),loop,boxes)['status'],'PASS')
        self.assertEqual(material_side(plane,(0,0,-1),loop,boxes)['status'],'FAIL')
        self.assertEqual(material_side(plane,(0,0,1),loop,[])['status'],'FAIL')
