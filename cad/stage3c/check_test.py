import unittest,json,copy
from pathlib import Path
from check import validate_pairs,pairs_expected,IDS,MOVING,validate_sources,validate_contacts,SOURCES,CONTACTS
class Faults(unittest.TestCase):
 def rows(self):return [{'a':a,'b':b,'distance_m':.01,'overlap_mm3':0,'contact':'CLEAR'} for a,b in sorted(pairs_expected({'GATE_Bolt'}))]
 def test_complete(self):validate_pairs(self.rows(),pairs_expected({'GATE_Bolt'}),.0001)
 def test_omission(self):
  r=self.rows();r.pop()
  with self.assertRaises(AssertionError):validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_mutations(self):
  for field,value in [('overlap_mm3',1),('overlap_mm3',float('nan')),('distance_m',-1),('distance_m',float('inf')),('contact','PASS'),('a','missing')]:
   with self.subTest(field=field,value=value):
    r=self.rows();r[0][field]=value
    with self.assertRaises(AssertionError):validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_duplicate(self):
  r=self.rows();r[-1]=r[0]
  with self.assertRaises(AssertionError):validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_positive_zero_distance(self):
  r=self.rows();r[0].update(distance_m=0,overlap_mm3=1,contact='CLEAR')
  with self.assertRaises(AssertionError):validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_true_contact(self):
  r=self.rows();r[0].update(distance_m=0,overlap_mm3=0,contact='TOUCHING');validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_self_pair(self):
  r=self.rows();r[0]['b']=r[0]['a']
  with self.assertRaises(AssertionError):validate_pairs(r,pairs_expected({'GATE_Bolt'}),.0001)
 def test_source_coverage(self):
  validate_sources(dict.fromkeys(SOURCES,'hash'))
  for missing in SOURCES:
   with self.subTest(missing=missing),self.assertRaises(AssertionError):validate_sources(dict.fromkeys(SOURCES-{missing},'hash'))
 def test_empty_sources(self):
  with self.assertRaises(AssertionError):validate_sources({})
 def test_contact_identity(self):
  rows=[{'a':a,'b':b} for a,b in sorted(CONTACTS)];validate_contacts(rows);rows[-1]=rows[0]
  with self.assertRaises(AssertionError):validate_contacts(rows)
 def test_count(self):self.assertEqual((len(IDS),len(MOVING),len(pairs_expected(MOVING)),len(pairs_expected({'GATE_Bolt'}))),(38,9,297,37))
if __name__=='__main__':unittest.main()
