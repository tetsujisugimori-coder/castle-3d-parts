"""Synthetic bounded controls for D2 Q and exact trimmed Guide face regions."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from through_q import exact_q, gap_sq, face_rects
from guide_q_native_helpers import check_native
from test_face_region import fixture, BOXES


def d2():
    return {'unit':'mm','parts':['GATE_Bolt','GATE_BoltGuide_Left'],
            'obstacle_boxes':deepcopy(BOXES),
            'moving_box':['-400','-115','1000','500','-95','1040']}


class GuideThroughQTests(unittest.TestCase):
    def test_q_is_existing_d2_section(self):
        q,boxes=exact_q(d2())
        self.assertEqual(q,tuple(map(F,(-201,-115,1000,-179,-95,1040))))
        self.assertEqual(len(boxes),4)
        self.assertTrue(all(gap_sq(q,b)>=1 for b in boxes))

    def test_q_fails_closed_if_cross_section_or_wall_moves(self):
        obj=d2();obj['moving_box'][1]='-116'
        with self.assertRaisesRegex(ValueError,'FIXED_D2_Q_NOT_AS_EXPECTED'):
            exact_q(obj)
        obj=d2();obj['obstacle_boxes'][0][4]='-114'
        with self.assertRaisesRegex(ValueError,'D2_Q_NOT_INSIDE_PASSAGE'):
            exact_q(obj)

    def test_exact_face_zero_hole_and_minimum_clearance(self):
        trim,_,_=fixture()
        face=trim['parts']['GATE_BoltGuide_Left']['faces'][0]
        areas,keys=face_rects(face)
        q,_=exact_q(d2())
        self.assertEqual(len(areas),4)
        self.assertEqual(len(keys),8)
        self.assertEqual(min(gap_sq(a,q) for a in areas),F(1))

    def test_an_untrimmed_end_plane_cannot_pass_as_hole(self):
        trim,_,_=fixture()
        f=deepcopy(trim['parts']['GATE_BoltGuide_Left']['faces'][0])
        f['wires'].pop()
        f['uv_bounds']=['0','60','-130','0']
        # Without an inner wire the full end rectangle enters Q.
        rects,_=face_rects(f)
        q,_=exact_q(d2())
        self.assertEqual(min(gap_sq(r,q) for r in rects),F(0))

    def test_geometry_faults_fail_closed(self):
        trim,_,_=fixture()
        face=trim['parts']['GATE_BoltGuide_Left']['faces'][0]
        for change in ('direction','normal','pcurve'):
            f=deepcopy(face)
            if change=='direction':f['wires'][0]['uses'][0]['orientation']='Reversed'
            if change=='normal':f['normal']=['1','0','0']
            if change=='pcurve':f['wires'][0]['uses'][0]['pcurve'][0][0]='1'
            with self.subTest(change=change),self.assertRaises(ValueError):
                face_rects(f)

    def test_native_observation_does_not_certify_void(self):
        q,_=exact_q(d2())
        native={'schema':1,'occt':'7.8.1','face_count':10,'solid_count':1,
                'shell_count':1,'shell_closed_flag':True,'brepcheck_solid_valid':True,
                'native_all_point_void_inclusion':'UNKNOWN',
                'q_closed_box_mm':[-201,-115,1000,-179,-95,1040],
                'one_center_point_mm':[-190,-105,1020],
                'one_center_state':'OUT','one_center_tolerance_mm':1e-7,
                'faces':[{'face_index':i,'orientation':'Forward',
                          'distance_is_done':True,'distance_solution_count':1,
                          'face_tolerance_mm':1e-7,
                          'boundary_to_q_observed_distance_mm':1.0} for i in range(10)]}
        rows=[{'exact_boundary_to_q_distance_sq_mm2':'1'} for i in range(10)]
        faces=[{'orientation':'Forward'} for i in range(10)]
        self.assertEqual(check_native(native,q,rows,faces)['all_point_certified_native_void'],'UNKNOWN')
        broken=deepcopy(native);broken['faces'][4]['boundary_to_q_observed_distance_mm']=0
        with self.assertRaises(ValueError):
            check_native(broken,q,rows,faces)
        broken=deepcopy(native);broken['one_center_state']='IN'
        with self.assertRaises(ValueError):
            check_native(broken,q,rows,faces)


if __name__=='__main__':
    unittest.main()
