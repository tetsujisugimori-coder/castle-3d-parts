import unittest,json,tempfile,shutil
from pathlib import Path
from check import verify,ROOT
class Faults(unittest.TestCase):
 def test_original(self):self.assertEqual(verify()['result'],'PASS')
 def mutate(self,file,fn):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td);shutil.copytree(ROOT/'cad/stage3b/generated',out,dirs_exist_ok=True);p=out/file;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
   with self.assertRaises((AssertionError,KeyError,ValueError)):verify(out)
 def test_axis(self):self.mutate('manifest.json',lambda v:v.update(pivot_m=[0,0,0]))
 def test_missing_part(self):self.mutate('manifest.json',lambda v:v['parts'].pop())
 def test_duplicate_id(self):self.mutate('manifest.json',lambda v:v['parts'][0].update(id=v['parts'][1]['id']))
 def test_missing_angle(self):self.mutate('collision.json',lambda v:v['samples'].pop())
 def test_penetration(self):self.mutate('collision.json',lambda v:v['samples'][0]['pairs'][0].update(overlap_mm3=1))
 def test_wrong_hash(self):self.mutate('manifest.json',lambda v:v['glb'].update(sha256='0'*64))
 def test_missing_reload(self):self.mutate('cad-audit.json',lambda v:v.update(step_reloaded=False))
 def test_angle_limit(self):self.mutate('manifest.json',lambda v:v.update(angle_range_deg=[0,120]))
 def test_empty_pairs(self):self.mutate('collision.json',lambda v:v['samples'][0].update(pairs=[]))
 def test_infinite_gap(self):self.mutate('collision.json',lambda v:v['samples'][0]['pairs'][0].update(distance_m=float('nan')))
 def test_shifted_bounds(self):self.mutate('blender-audit.json',lambda v:v['glb_reopened'][0]['bounds_m'].__setitem__(0,42))
 def test_missing_tolerance(self):self.mutate('collision.json',lambda v:v.pop('tolerance_mm3'))
 def test_missing_fixed_pair(self):self.mutate('collision.json',lambda v:v['fixed_pairs'].pop())
 def test_overclaim(self):self.mutate('collision.json',lambda v:v.update(continuous_path='PASS'))
if __name__=='__main__':unittest.main()
