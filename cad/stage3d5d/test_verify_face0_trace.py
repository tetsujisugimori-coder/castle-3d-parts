"""Synthetic contract tests; these do not claim an actual OCCT hook executed."""
from copy import deepcopy
from fractions import Fraction as Q
import unittest
from verify_face0_trace import validate
from verify_face0_uv import QUERIES
from test_face_region import fixture
from test_verify_face0_uv import NATIVE


def example():
    tr,_,_=fixture()
    tr['parts']['GATE_BoltGuide_Left']['faces'][0]['wires'][0]['uses'][0]['edge']=0
    n=deepcopy(NATIVE)
    w=tr['parts']['GATE_BoltGuide_Left']['faces'][0]['wires'][0]['uses'][0]
    a,b=w['directed_uv']
    events=[]
    for name,point,state in QUERIES:
        ray={'origin':list(point),'direction':[1,0]}
        base={'query':name,'ray':ray}
        events.append({'seq':len(events)+1,'query':name,'event':'ray_choice',
                       'candidate_point_uv':list(point),'ray':ray,'ray_length':1,
                       'selected':True})
        x={'seq':len(events)+1,'query':name,'event':'intersector',
           'face_local_edge_ordinal':1,'edge_orientation':'Forward',
           'edge_start_uv':a,'edge_end_uv':b,'use_bbox':False,
           'gap_check_tolerance':0.1,'ray':ray,'ray_length':1,
           'tol_argument':1e-9,'is_done':True,'intersection_points':1,'intersection_segments':0}
        events.append(x)
        y={'seq':len(events)+1,'query':name,'event':'compare',
           'face_local_edge_ordinal':1,'edge_orientation':'Forward',
           'edge_start_uv':a,'edge_end_uv':b,'use_bbox':False,
           'gap_check_tolerance':0.1,
           'compare_orientation':'Forward',
           'closest_index':1,'state_after':state}
        events.append(y)
    return n,deepcopy(n),events,tr


class TraceContractTests(unittest.TestCase):
    def test_valid_bounded_trace_does_not_promote_global_claim(self):
        r=validate(*example())
        self.assertEqual(r['status'],'PASS',r)
        self.assertEqual(len(r['five_points']),5)
        self.assertEqual(r['native_full_face_set_equality'],'UNKNOWN')
        self.assertEqual(r['native_actual_interposition'],'PASS')
        self.assertEqual(r['native_representative_interval'],'NOT_TESTED')

    def test_missing_or_mutated_hook_fails_closed(self):
        for mutation in ('missing_ray','missing_compare','wrong_edge','wrong_query','wrong_option','no_hit','missing_closest'):
            d=list(example())
            if mutation=='missing_ray':d[2].pop(0)
            if mutation=='missing_compare':d[2].pop(2)
            if mutation=='wrong_edge':d[2][1]['edge_start_uv']=[999,999]
            if mutation=='wrong_query':d[2][1]['query']='UNMATCHED'
            if mutation=='wrong_option':d[2][1]['use_bbox']=True
            if mutation=='no_hit':d[2][1]['intersection_points']=0
            if mutation=='missing_closest':d[2][2]['closest_index']=0
            for i,e in enumerate(d[2]):e['seq']=i+1
            with self.subTest(mutation=mutation):
                self.assertEqual(validate(*d)['status'],'FAIL')

    def test_interposed_output_must_equal_original(self):
        d=list(example())
        d[1]['samples'][0]['state']='OUT'
        self.assertEqual(validate(*d)['status'],'FAIL')

    def test_unknown_numeric_bound_preserved_even_with_hits(self):
        report=validate(*example())
        self.assertEqual(report['native_classifier_total_rounding_error'],'UNKNOWN')
        self.assertEqual(report['native_material_outer'],'UNKNOWN')
        self.assertEqual(report['native_void_inner'],'UNKNOWN')

if __name__=='__main__':
    unittest.main()
