"""Portable verification of preserved native evidence, not a CAD rerun."""
import json,hashlib,struct,math,itertools,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def verify(out=None):
 out=Path(out or ROOT/'cad/stage3b/generated');m=json.loads((out/'manifest.json').read_text());c=json.loads((out/'collision.json').read_text());cad=json.loads((out/'cad-audit.json').read_text());bl=json.loads((out/'blender-audit.json').read_text())
 assert m['basis']=='D' and m['unit']=='m' and m['up']=='Z'
 assert m['pivot_m']==[-.54,0,.1] and m['angle_range_deg']==[0,90]
 ids=[p['id'] for p in m['parts']];assert len(ids)==15 and len(set(ids))==15
 assert set(m['moving_ids'])<=set(ids) and len(m['moving_ids'])==6
 assert cad['fcstd_reloaded'] and cad['step_reloaded'] and cad['native_dimension_edit'];assert cad['parts']==15
 assert len(cad['legacy_poses'])==3 and [x['angle_degrees'] for x in cad['legacy_poses']]==[0,45,90]
 assert c['continuous_path']=='UNKNOWN' and not c['failures']
 assert c['tolerance_mm3']==1e-4
 allids=m['collision_ids'];assert len(allids)==30 and len(set(allids))==30 and set(ids)<=set(allids)
 expected={tuple(sorted(x)) for x in itertools.combinations(allids,2) if any(a in m['moving_ids'] for a in x)}
 fixed={tuple(sorted(x)) for x in itertools.combinations(allids,2) if not any(a in m['moving_ids'] for a in x)}
 assert {tuple(sorted([p['a'],p['b']])) for p in c['fixed_pairs']}==fixed
 assert all(math.isfinite(p['overlap_mm3']) and p['overlap_mm3']<=1e-4 and math.isfinite(p['distance_m']) and p['distance_m']>=0 for p in c['fixed_pairs'])
 assert hashlib.sha256((out/'collision.json').read_bytes()).hexdigest()==m['collision']['sha256']
 assert [x['angle_degrees'] for x in c['samples']]==list(range(91))
 pairsets=[]
 for sample in c['samples']:
  pairs=sample['pairs'];keys=[tuple(sorted([p['a'],p['b']])) for p in pairs];assert len(keys)==len(set(keys)) and set(keys)==expected
  for p in pairs:
   assert isinstance(p['distance_m'],(int,float)) and math.isfinite(p['distance_m']) and p['distance_m']>=0
   assert isinstance(p['overlap_mm3'],(int,float)) and math.isfinite(p['overlap_mm3']) and -1e-8<=p['overlap_mm3']<=c['tolerance_mm3']
   assert p['contact'] in ['CLEAR','TOUCHING']
  pairsets.append(set(keys))
 assert all(s==pairsets[0] for s in pairsets)
 for k in ['created','blend_reopened','glb_reopened']:
  assert {x['id'] for x in bl[k]}==set(ids)
  for x in bl[k]:
   ref=next(p['bounds_m'] for p in m['parts'] if p['id']==x['id']);assert len(x['bounds_m'])==6 and all(math.isfinite(a) and abs(a-b)<1e-5 for a,b in zip(x['bounds_m'],ref))
 with zipfile.ZipFile(out/'assembly.FCStd') as z:
  xml=z.read('Document.xml').decode();assert 'Mechanism.Angle' in xml and 'Mechanism.MaximumAngle' in xml and 'Mechanism.MinimumAngle' in xml
 for name,sha in m.get('evidence_hashes',{}).items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
 assert len(m.get('evidence_hashes',{}))>=10
 for name,sha in m['source_hashes'].items():assert hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()==sha
 drawing=json.loads((out/'drawing-audit.json').read_text());limits=json.loads((out/'limit-audit.json').read_text());assert limits['saved_reopened_range']==[10,60] and limits['saved_reopened_angle']==35 and len(limits['endpoint_contacts'])==2 and all(x['overlap_mm3']<=1e-4 and x['gap_m']<1e-9 for x in limits['endpoint_contacts'])
 assert drawing['saved_reopened'] and drawing['radial_gap_mm']==.5 and len(drawing['native_dimensions'])==3
 raw=(out/m['glb']['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==m['glb']['sha256'];assert raw[:4]==b'glTF';length,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+length]);assert any(n.get('name')=='GatePivot' for n in g['nodes'])
 assert len(g.get('animations',[]))>=1
 for kind in ['blend_animation','glb_animation']:
  assert [x['angle_degrees'] for x in bl[kind]]==[0,45,90,0] and all(x['parts']==15 and x['independent_vertex_rotation']=='PASS' for x in bl[kind])
 nt=json.loads((out/'native-tests.json').read_text());assert nt['fresh_reload'] and len(nt['faults'])>=6 and len(nt['poses_tested'])==27 and len(nt['contacts'])==4
 for f in ['assembly.FCStd','assembly.step','assembly.blend']+[x['path'] for x in m['native_drawings']]:assert (out/f).stat().st_size>100
 return {'result':'PASS','parts':len(ids),'angles':91,'pair_checks':sum(len(x['pairs']) for x in c['samples']),'continuous_path':'UNKNOWN','mode':'portable evidence checks; not native app rerun'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
