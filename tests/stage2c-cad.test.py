import unittest,sys,json,copy,zipfile,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cad/stage2c'))
import check
class Contract(unittest.TestCase):
 def setUp(self):
  self.p=check.ROOT/'cad/stage2c/generated/B0';self.audit=json.loads((self.p/'native-audit.json').read_text());self.rows=self.audit['restored']
 def test_complete_outputs_and_preservation(self):self.assertEqual(check.check()['preserved_files'],839)
 def test_missing_duplicate_unknown_dimensions(self):
  for mutate in [lambda x:x.pop(),lambda x:x.__setitem__(1,copy.deepcopy(x[0])),lambda x:x[0].__setitem__('id','UNKNOWN')]:
   rows=copy.deepcopy(self.rows);mutate(rows)
   with self.assertRaises(AssertionError):check.validate_dimensions(rows,'B0','value_mm',1000)
 def test_type_values_and_projected_rejected(self):
  for value in [None,False,'2200',float('nan'),2400]:
   rows=copy.deepcopy(self.rows);rows[0]['value_mm']=value
   with self.assertRaises(AssertionError):check.validate_dimensions(rows,'B0','value_mm',1000)
  rows=copy.deepcopy(self.rows);rows[0]['kind']='projected'
  with self.assertRaises(AssertionError):check.validate_dimensions(rows,'B0','value_mm',1000)
 def test_stale_revision(self):
  with self.assertRaises(AssertionError):check.validate_dimensions(self.rows,'B2','value_mm',1000)
 def test_fcstd_reference_and_expression_faults(self):
  xml=zipfile.ZipFile(self.p/'assembly.FCStd').read('Document.xml')
  for field in ['References3D','References2D','Arbitrary','FormatSpec','ExpressionEngine']:
   tree=E.fromstring(xml);obj='Witness_U01_post_height' if field=='ExpressionEngine' else 'Dim_U01_post_height';p=tree.find(f'./ObjectData/Object[@name="{obj}"]/Properties/Property[@name="{field}"]')
   if field.startswith('References'):p.find('.//Link').attrib['obj']='WrongObject'
   elif field=='ExpressionEngine':p.find('.//Expression').attrib['expression']='2200 mm'
   elif field=='Arbitrary':p.find('Bool').attrib['value']='true'
   else:p.find('String').attrib['value']='2200'
   with self.assertRaises((AssertionError,KeyError)):check.validate_xml(E.tostring(tree),self.rows)
if __name__=='__main__':unittest.main()
