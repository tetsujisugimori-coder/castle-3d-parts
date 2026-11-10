import sys,json,tempfile,shutil,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from check import check,ROOT,h
class Controls(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(prefix='gate-check-');self.r=Path(self.t.name)
  for p in ['cad/stage3a','blender/stage3a']:shutil.copytree(ROOT/p,self.r/p)
 def tearDown(self):self.t.cleanup()
 def mutate(self,path,fn,rehash=True):
  p=self.r/path;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
  if rehash and p.name!='generation-manifest.json':
   m=p.parent/'generation-manifest.json';v=json.loads(m.read_text());v['outputs'][p.name]=h(p);m.write_text(json.dumps(v))
 def reject(self):
  with self.assertRaises((AssertionError,KeyError,StopIteration)):check(self.r)
 def test_positive(self):self.assertEqual(check(self.r)['status'],'PASS')
 def test_hash_omission(self):self.mutate('cad/stage3a/generated/B0/generation-manifest.json',lambda x:x['outputs'].pop('assembly.glb'));self.reject()
 def test_duplicate_id(self):self.mutate('cad/stage3a/generated/B0/blender-audit.json',lambda x:x['glb_reopened']['components'].__setitem__(0,x['glb_reopened']['components'][1]));self.reject()
 def test_short_bounds(self):self.mutate('cad/stage3a/generated/B0/blender-audit.json',lambda x:x['glb_reopened']['components'][0].__setitem__('bounds_m',[]));self.reject()
 def test_pose_mix(self):self.mutate('cad/stage3a/generated/B0/cad-audit.json',lambda x:x['pose'].__setitem__('angle_degrees',90));self.reject()
 def test_source_mismatch(self):self.mutate('cad/stage3a/generated/B0/generation-manifest.json',lambda x:x.__setitem__('source_commit','wrong'));self.reject()
 def test_script_omission(self):self.mutate('cad/stage3a/generated/B0/generation-manifest.json',lambda x:x['source_scripts'].pop('cad/stage3a/build.py'));self.reject()
 def test_empty_poses(self):
  p=self.r/'cad/stage3a/spec.json';s=json.loads(p.read_text());s['poses']=[];p.write_text(json.dumps(s));self.reject()
 def test_duplicate_connection_side(self):
  p=self.r/'cad/stage3a/generated/connection-audit.json';s=json.loads(p.read_text());s['rows'][0]['connections'][1]['side']='left';p.write_text(json.dumps(s));self.reject()
 def test_negative_connection_distance(self):
  p=self.r/'cad/stage3a/generated/connection-audit.json';s=json.loads(p.read_text());s['rows'][0]['connections'][0]['upper_rail_connector_distance_m']=-1;p.write_text(json.dumps(s));self.reject()
 def test_swapped_native_pose(self):
  a=self.r/'cad/stage3a/generated/B0/assembly.FCStd';b=self.r/'cad/stage3a/generated/B1/assembly.FCStd';a.write_bytes(b.read_bytes())
  p=a.parent/'generation-manifest.json';v=json.loads(p.read_text());v['outputs']['assembly.FCStd']=h(a);p.write_text(json.dumps(v));self.reject()
if __name__=='__main__':unittest.main()
