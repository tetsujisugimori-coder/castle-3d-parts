"""Synthetic adversarial tests for exact candidate correspondence, not CAD proof."""
import copy
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cad/stage3d5b'))
from test_planar_contract import block, guide
from test_planar_native import observation
from correspondence import contained, boxes_mm_to_m, correspondence, endpoint_link, pair_gap


def line_fixture(d):
    t = observation(d)
    for e in t['edges']:
        a,b = [list(map(F,t['vertices'][i]['point_mm_ieee'])) for i in e['vertex_ids']]
        e['curve_location_mm_observed'] = list(map(str,a))
        e['curve_direction_observed'] = [str(b[i]-a[i]) for i in range(3)]
        e['parameters_ieee'] = ['0','1']
    return t


def guide_boxes_mm():
    return [['0','0','0','2000','1000','4000'],
            ['0','3000','0','2000','4000','4000'],
            ['0','1000','0','2000','3000','1000'],
            ['0','1000','3000','2000','3000','4000']]


class ExactBridgeTests(unittest.TestCase):
    def test_positive_guide_material_and_open_void(self):
        r=correspondence(line_fixture(guide()),guide_boxes_mm(),
                         ['-1000','1500','1500','3000','2500','2500'])
        self.assertEqual(r['status'],'PASS',r)
        self.assertEqual(r['edge_parameter_link']['edge_count'],24)
        self.assertEqual(r['represented_set_equality'],'PASS')
        self.assertEqual(r['candidate_void_to_query']['status'],'PASS')
        self.assertEqual(r['candidate_void_to_query']['min_squared_gap_mm2'],'250000')
        self.assertEqual(r['real_material_inclusion'],'UNKNOWN')
        self.assertEqual(r['real_void_inclusion'],'UNKNOWN')

    def test_positive_block(self):
        r=correspondence(line_fixture(block()),[['0','0','0','4000','4000','4000']])
        self.assertEqual(r['status'],'PASS',r)
        self.assertEqual(r['edge_parameter_link']['edge_count'],12)

    def test_line_parameter_mismatch(self):
        t=line_fixture(block());t['edges'][0]['parameters_ieee']=['0','2']
        self.assertEqual(correspondence(t,[['0','0','0','4000','4000','4000']])['reason'],
                         'LINE_ENDPOINT_PARAMETERS_DISAGREE_WITH_VERTICES')

    def test_missing_trim_or_normal(self):
        for fault in ('missing-trim','normal'):
            t=line_fixture(guide())
            if fault=='missing-trim':
                t['faces'][0]['wire_roles'].pop();t['faces'][0]['wire_ids'].pop()
            else:
                t['faces'][0]['normal_ieee'][0]='1'
            self.assertEqual(correspondence(t,guide_boxes_mm())['status'],'FAIL')

    def test_one_way_containment_insufficient(self):
        small=boxes_mm_to_m([['0','0','0','2000','1000','1000']])
        big=boxes_mm_to_m([['0','0','0','2000','2000','1000']])
        self.assertEqual(contained(small,big)['status'],'PASS')
        self.assertEqual(contained(big,small)['status'],'FAIL')

    def test_narrowed_hole_or_touch_fails(self):
        t=line_fixture(guide())
        model=guide_boxes_mm()
        model[0][4]='1500'
        self.assertEqual(correspondence(t,model)['represented_set_equality'],'FAIL')
        touch=['-1000','1000','1000','3000','2500','2500']
        self.assertEqual(correspondence(line_fixture(guide()),guide_boxes_mm(),touch)
                         ['candidate_void_to_query']['status'],'FAIL')

    def test_missing_candidate_never_real_pass(self):
        self.assertEqual(pair_gap({'status':'FAIL'}, {'status':'PASS'})['status'],'NOT_TESTED')
        t=line_fixture(block())
        t['edges'][0]['curve_type']='Circle'
        result=correspondence(t,[['0','0','0','4000','4000','4000']])
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['real_material_inclusion'],'UNKNOWN')


if __name__=='__main__':
    unittest.main()
