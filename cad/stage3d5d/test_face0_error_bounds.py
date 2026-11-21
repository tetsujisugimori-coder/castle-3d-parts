"""Adversarial tests: exact input bounds are NOT native classifier bounds."""
from copy import deepcopy
from fractions import Fraction as Q
import unittest

from face0_error_bounds import analyze, mathematical_margin, finite_segments, exact_binary64
from test_face_region import fixture
from test_verify_face0_uv import REGION, NATIVE


def records():
    trim, _, _=fixture()
    region=deepcopy(REGION)
    native=deepcopy(NATIVE)
    observed={'status':'PASS','native_full_face_equality':'UNKNOWN',
              'native_metadata':deepcopy(native)}
    return [region,native,observed,trim]


class Face0ErrorBoundsTests(unittest.TestCase):
    def test_fixed_exact_inputs_and_margins(self):
        result=analyze(*records())
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['recorded_binary64_input_quantization_error_upper_mm'],'0')
        self.assertGreater(result['recorded_binary64_input_count'],50)
        self.assertEqual([Q(x['exact_distance_to_model_boundary_Linf_mm'])
                          for x in result['query_margins']],list(map(Q,(4,6,0,0,1))))
        self.assertEqual([x['positive_robust_radius_exists']
                          for x in result['query_margins']],[True,True,False,False,True])
        self.assertEqual(result['ideal_UV_to_3D_distance_scale'],'1')
        self.assertIsNone(result['native_classifier_total_rounding_error_upper_mm'])
        self.assertIsNone(result['native_effective_tolerance_band_upper_mm'])
        self.assertEqual(result['native_real_face_all_point_equivalence'],'UNKNOWN')

    def test_binary64_exact_half_but_not_tenth(self):
        self.assertTrue(exact_binary64('9/2'))
        self.assertTrue(exact_binary64('93/2'))
        self.assertFalse(exact_binary64('1/10'))

    def test_mutated_non_dyadic_pcurve_rejected(self):
        d=records()
        d[3]['parts']['GATE_BoltGuide_Left']['faces'][0]['wires'][0]['uses'][0]['pcurve'][0][0]='1/10'
        with self.assertRaisesRegex(ValueError,'BINARY64_INPUT_QUANTIZATION_NOT_ZERO'):
            analyze(*d)

    def test_native_and_summary_must_be_byte_semantically_identical(self):
        d=records()
        d[1]['samples'][0]['state']='OUT'
        with self.assertRaisesRegex(ValueError,'NATIVE_FIVE_POINT_REPORT_NOT_IDENTICAL'):
            analyze(*d)

    def test_frame_and_query_identity_fail_closed(self):
        d=records()
        d[1]['surface_frame_mm'][0][0]=-199
        d[2]['native_metadata']=deepcopy(d[1])
        with self.assertRaisesRegex(ValueError,'NATIVE_FRAME_NOT_REPRESENTED_FRAME'):
            analyze(*d)
        d=records()
        d[1]['samples'][1]['uv'][0]=21
        d[2]['native_metadata']=deepcopy(d[1])
        with self.assertRaisesRegex(ValueError,'FIXED_NATIVE_OR_MODEL_POINT_CHANGED'):
            analyze(*d)

    def test_boundary_radius_zero_no_positive_global_claim(self):
        d=records()
        e=finite_segments(d[3]['parts']['GATE_BoltGuide_Left']['faces'][0])
        self.assertEqual(mathematical_margin((9,-20),e),0)
        self.assertEqual(mathematical_margin((0,-20),e),0)
        self.assertEqual(mathematical_margin((5,-20),e),4)
        self.assertEqual(mathematical_margin((20,-20),e),6)
        self.assertEqual(mathematical_margin((-1,-20),e),1)

    def test_missing_native_or_prior_proof_never_pass(self):
        d=records();d[0]['status']='FAIL'
        with self.assertRaises(ValueError):analyze(*d)
        d=records();d[1]['classifier_tolerance_uv']=0
        d[2]['native_metadata']=deepcopy(d[1])
        with self.assertRaises(ValueError):analyze(*d)
        d=records();d[3]['source_d2_sha256']='tampered'
        with self.assertRaises(ValueError):analyze(*d)


if __name__=='__main__':
    unittest.main()
