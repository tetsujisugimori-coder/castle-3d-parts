"""Portable synthetic guards; does not run FreeCAD or certify native geometry."""
import copy
from fractions import Fraction as Q
import unittest
from one_slice import target, interpretation, REF


def fixture():
    return {
        'schema':'aabb-union-translation-v1', 'unit':'mm',
        'parts':['GATE_Bolt','GATE_BoltGuide_Left'],
        'door_degrees':'0','range':['0','140'],
        'moving_velocity':['1','0','0'],'obstacle_velocity':['0','0','0'],
        'moving_box':['-400','-115','1000','500','-95','1040'],
        'obstacle_boxes':[
            ['-200','-130','990','-180','-116','1050'],
            ['-200','-94','990','-180','0','1050'],
            ['-200','-116','990','-180','-94','999'],
            ['-200','-116','1041','-180','-94','1050'],
        ],
    }


class TargetTests(unittest.TestCase):
    def test_first_leaf_arithmetic(self):
        r=target(fixture())
        self.assertEqual(REF,Q(35,64))
        self.assertEqual(r['movement_bound_mm'],'35/64')
        self.assertEqual(r['conditional_model_clearance_lower_mm'],'29/64')
        self.assertEqual(r['model_certificate'],'PASS')
        self.assertEqual(r['real_cad_certificate'],'NOT_TESTED')

    def test_channel_contact_rejected(self):
        d=fixture();d['moving_box'][1]='-116'
        with self.assertRaisesRegex(ValueError,'CHANNEL_NOT_STRICTLY'):
            target(d)

    def test_target_and_velocity_mutations_fail(self):
        for key,value in (('door_degrees','1'),('moving_velocity',['0','1','0']),
                          ('parts',['GATE_Bolt','Other']),('range',['1','140'])):
            d=fixture();d[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):target(d)

    def test_native_probes_never_promote(self):
        for observed in ({'bolt_outside_model_volume_mm3':0.0,
                          'guide_outside_model_volume_mm3':0.0,
                          'guide_to_closed_channel_distance_mm':1.0},
                         {'bolt_outside_model_volume_mm3':1.0,
                          'guide_outside_model_volume_mm3':0.0,
                          'guide_to_closed_channel_distance_mm':0.0},{}):
            r=interpretation(observed)
            self.assertEqual(r['material_outer_containment'],'UNKNOWN')
            self.assertEqual(r['void_inner_containment'],'UNKNOWN')
            self.assertEqual(r['native_real_interval'],'NOT_TESTED')

    def test_material_and_void_diagnostics_separate(self):
        r=interpretation({'bolt_outside_model_volume_mm3':0,
                          'guide_outside_model_volume_mm3':2,
                          'guide_to_closed_channel_distance_mm':0})
        self.assertEqual(r['material_outer_probe']['guide_outside_model_volume_mm3'],'POSITIVE_DIFFERENCE_OBSERVED')
        self.assertEqual(r['void_inner_probe'],'CONTACT_OR_ZERO_DISTANCE_OBSERVED')


if __name__=='__main__':unittest.main()
