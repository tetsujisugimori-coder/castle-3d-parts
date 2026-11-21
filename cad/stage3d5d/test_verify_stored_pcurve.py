"""Only synthetic observation-record controls. Native controls run separately."""
import copy
import unittest

from verify_stored_pcurve import controls, join_all, LOCATIONS, verdict

MATRIX = [[1, 0, 0, -400], [0, 1, 0, -115], [0, 0, 1, 1000], [0, 0, 0, 1]]
IDENTITY = [[int(i == j) for j in range(4)] for i in range(4)]
EXPECTED = {'face': 0, 'wire': 0, 'edge': 0, 'use': 0, 'face_orientation': 'Reversed',
            'wire_orientation': 'Reversed', 'orientation': 'Forward', 'pcurve_type': 'Line2d',
            'pcurve_range': ['0', '40'], 'curve_range': ['0', '40'],
            'plane': [['-400', '-115', '1000'], ['0', '0', '1'], ['0', '-1', '0']],
            'curve': [['-400', '-115', '1000'], ['0', '0', '1']],
            'pcurve': [['0', '0'], ['1', '0']], **dict.fromkeys(LOCATIONS, MATRIX)}
NATIVE = {**EXPECTED, 'pcurve_type': 'Geom2d_Line', 'curve_type': 'Geom_Line',
          'surface_type': 'Geom_Plane', 'status': 'CAPTURED', 'degenerated': False,
          'ordered_use': 0, 'ordered_matches': 1, 'indexed_matches': 1, 'surface_location_candidate_count': 1,
          'selected_2d_matches': 1, 'matching_3d_count': 1, 'seam': False, 'stored': True,
          'same_parameter': True, 'same_range': True, 'selected_2d_rep_ordinal': 2,
          'selected_3d_rep_ordinal': 1, 'indexed_tool_rank': 1, 'indexed_range': [0, 40],
          'surface_location': MATRIX, 'edge_location': MATRIX,
          'relative_rep_2d_location': IDENTITY, 'relative_rep_3d_location': IDENTITY}


class StoredProofTests(unittest.TestCase):
    def test_normal_and_fault_matrix(self):
        for test in controls(NATIVE, EXPECTED):
            with self.subTest(fault=test['case']):
                self.assertEqual(test['status'], test['expected'])

    def test_distinct_matching_handle_needed_even_at_same_coefficients(self):
        for k in ('indexed_matches', 'selected_2d_matches', 'matching_3d_count'):
            with self.subTest(key=k):
                self.assertEqual(verdict({**NATIVE, k: 0}, EXPECTED)['status'], 'UNKNOWN')

    def test_additional_relative_rep_location_is_not_topological_location(self):
        record = copy.deepcopy(NATIVE)
        record['relative_rep_2d_location'] = [row[:] for row in IDENTITY]
        record['surface_location'] = [row[:] for row in MATRIX]
        record['relative_rep_2d_location'][0][3] = 20
        record['surface_location'][0][3] = -380
        self.assertEqual(verdict(record, EXPECTED)['status'], 'PASS')
        record['surface_location'][0][3] = -400
        self.assertEqual(verdict(record, EXPECTED)['reason'], 'GEOMETRY_LOCATION_MISMATCH')

    def test_nontrivial_rational_comparison(self):
        record = copy.deepcopy(NATIVE)
        record['curve'][0][0] = -400.00000000000006
        self.assertEqual(verdict(record, EXPECTED)['reason'], 'FORMULA_COEFFICIENT_MISMATCH')

    def test_join_refuses_duplicates_and_keeps_missing_unknown(self):
        census = {(0, 0, 0): EXPECTED}
        self.assertEqual(join_all([], census)[0]['status'], 'UNKNOWN')
        self.assertEqual(join_all([NATIVE], census)[0]['status'], 'PASS')
        with self.assertRaisesRegex(ValueError, 'NATIVE_CENSUS'):
            join_all([NATIVE, NATIVE], census)
        with self.assertRaisesRegex(ValueError, 'NATIVE_CENSUS'):
            join_all([{**NATIVE, 'edge': 9}], census)
