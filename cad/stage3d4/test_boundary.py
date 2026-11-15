"""Exact synthetic controls. No test here establishes imported CAD containment."""
import copy
import json
from pathlib import Path
import unittest
from boundary import (VERSION, from_boxes, verify_boundary, verify_void, enclose,
                      pair_relation, rational)


def cube():
    return from_boxes([[0, 0, 0, 1, 1, 1]])


class Boundary(unittest.TestCase):
    def bad(self, mutate, code):
        data = cube(); mutate(data)
        with self.assertRaisesRegex(ValueError, code):
            verify_boundary(data)

    def test_normal(self):
        r = verify_boundary(cube())
        self.assertEqual(r['material_outer_cells'], [['0', '0', '0', '1', '1', '1']])
        self.assertEqual(r['oriented_closed_boundary'], 'PASS')
        self.assertEqual(r['cad_application'], 'UNKNOWN')

    def test_fixed_d2_ring_and_bolt(self):
        c = json.loads((Path(__file__).parents[1] / 'stage3d2/contract.json').read_text())
        bolt, guide = from_boxes([c['moving_box']]), from_boxes(c['obstacle_boxes'])
        r = verify_boundary(guide)
        self.assertGreater(r['material_cell_count'], 1)
        self.assertEqual(verify_void(guide, [-200, '-231/2', '1999/2', -180, '-189/2', '2081/2'])['status'], 'PASS')
        self.assertEqual(pair_relation(bolt, guide)['relation'], 'SEPARATE')
        self.assertEqual(pair_relation(bolt, guide)['minimum_squared_distance_mm2'], '1')

    def test_contact(self):
        r = pair_relation(cube(), from_boxes([[1, 0, 0, 2, 1, 1]]))
        self.assertEqual(r['relation'], 'CONTACT'); self.assertEqual(r['cad_status'], 'UNKNOWN')

    def test_penetration(self):
        self.assertEqual(pair_relation(cube(), from_boxes([['1/2', 0, 0, 2, 1, 1]]))['relation'], 'PENETRATION')

    def test_separation(self):
        self.assertEqual(pair_relation(cube(), from_boxes([[2, 0, 0, 3, 1, 1]]))['minimum_squared_distance_mm2'], '1')

    def test_void_touch_unknown(self):
        self.assertEqual(verify_void(cube(), [1, 0, 0, 2, 1, 1])['status'], 'UNKNOWN')

    def test_void_intersect_unknown(self):
        self.assertEqual(verify_void(cube(), ['1/2', 0, 0, 2, 1, 1])['status'], 'UNKNOWN')

    def test_void_boundary_before_after(self):
        for x, status in [('999999/1000000', 'UNKNOWN'), ('1', 'UNKNOWN'), ('1000001/1000000', 'PASS')]:
            self.assertEqual(verify_void(cube(), [x, 0, 0, 2, 1, 1])['status'], status)

    def test_missing_face(self):
        self.bad(lambda d: d['faces'].pop(), 'FACE_COUNT')

    def test_missing_face_larger_shell(self):
        d = from_boxes([[0, 0, 0, 2, 1, 1], [0, 1, 0, 1, 2, 1]])
        d['faces'].pop()
        with self.assertRaises(ValueError): verify_boundary(d)

    def test_flip_x(self):
        self.bad(lambda d: d['faces'][0].update(normal=1), 'WINDING_ORIENTATION')

    def test_flip_y(self):
        self.bad(lambda d: d['faces'][2].update(normal=1), 'BOUNDARY_INCIDENCE_MISMATCH')

    def test_duplicate(self):
        self.bad(lambda d: d['faces'].append(copy.deepcopy(d['faces'][0])), 'DUPLICATE')

    def test_extra_rectangle(self):
        self.bad(lambda d: d['faces'].append({'axis': 0, 'coordinate': '2', 'u': ['0', '1'], 'v': ['0', '1'], 'normal': 1}), 'WINDING_ORIENTATION')

    def test_unsupported_face(self):
        self.bad(lambda d: d['faces'][0].update(surface='Cylinder'), 'RECTANGLE_FIELDS')

    def test_degenerate_face(self):
        self.bad(lambda d: d['faces'][0].update(u=['0', '0']), 'DEGENERATE_FACE')

    def test_float(self):
        self.bad(lambda d: d['faces'][0].update(coordinate=0.0), 'EXACT_RATIONAL_REQUIRED')

    def test_nonfinite(self):
        for v in ['nan', 'Infinity', '1/0']:
            self.bad(lambda d: d['faces'][0].update(coordinate=v), 'INVALID_RATIONAL')

    def test_unit(self):
        self.bad(lambda d: d.update(unit='m'), 'SCHEMA_OR_UNIT')

    def test_missing_field(self):
        self.bad(lambda d: d['faces'][0].pop('normal'), 'RECTANGLE_FIELDS')

    def test_empty(self):
        self.bad(lambda d: d.update(faces=[]), 'FACE_COUNT')

    def test_forged_pass(self):
        self.bad(lambda d: d.update(status='PASS'), 'SCHEMA_FIELDS')

    def test_forged_zero_error(self):
        self.bad(lambda d: d.update(error_mm='0'), 'SCHEMA_FIELDS')

    def test_disconnected_extra_solid(self):
        with self.assertRaisesRegex(ValueError, 'DISCONNECTED'):
            verify_boundary(from_boxes([[0, 0, 0, 1, 1, 1], [2, 0, 0, 3, 1, 1]]))

    def test_nonmanifold_touching_edge(self):
        # Main two columns joined behind, with diagonal edge contact at front.
        cells = [[0, 0, 0, 1, 1, 2], [1, 1, 0, 2, 2, 2], [0, 0, 1, 2, 2, 2]]
        with self.assertRaisesRegex(ValueError, 'NONMANIFOLD_EDGE'):
            verify_boundary(from_boxes(cells))

    def test_outward_rounding_negative(self):
        d = from_boxes([['-1/3', '1/3', '2/3', '2/3', '4/3', '5/3']])
        r = enclose(d, '1/2')
        self.assertEqual(r['outer_cells'], [['-1/2', '0', '1/2', '1', '3/2', '2']])
        self.assertEqual(r['max_coordinate_error_mm'], '1/3')

    def test_understated_error(self):
        d = from_boxes([['1/3', '1/3', '1/3', '2/3', '2/3', '2/3']])
        with self.assertRaisesRegex(ValueError, 'UNDERSTATED'):
            enclose(d, 1, '1/4')
        self.assertEqual(enclose(d, 1, '1/3')['max_coordinate_error_mm'], '1/3')

    def test_reversed_rounding_cannot_enter_schema(self):
        self.bad(lambda d: d.update(rounding='ceil-minima-floor-maxima'), 'SCHEMA_FIELDS')

    def test_invalid_step(self):
        for step in [0, -1]:
            with self.assertRaisesRegex(ValueError, 'POSITIVE'): enclose(cube(), step)

    def test_bool_axis(self):
        self.bad(lambda d: d['faces'][0].update(axis=False), 'AXIS_OR_ORIENTATION')

    def test_rational_budget(self):
        with self.assertRaisesRegex(ValueError, 'BUDGET'): rational(str(2 ** 300))

    def test_inward_hole_shrink(self):
        c = json.loads((Path(__file__).parents[1] / 'stage3d2/contract.json').read_text())
        hole = [-200, '-231/2', '1999/2', -180, '-189/2', '2081/2']
        changed = copy.deepcopy(c['obstacle_boxes'])
        changed[0][4] = '-115'
        self.assertEqual(verify_void(from_boxes(changed), hole)['status'], 'UNKNOWN')

    def test_bolt_enlargement(self):
        c = json.loads((Path(__file__).parents[1] / 'stage3d2/contract.json').read_text())
        changed = copy.deepcopy(c['moving_box']); changed[1] = '-117'
        self.assertEqual(pair_relation(from_boxes([changed]), from_boxes(c['obstacle_boxes']))['relation'], 'PENETRATION')

    def test_placement_shift(self):
        self.assertEqual(pair_relation(cube(), from_boxes([['1/2', 0, 0, '3/2', 1, 1]]))['relation'], 'PENETRATION')

if __name__ == '__main__': unittest.main()
