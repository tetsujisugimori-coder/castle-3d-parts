"""Small synthetic controls for the fixed native PlaneValue error enclosure.

This tests the exact arithmetic and failure behavior, NOT the OCCT runtime.
"""
from copy import deepcopy
from fractions import Fraction as Q
import unittest

from verify_plane_roundoff import (EPS,GAMMA16,analyze,bound_for_coordinate,
                                   outward_up,outward_down)


WORLD=[
([-200,-130,990],[0,0,1],[0,-1,0],[0,60,-130,0]),
([-200,-130,990],[0,0,1],[1,0,0],[0,60,0,20]),
([-200,-130,1050],[1,0,0],[0,1,0],[0,20,0,130]),
([-200,-130,990],[1,0,0],[0,1,0],[0,20,0,130]),
([-200,0,990],[0,0,1],[1,0,0],[0,60,0,20]),
([-201,-116,999],[1,0,0],[0,1,0],[1,21,0,22]),
([-201,-94,999],[0,0,1],[1,0,0],[0,42,1,21]),
([-201,-116,1041],[1,0,0],[0,1,0],[1,21,0,22]),
([-201,-116,999],[0,0,1],[1,0,0],[0,42,1,21]),
([-180,-130,990],[0,0,1],[0,-1,0],[0,60,-130,0]),
]

def synthetic():
    native={'schema':1,'occt':'7.8.1',
            'ieee_binary64_round_to_nearest':True,'face_count':10,'faces':[]}
    trim={'source_fcstd_sha256':'c3ca0f1ee580fbb4665c4039dfd63200a73c77eaea6ef3114a0d17bd56d70d1a',
          'source_d2_sha256':'88cf09ddd61a59faa3699bd8f0779b6c9cc060edfef04383575b0701126034fa',
          'parts':{'GATE_BoltGuide_Left':{
              'source_brep_sha256':'043b1fb89aad7bf3004afeb1bf62c352e47250420c4e6f6f852265125e3cf261',
              'status':'PASS','faces':[]}}}
    t=(-540,0,100)
    tr=[[1,0,0,t[0]],[0,1,0,t[1]],[0,0,1,t[2]],[0,0,0,1]]
    trim['parts']['GATE_BoltGuide_Left']['shape_location']=[list(map(str,row)) for row in tr]
    for i,(o,u,v,b) in enumerate(WORLD):
        native_t=list(t) if i not in (5,6,7,8) else [-201,-116,999]
        local=[o[j]-native_t[j] for j in range(3)]
        orientation='Reversed' if i in (0,1,3,6,7) else 'Forward'
        native['faces'].append({
            'face_index':i,'orientation':orientation,
            'local_plane_origin_mm':local,'native_u_direction':u,
            'native_v_direction':v,'translation_mm':native_t,
            'transform_form':'Translation',
            'raw_transform_form_enum':2,
            'native_affine_matrix_is_identity':True,
            'native_face_uv_bounds':list(b)})
        trim['parts']['GATE_BoltGuide_Left']['faces'].append({
            'face':i,'orientation':orientation,'plane':[list(map(str,row)) for row in (o,u,v)],
            'location':[list(map(str,row)) for row in tr],
            'uv_bounds':list(map(str,b))})
    prior={'status':'PASS','face_count':10,'full_face_oriented_pcurve_uses':48,
           'exact_represented_boundary_min_distance_sq_mm2':'1',
           'native_full_q_void_inclusion':'UNKNOWN',
           'face_results':[{'exact_boundary_to_q_distance_sq_mm2':'1'} for _ in range(10)]}
    return native,trim,prior


class PlaneRoundoffTests(unittest.TestCase):
    def test_fixed_face_frames_and_bound(self):
        r=analyze(*synthetic())
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['native_raw_frame_equal_saved_world_planes'],'PASS')
        self.assertLess(Q(r['max_point_coordinate_roundoff_upper_exact_mm']),Q('1e-10'))
        self.assertGreater(Q(r['conditional_evaluated_plane_point_distance_to_exact_q_lower_exact_mm']),
                           Q('0.9999999999'))
        self.assertEqual(r['brep_extrema_total_error_status'],'UNKNOWN')
        self.assertEqual(r['native_full_q_void_inclusion'],'UNKNOWN')
        self.assertEqual(len(r['face_details']),10)
        self.assertEqual([x['face'] for x in r['face_details']
                          if x['native_location_differs_from_freecad_shape_placement']],
                         [5,6,7,8])

    def test_exact_gamma_and_outward_decimals(self):
        self.assertEqual(EPS,Q(1,2**53))
        self.assertLess(GAMMA16,Q('2e-15'))
        z=bound_for_coordinate(340,0,0,-540,Q(60),Q(130))
        self.assertGreater(z,0)
        self.assertGreaterEqual(outward_up(z),z)
        self.assertLessEqual(outward_down(Q(1)-2*z),Q(1)-2*z)

    def test_native_face_frame_and_location_faults_fail_closed(self):
        for change in ('position','axis','translate','assembly','uv_bounds','mode','matrix','mirror','rounding'):
            n,t,p=synthetic()
            if change=='position':n['faces'][6]['local_plane_origin_mm'][1]=-95
            if change=='axis':n['faces'][6]['native_v_direction'][0]=0.5
            if change=='translate':n['faces'][6]['translation_mm'][0]=-539
            if change=='assembly':t['parts']['GATE_BoltGuide_Left']['faces'][6]['location'][0][3]='-539'
            if change=='uv_bounds':n['faces'][9]['native_face_uv_bounds'][1]=61
            if change=='mode':n['faces'][0]['transform_form']='Scale'
            if change=='matrix':n['faces'][0]['native_affine_matrix_is_identity']=False
            if change=='mirror':n['faces'][0]['raw_transform_form_enum']=3
            if change=='rounding':n['ieee_binary64_round_to_nearest']=False
            with self.subTest(change=change),self.assertRaises(ValueError):
                analyze(n,t,p)

    def test_no_prior_model_or_unknown_scope_rejected(self):
        for kind in ('model_status','model_distance','numeric_scope'):
            n,t,p=synthetic()
            if kind=='model_status':p['status']='FAIL'
            if kind=='model_distance':p['exact_represented_boundary_min_distance_sq_mm2']='0'
            if kind=='numeric_scope':p['native_full_q_void_inclusion']='PASS'
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                analyze(n,t,p)

if __name__=='__main__':
    unittest.main()
