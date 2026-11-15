import unittest
from fractions import Fraction as F
from intervals import classify,validate_cover

def oracle(distance,certified=True,error=0):
 return lambda x:dict(distance=str(distance(x)),certified=certified,absolute_error=error,contact='CLEAR')
class Intervals(unittest.TestCase):
 def test_normal(self):
  r=classify(0,1,oracle(lambda x:2),1);self.assertTrue(all(x['status']=='PASS' for x in r));validate_cover(r,0,1)
 def test_midpoint_collision(self):
  # Points at 0 and 1 miss the sphere/obstacle contact at 1/2.
  d=lambda x:max(F(0),abs(x-F(1,2))-F(1,100))
  self.assertGreater(d(F(0)),0);self.assertGreater(d(F(1)),0)
  def sample(x):return dict(distance=str(d(x)),certified=True,absolute_error=0,penetration_proven=abs(x-F(1,2))<F(1,100),contact='PENETRATION' if d(x)==0 else 'CLEAR')
  r=classify(0,1,sample,1);self.assertEqual(r[0]['status'],'FAIL');validate_cover(r,0,1)
 def test_unknown_error(self):
  r=classify(0,1,oracle(lambda x:100,False,None),1,max_depth=2);self.assertEqual(len(r),4);self.assertTrue(all(x['status']=='UNKNOWN' for x in r))
 def test_touching(self):self.assertTrue(all(x['status']=='UNKNOWN' for x in classify(0,1,oracle(lambda x:0),0,max_depth=1)))
 def test_error_not_ignored(self):self.assertEqual(classify(0,1,oracle(lambda x:1,True,2),0,max_depth=0)[0]['status'],'UNKNOWN')
 def test_motion_not_ignored(self):self.assertEqual(classify(0,1,oracle(lambda x:1),4,max_depth=0)[0]['status'],'UNKNOWN')
 def test_cover_faults(self):
  for r in [[],[{'lo':'0','hi':'0.4'},{'lo':'0.5','hi':'1'}],[{'lo':'0','hi':'0.6'},{'lo':'0.5','hi':'1'}]]:
   with self.assertRaises(ValueError):validate_cover(r,0,1)
 def test_invalid(self):
  for args in [(1,0,1),(0,1,-1)]:
   with self.assertRaises(ValueError):classify(args[0],args[1],oracle(lambda x:1),args[2])
 def test_recursion_budget_input(self):
  for depth in [-1,-10000,True,0.5,1]:
   with self.assertRaises(ValueError):classify(0,1,oracle(lambda x:0),0,max_depth=0,depth=depth)
  for budget in [True,False,0.5,-1,13]:
   with self.assertRaises(ValueError):classify(0,1,oracle(lambda x:0),0,max_depth=budget)
 def test_refinement_normal(self):
  r=classify(0,1,oracle(lambda x:F(1,10)),1);self.assertTrue(all(x['status']=='PASS' for x in r));validate_cover(r,0,1)
if __name__=='__main__':unittest.main()
