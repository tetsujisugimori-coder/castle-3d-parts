"""Portable controls for the separate sampled-placement observation gate."""
import unittest

from placement_observation import CHECKS, LEAF_HI, LEAF_LO, PARTS, REF, sampled_gate


class SampledGateTests(unittest.TestCase):
    def cases(self):
        return [{'requested_mm': str(t), 'represented_bolt_mm': str(t), 'angle_degrees': '0',
                 'parts': [{'object': name, 'represented_checks': dict.fromkeys(CHECKS, True)}
                           for name in PARTS]} for t in (LEAF_LO, REF, LEAF_HI)]

    def test_normal(self):
        self.assertEqual(sampled_gate(self.cases()), 'PASS')

    def test_missing_position_or_inexact_quantity(self):
        self.assertEqual(sampled_gate(self.cases()[:-1]), 'FAIL')
        broken = self.cases()
        broken[1]['represented_bolt_mm'] = '1/2'
        self.assertEqual(sampled_gate(broken), 'FAIL')

    def test_missing_or_extra_application_fails(self):
        for check in CHECKS:
            for fault in (False, None, 1):
                with self.subTest(check=check, fault=fault):
                    broken = self.cases()
                    observed = broken[1]['parts'][0]['represented_checks']
                    if fault is None:
                        del observed[check]
                    else:
                        observed[check] = fault
                    self.assertEqual(sampled_gate(broken), 'FAIL')
