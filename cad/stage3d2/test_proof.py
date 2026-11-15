import copy,json,unittest
from pathlib import Path
from fractions import Fraction as Q
from proof import verify,digest,sqrt_enclosure
C=json.loads(Path(__file__).with_name('contract.json').read_text())
def run(c=None,depth=8):
 c=c or copy.deepcopy(C);return verify(c,digest(c),c['sources'],depth)
def fixture(a,b,v=(0,0,0),w=(0,0,0),range_=('0','1')):
 c=copy.deepcopy(C);c.update(moving_box=list(map(str,a)),obstacle_boxes=[list(map(str,b))],moving_velocity=list(map(str,v)),obstacle_velocity=list(map(str,w)),range=list(range_));return c
class Proofs(unittest.TestCase):
 def test_representative(self):
  r=run();self.assertEqual(len(r['intervals']),128);self.assertEqual({x['status'] for x in r['intervals']},{'PASS'});self.assertEqual(r['cad_application']['status'],'UNKNOWN');self.assertEqual({x['distance_squared'] for x in r['intervals']},{'1'})
 def test_touch(self):self.assertEqual(run(fixture([0,0,0,1,1,1],[1,0,0,2,1,1]),0)['intervals'][0]['contact'],'CONTACT')
 def test_touch_unknown(self):self.assertEqual(run(fixture([0,0,0,1,1,1],[1,0,0,2,1,1]),0)['intervals'][0]['status'],'UNKNOWN')
 def test_penetration(self):self.assertEqual(run(fixture([0,0,0,2,2,2],[1,1,1,3,3,3]),0)['intervals'][0]['status'],'FAIL')
 def test_normal(self):self.assertEqual(run(fixture([0,0,0,1,1,1],[2,0,0,3,1,1]),0)['intervals'][0]['status'],'PASS')
 def test_midpoint_collision(self):
  c=fixture([0,0,0,'1/100',1,1],['1/2',0,0,'51/100',1,1],v=(1,0,0));r=run(c,0);self.assertEqual(r['intervals'][0]['status'],'FAIL')
 def test_boundary(self):
  c=fixture([0,0,0,1,1,1],[2,0,0,3,1,1]);c['required_clearance']='1';self.assertEqual(run(c,0)['intervals'][0]['status'],'UNKNOWN')
 def test_relative_motion(self):
  c=fixture([0,0,0,1,1,1],[2,0,0,3,1,1],v=(1,0,0),w=(1,0,0));self.assertEqual(run(c,0)['guarantees']['motion_upper']['L'],'0');self.assertEqual(run(c,0)['intervals'][0]['status'],'PASS')
 def test_opponent_moving(self):
  c=fixture([0,0,0,1,1,1],[3,0,0,4,1,1],w=(-4,0,0));self.assertEqual(run(c,0)['intervals'][0]['status'],'UNKNOWN')
 def test_sqrt(self):
  for q in [Q(0),Q(1),Q(2),Q(1,3),Q(10**100+3,7)]:
   lo,hi=sqrt_enclosure(q);self.assertLessEqual(lo*lo,q);self.assertGreaterEqual(hi*hi,q);self.assertLessEqual(hi-lo,Q(1,2**32))
 def test_wrong_unit(self):
  c=copy.deepcopy(C);c['unit']='m'
  with self.assertRaises(ValueError):run(c)
 def test_invalid_numeric(self):
  for bad in [True,float('nan'),'NaN','Infinity','1/0']:
   c=copy.deepcopy(C);c['moving_box'][0]=bad
   with self.assertRaises((ValueError,ZeroDivisionError)):run(c)
 def test_absent_guarantee_source(self):
  c=copy.deepcopy(C);c['sources']={}
  with self.assertRaises(ValueError):run(c)
 def test_source_mismatch(self):
  with self.assertRaises(ValueError):verify(C,digest(C),{})
 def test_shape_mismatch(self):
  c=copy.deepcopy(C);c['moving_box'][3]='900'
  with self.assertRaises(ValueError):verify(c,digest(C),C['sources'])
 def test_placement_mismatch(self):
  c=copy.deepcopy(C);c['obstacle_boxes'][0][0]='-199'
  with self.assertRaises(ValueError):verify(c,digest(C),C['sources'])
 def test_depth(self):
  for n in [-1,11,True,0.1]:
   with self.assertRaises(ValueError):run(depth=n)
 def test_unproved_at_limit(self):self.assertEqual(run(depth=0)['intervals'][0]['status'],'UNKNOWN')
 def test_bad_box(self):
  c=copy.deepcopy(C);c['moving_box'][3]=c['moving_box'][0]
  with self.assertRaises(ValueError):run(c)
 def test_part_binding(self):
  c=copy.deepcopy(C);c['parts'][0]='other'
  with self.assertRaises(ValueError):run(c)
if __name__=='__main__':unittest.main()
