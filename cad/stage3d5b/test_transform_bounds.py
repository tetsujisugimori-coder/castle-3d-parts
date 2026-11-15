"""Exact conditional transform controls, separate from actual CAD extraction."""
from copy import deepcopy
from fractions import Fraction
import unittest
from transform_bounds import (Interval as I, IDENTITY, ERROR_COMPONENTS, affine,
                             stored_float, compose, apply, affine_error,
                             observed_matrix_error, round_enclosure,
                             combined_error, chain, translation_motion, distance_lower)
from transform_bounds import offset_box


def fixture():
    shift = list(IDENTITY); shift[3] = 1000
    scale = [str(Fraction(v, 1000)) for v in IDENTITY]
    return [dict(id='shape-location', from_frame='local', to_frame='world-mm',
                 from_unit='mm', to_unit='mm', matrix=shift),
            dict(id='mm-to-m', from_frame='world-mm', to_frame='world-m',
                 from_unit='mm', to_unit='m', matrix=scale)]


class TransformBounds(unittest.TestCase):
    def test_binary_value_is_not_decimal_or_real_enclosure(self):
        exact = stored_float(0.1)
        self.assertEqual(exact.lo, Fraction(*0.1.as_integer_ratio()))
        self.assertNotEqual(exact.lo, Fraction(1, 10))
        with self.assertRaises(ValueError): I('sqrt(2)', 'sqrt(2)')
        for x in [float('inf'), float('nan')]:
            with self.assertRaises(ValueError): stored_float(x)
        with self.assertRaises(ValueError): I(0.1, 0.1)

    def test_interval_negative_products(self):
        self.assertEqual(I(-3, 2)*I(-5, -1), I(-10, 15))
        self.assertEqual(I('-1/7', '2/3')+I('1/7', '1/3'), I(0, 1))

    def test_composition_order_noncommuting(self):
        scale = list(IDENTITY); scale[0] = 2
        shift = list(IDENTITY); shift[3] = 3
        self.assertEqual(apply(compose(scale, shift), [1, 0, 0])[0], I.point(8))
        self.assertEqual(apply(compose(shift, scale), [1, 0, 0])[0], I.point(5))

    def test_generic_near_rotation_error_not_projected(self):
        actual = list(IDENTITY); actual[0] = ['999/1000', '1001/1000']
        actual[3] = ['-1/10000', '2/10000']
        r = affine_error(actual, IDENTITY, [[-2, 3], [0, 0], [0, 0]])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['error_m'], '2/625')
        self.assertEqual(r['real_brep'], 'UNKNOWN')

    def test_observed_ieee_comparison_does_not_prove_real_error(self):
        a = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
        r = observed_matrix_error(a, IDENTITY, [[-1, 1]]*3)
        self.assertEqual(r['represented_vs_nominal']['error_m'], '0')
        self.assertEqual(r['status'], 'UNKNOWN')
        self.assertIsNone(r['real_transform_error_m'])
        decimal_input = list(a); decimal_input[0] = '1.0'
        with self.assertRaises(ValueError):
            observed_matrix_error(decimal_input, IDENTITY, [[-1, 1]]*3)

    def test_outward_rounding_negative_asymmetric(self):
        self.assertEqual(round_enclosure(I('-1/3', '2/7'), '1/10'), I('-2/5', '3/10'))
        with self.assertRaises(ValueError): round_enclosure(I(0, 1), '-1/10')
        self.assertEqual(round_enclosure(I('-2/5', '3/10'), '1/10'), I('-2/5', '3/10'))

    def test_missing_components_stay_unknown(self):
        a = dict.fromkeys(ERROR_COMPONENTS, '0'); a['geometry'] = None
        r = combined_error(a)
        self.assertEqual(r['status'], 'UNKNOWN'); self.assertIsNone(r['error_m'])
        self.assertEqual(r['missing'], ['geometry'])
        self.assertEqual(affine_error(None, IDENTITY, [[-1, 1]]*3)['status'], 'UNKNOWN')

    def test_error_underreport_rejected(self):
        a = dict.fromkeys(ERROR_COMPONENTS, '1/1000000')
        self.assertEqual(combined_error(a, '6/1000000')['status'], 'FAIL')
        self.assertEqual(combined_error(a, '7/1000000')['status'], 'PASS')
        a['pose'] = '-1';
        with self.assertRaises(ValueError): combined_error(a)

    def test_declared_path_normal(self):
        r = chain(fixture(), ['shape-location', 'mm-to-m'], 'local', 'world-m')
        self.assertEqual(r['status'], 'PASS'); self.assertEqual(r['matrix'][3], ['1', '1'])
        self.assertEqual(r['real_brep'], 'UNKNOWN')

    def test_offset_directions_and_void_boundary(self):
        box = [['-1', '1']]*3
        a = offset_box(box, '1/10', 'material-outer')
        b = offset_box(box, '1/10', 'void-inner')
        self.assertEqual(a['box_m'], [['-11/10', '11/10']]*3)
        self.assertEqual(a['boundary'], 'closed')
        self.assertEqual(b['box_m'], [['-9/10', '9/10']]*3)
        self.assertEqual(b['boundary'], 'open')
        self.assertEqual(b['real_brep'], 'UNKNOWN')
        self.assertEqual(offset_box(box, '1', 'void-inner')['status'], 'UNKNOWN')
        self.assertEqual(offset_box(box, None, 'material-outer')['status'], 'UNKNOWN')

    def test_placement_omission_double_application_and_order(self):
        f = fixture(); ids = ['shape-location', 'mm-to-m']
        for bad in [f[1:], [f[0], f[0], f[1]], f[::-1]]:
            with self.subTest(ids=[e['id'] for e in bad]):
                self.assertEqual(chain(bad, ids, 'local', 'world-m')['status'], 'FAIL')
        self.assertEqual(chain(f, None, 'local', 'world-m')['status'], 'UNKNOWN')

    def test_wrong_units_and_conversion_rejected(self):
        f = fixture(); ids = ['shape-location', 'mm-to-m']
        for key, value in [('from_unit', 'm'), ('to_unit', 'mm')]:
            bad = deepcopy(f); bad[1][key] = value
            self.assertEqual(chain(bad, ids, 'local', 'world-m')['status'], 'FAIL')
        bad = deepcopy(f); bad[1]['matrix'][0] = '1'
        self.assertEqual(chain(bad, ids, 'local', 'world-m')['status'], 'FAIL')

    def test_translation_reference_and_missing_rotation_error(self):
        self.assertEqual(translation_motion([['0', '7/50'], 0, 0], ['7/100', 0, 0], '0')['motion_m'], '7/100')
        self.assertEqual(translation_motion([['0', '7/50'], 0, 0], [0, 0, 0], '0')['motion_m'], '7/50')
        self.assertEqual(translation_motion([['0', '7/50'], 0, 0], [0, 0, 0])['status'], 'UNKNOWN')

    def test_distance_touch_separation_intrusion_not_penetration_verdict(self):
        for lower, expected in [('1', 'UNKNOWN'), ('1000000000001/1000000000000', 'PASS'),
                                ('999999999999/1000000000000', 'UNKNOWN')]:
            self.assertEqual(distance_lower(lower, '1', '0', '0', '0')['status'], expected)
        self.assertEqual(distance_lower('1', None, '0', '0', '0')['status'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
