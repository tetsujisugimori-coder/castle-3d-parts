"""Synthetic counterexamples; no archived CAD or previous run is used."""
import copy
import unittest
from bounds import validate, directed_bound, rotation_chord_bound, continuous_lower_bound


def fixture():
    # A rectangular through-hole, along X, in a closed box. Four closed slabs
    # cover the regular closed stock minus the open bore (including its walls).
    solid = {
        'cells': {'bottom': ['0','0','0','1','1','0.2'],
                  'top': ['0','0','0.8','1','1','1'],
                  'left': ['0','0','0.2','1','0.2','0.8'],
                  'right': ['0','0.8','0.2','1','1','0.8']},
        'faces': {'x-min': {'normal': ['-1','0','0'], 'solid_side': 'positive'},
                  'x-max': {'normal': ['1','0','0'], 'solid_side': 'negative'}},
        'holes': {'bore': {'type': 'rectangular-through', 'axis': 'X',
                           'center_yz_m': ['0.5','0.5'], 'half_size_yz_m': ['0.3','0.3'],
                           'inner_walls': 4, 'solid_side': 'outside-bore',
                           'openings': ['x-min','x-max'], 'trim': 'four-lines'}},
        'transform': {'rotation': ['1','0','0','0','1','0','0','0','1'],
                      'translation_m': ['0','0','0']}}
    return {'kind': 'synthetic-exact-cell-union-v1', 'unit': 'm',
            'coordinates': 'world-right-handed-Z-up', 'source': solid,
            'model': copy.deepcopy(solid),
            'mapping': {k:k for k in solid['cells']}, 'epsilon_m': '0',
            'errors_m': {k:'0' for k in ('brep_tolerance','extraction','placement',
                                        'floating_point','predicate')}}


class Controls(unittest.TestCase):
    def test_normal_control(self):
        self.assertEqual(validate(fixture())['status'], 'PASS')

    def test_nonzero_bound_control(self):
        d=fixture(); d['model']['cells']['top'][5]='0.999'; d['epsilon_m']='0.001'
        self.assertEqual(validate(d)['status'], 'PASS')

    def test_ten_counterexamples(self):
        cases=[]
        d=fixture(); d['model']['faces']['x-min']['normal'][0]='1'; cases.append(d)
        d=fixture(); d['model']['holes']['bore']['center_yz_m'][0]='0.51'; cases.append(d)
        d=fixture(); d['model']['holes']['bore']['half_size_yz_m'][0]='0.31'; cases.append(d)
        d=fixture(); d['model']['holes']['bore']['solid_side']='inside-bore'; cases.append(d)
        d=fixture(); d['model']['transform']['translation_m'][0]='1'; cases.append(d)
        d=fixture(); f=d['model']['faces']; f['x-min'],f['x-max']=f['x-max'],f['x-min']; cases.append(d)
        # Point (0.5,0.5,1) is .01m above every model cell after shrinking.
        d=fixture(); d['model']['cells']['top'][5]='0.99'; d['epsilon_m']='0.001'; cases.append(d)
        # Endpoints x=-1,+1 clear of [-.1,.1], midpoint x=0 interferes.
        # Missing movement bound forbids sample-only admission.
        from fractions import Fraction as F
        def overlaps(center):
            return center-F('0.05') < F('0.1') and center+F('0.05') > F('-0.1')
        self.assertFalse(overlaps(F('-1'))); self.assertFalse(overlaps(F('1')))
        self.assertTrue(overlaps(F('0')))
        self.assertEqual(continuous_lower_bound('0.9','0','0',None,'0')['status'],'UNKNOWN')
        d=fixture(); d['errors_m']['brep_tolerance']='0.0000001'; cases.append(d)
        d=fixture(); del d['model']['holes']['bore']; cases.append(d)
        for i,d in enumerate(cases):
            with self.subTest(case=i+1): self.assertNotEqual(validate(d)['status'],'PASS')

    def test_real_cad_gate(self):
        d=fixture(); d['kind']='occt-extracted'; self.assertEqual(validate(d)['status'],'UNKNOWN')

    def test_malformed_map(self):
        d=fixture(); d['mapping']=list(d['mapping']); self.assertEqual(validate(d)['status'],'FAIL')
        d=fixture(); d['model']['cells']['invalid']=['nan']*6
        self.assertEqual(validate(d)['status'],'FAIL')

    def test_arithmetic(self):
        self.assertEqual(str(directed_bound(['0']*3+['1']*3,['0']*3+['1.1']*3)), '3/10')
        self.assertEqual(str(rotation_chord_bound('2','0.1','0.01','0')), '21/100')
        self.assertEqual(continuous_lower_bound('1','0.1','0.1','0.1','0.1')['status'],'PASS')
        self.assertEqual(continuous_lower_bound('0','0','0','0','0')['status'],'UNKNOWN')
        for bad in ('nan','inf','1e-10',0.1):
            self.assertEqual(continuous_lower_bound(bad,'0','0','0','0')['status'],'FAIL')


if __name__ == '__main__': unittest.main(verbosity=2)
