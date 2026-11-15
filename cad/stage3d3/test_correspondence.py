"""Portable metadata/contract controls, distinct from native BRep mutation runs."""
import copy
import unittest
from correspondence import SOURCES, PARTS, evaluate


def reference():
    return {'sources':dict(SOURCES), 'unit':'mm', 'coordinate_frame':'FreeCAD world; project m -> native mm x1000',
            'door_degrees':0, 'travel_mm':[0,140],
            'parts':{p:{'valid':True,'solids':1,'brep_sha256':'synthetic-only','placement_observed':'synthetic'} for p in PARTS}}


class Gate(unittest.TestCase):
    def check_change(self, mutate, reason):
        r=reference(); o=copy.deepcopy(r); mutate(o)
        result=evaluate(o,r)
        self.assertEqual(result['status'],'REJECTED')
        self.assertIn(reason,result['reasons'])
        self.assertEqual(result['d2_cad_application'],'UNKNOWN')
    def test_normal_is_not_proof(self):
        r=reference(); v=evaluate(r,r)
        self.assertEqual(v['observed_contract'],'PASS'); self.assertEqual(v['status'],'UNKNOWN')
        self.assertEqual(v['cad_intervals'],{'PASS':0,'FAIL':0,'UNKNOWN':128})
    def test_unit(self):self.check_change(lambda o:o.update(unit='m'),'UNIT_MISMATCH')
    def test_source(self):self.check_change(lambda o:o['sources'].update({'extra':'x'}),'SOURCE_IDENTITY_MISMATCH')
    def test_hash(self):self.check_change(lambda o:o['sources'].update({next(iter(SOURCES)):'0'*64}),'SOURCE_IDENTITY_MISMATCH')
    def test_missing(self):self.check_change(lambda o:o['parts'].pop(PARTS[0]),'PART_SET_MISMATCH')
    def test_added(self):self.check_change(lambda o:o['parts'].update(extra={}), 'PART_SET_MISMATCH')
    def test_shape(self):self.check_change(lambda o:o['parts'][PARTS[0]].update(brep_sha256='different'), 'SHAPE_OR_PLACEMENT_CHANGED:'+PARTS[0])
    def test_placement(self):self.check_change(lambda o:o['parts'][PARTS[1]].update(placement_observed='shift'), 'SHAPE_OR_PLACEMENT_CHANGED:'+PARTS[1])
    def test_range(self):self.check_change(lambda o:o.update(travel_mm=[0,141]), 'MOTION_CONTRACT_MISMATCH')
    def test_angle(self):self.check_change(lambda o:o.update(door_degrees=1), 'MOTION_CONTRACT_MISMATCH')
    def test_frame(self):self.check_change(lambda o:o.update(coordinate_frame='local'), 'COORDINATE_FRAME_MISMATCH')
    def test_invalid_solid(self):self.check_change(lambda o:o['parts'][PARTS[0]].update(valid=False),'INVALID_OBSERVED_SOLID:'+PARTS[0])
    def test_extra_solid(self):self.check_change(lambda o:o['parts'][PARTS[0]].update(solids=2),'INVALID_OBSERVED_SOLID:'+PARTS[0])
    def test_forged_proof(self):
        r=reference();o=copy.deepcopy(r);o.update(shape_containment='PASS',proof={'trusted':True})
        self.assertEqual(evaluate(o,r)['shape_containment'],'UNKNOWN')
    def test_absent_reference(self):
        self.assertNotEqual(evaluate(reference(),{})['status'],'PASS')
    def test_numeric_equality_not_proof(self):
        r=reference();r.update(difference_volume=0,tolerance=1e-7,observed_distance=1)
        self.assertEqual(evaluate(r,r)['status'],'UNKNOWN')

if __name__=='__main__':unittest.main()
