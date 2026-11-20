"""Synthetic controls for native Guide Face 0 five-UV observation gate."""
from copy import deepcopy
import unittest
from verify_face0_uv import QUERIES, validate, membership


REGION = {
    'status':'PASS','represented_face_region_equivalence':'PASS',
    'target':{'part':'GATE_BoltGuide_Left','face':0,'saved_pcurve_uses':8},
    'plane_mm':[['-200','-130','990'],['0','0','1'],['0','-1','0']],
    'outer_uv_mm':{'low':['0','-130'],'high':['60','0']},
    'inner_uv_mm':{'low':['9','-36'],'high':['51','-14']},
}
NATIVE = {
    'schema':1,'occt':'7.8.1','face_index':0,'face_count':10,'wire_count':2,
    'orientation':'Reversed','natural_restriction':False,
    'face_tolerance_mm':0.0000001,'classifier_tolerance_uv':0.000000001,
    'uv_bounds':[0,60,-130,0], 'surface_type':'Geom_Plane',
    'surface_location':[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
    'surface_frame_mm':[[-200,-130,990],[0,0,1],[0,-1,0]],
    'samples':[{'id':name,'uv':list(pt),'state':state} for name,pt,state in QUERIES],
    'sample_count':5,'native_full_face_equality':'UNKNOWN',
}


class Face0UVTests(unittest.TestCase):
    def test_expected_five_model_states(self):
        r=validate(deepcopy(NATIVE),deepcopy(REGION))
        self.assertEqual(r['status'],'PASS',r)
        self.assertEqual([x['native_classifier_state'] for x in r['observations']],
                         ['IN','OUT','ON','ON','OUT'])
        self.assertEqual(r['native_full_face_equality'],'UNKNOWN')
        self.assertEqual(r['native_representative_interval'],'NOT_TESTED')

    def test_boundary_belongs_to_mathematical_face_but_is_on(self):
        a,b=REGION['outer_uv_mm'],REGION['inner_uv_mm']
        self.assertEqual(membership((9,-20),a,b),'ON')
        self.assertEqual(membership((0,-20),a,b),'ON')
        self.assertEqual(membership((20,-20),a,b),'OUT')

    def test_wrong_classification_never_becomes_pass(self):
        for key,bad in [('face_interior','OUT'),('hole_interior','IN'),
                        ('inner_boundary','IN'),('outer_boundary','OUT'),
                        ('face_exterior','IN')]:
            n=deepcopy(NATIVE)
            next(x for x in n['samples'] if x['id']==key)['state']=bad
            with self.subTest(key=key),self.assertEqual(validate(n,REGION)['status'],'FAIL')

    def test_missing_or_extra_or_swapped_sample_rejected(self):
        for kind in ('missing','extra','swapped','coordinate','unknown'):
            n=deepcopy(NATIVE)
            if kind=='missing':n['samples'].pop()
            elif kind=='extra':n['samples'].append(n['samples'][0])
            elif kind=='swapped':n['samples'][0],n['samples'][1]=n['samples'][1],n['samples'][0]
            elif kind=='coordinate':n['samples'][0]['uv'][0]=6
            else:n['samples'][0]['state']='UNKNOWN'
            with self.subTest(kind=kind):
                self.assertEqual(validate(n,REGION)['status'],'FAIL')

    def test_native_face_identity_tolerance_restriction_and_frame(self):
        for key,bad in [('face_index',1),('wire_count',1),('orientation','Forward'),
                        ('natural_restriction',True),('classifier_tolerance_uv',0),
                        ('face_tolerance_mm',-1),('surface_type','Geom_CylindricalSurface'),
                        ('native_full_face_equality','PASS')]:
            n=deepcopy(NATIVE);n[key]=bad
            with self.subTest(key=key):
                self.assertEqual(validate(n,REGION)['status'],'FAIL')
        n=deepcopy(NATIVE);n['surface_frame_mm'][0][0]=-199
        self.assertEqual(validate(n,REGION)['status'],'FAIL')
        n=deepcopy(NATIVE);n['uv_bounds'][1]=61
        self.assertEqual(validate(n,REGION)['status'],'FAIL')

    def test_prior_region_failures_rejected(self):
        for key,bad in [('status','FAIL'),('represented_face_region_equivalence','FAIL')]:
            r=deepcopy(REGION);r[key]=bad
            self.assertEqual(validate(NATIVE,r)['status'],'FAIL')


if __name__=='__main__':
    unittest.main()
