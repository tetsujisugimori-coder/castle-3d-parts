"""Portable archive/evidence consistency, not replacement for native execution."""
import json,hashlib,zipfile,math,sys,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(root=ROOT):
 out=root/'cad/stage3a/generated';spec=json.loads((root/'cad/stage3a/spec.json').read_text());count=0
 assert spec['poses']==[{'id':'B0','angle_degrees':0},{'id':'B1','angle_degrees':45},{'id':'B2','angle_degrees':90}],'POSE_SET'
 names={'GATE_Post_Left','GATE_Post_Right','GATE_Beam','GATE_Door','GATE_Axis','GATE_Connector_Left','GATE_Connector_Right'}
 def parts(rows):
  assert len(rows)==7 and {x['id'] for x in rows}==names
  for x in rows:assert len(x['bounds_m'])==6 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in x['bounds_m'])
 for pose in spec['poses']:
  d=out/pose['id'];m=json.loads((d/'generation-manifest.json').read_text());assert m['spec_sha256']==h(root/'cad/stage3a/spec.json')
  assert set(m['source_scripts'])=={'cad/stage3a/build.py','cad/stage3a/link.py','cad/stage3a/run.py','blender/stage3a/build.py','cad/stage3a/connection.py','cad/stage3a/faults.py','cad/stage3a/check.py','cad/stage3a/check_test.py'}
  required={'assembly.FCStd','assembly.step','assembly.blend','assembly.glb','mesh-transfer.json','cad-audit.json','native-audit.json','blender-audit.json','native-front.svg','native-top.svg','native-side.svg','native-pivot.svg','native-connection.svg','link-manifest.json','drawing.svg','parameter-variation.FCStd','pose-variation.FCStd','page-template.svg'}
  assert set(m['outputs'])==required
  assert m['source_commit']=='1cc50d1a6d1af8164cada51124cb02279dbe316c' and m['revision']==pose['id']
  for p,v in m['source_scripts'].items():assert h(root/p)==v,('SCRIPT_HASH',p)
  for p,v in m['outputs'].items():assert Path(p).name==p and h(d/p)==v,('OUTPUT_HASH',p)
  with zipfile.ZipFile(d/'assembly.FCStd') as z:
   assert z.testzip() is None;xml=E.fromstring(z.read('Document.xml'))
  objects={o.attrib['name']:o for o in xml.findall('./ObjectData/Object')}
  def prop(name,key):return objects[name].find('./Properties/Property[@name="'+key+'"]')
  assert {k for k in objects if prop(k,'PartID') is not None}==names,'XML_PART_SET'
  for name in names:
   assert prop(name,'PartID').find('String').attrib['value']==name
   assert prop(name,'Revision').find('String').attrib['value']=='GATE-SIMPLE-01/'+pose['id']
  angle=float(prop('Parameters','pose_angle').find('Float').attrib['value'])
  assert abs(angle-pose['angle_degrees'])<1e-8,'XML_POSE'
  placement=prop('GATE_Door','Placement').find('PropertyPlacement').attrib
  assert abs(float(placement['A'])*180/math.pi-angle)<1e-8,'XML_ROTATION'
  expr={e.attrib['path']:e.attrib['expression'] for e in prop('GATE_Door','ExpressionEngine').iter('Expression')}
  assert expr['.Placement.Rotation.Angle']=='Parameters.pose_angle','XML_ROTATION_EXPRESSION'
  assert {x.attrib['value'] for x in prop('ConnectionView','Source').iter('Link')}=={'GATE_Post_Left','GATE_Connector_Left','Reference_U01_Post_005','Reference_U01_Rail_002'},'XML_FENCE_REFERENCE'
  for dim in ['beam_length','post_height','opening','door_width','door_height','door_thickness','axis_radius','connector_length']:
   assert prop('Dim_'+dim,'Arbitrary').find('Bool').attrib['value']=='false'
   assert prop('Dim_'+dim,'MeasureType').find('Integer').attrib['value']=='0'
   assert [(x.attrib['obj'],x.attrib['sub']) for x in prop('Dim_'+dim,'References3D').iter('Link')]==[('Witness_'+dim,'Edge1')],'XML_DIM_REFERENCE'
  p=spec['parameters'];theta=pose['angle_degrees']*math.pi/180
  vectors={'beam_length':[p['opening']+2*p['post_width'],0,0],'post_height':[0,0,p['post_height']],'opening':[p['opening'],0,0],'door_width':[p['door_width']*math.cos(theta),p['door_width']*math.sin(theta),0],'door_height':[0,0,p['door_height']],'door_thickness':[-p['door_thickness']*math.sin(theta),p['door_thickness']*math.cos(theta),0],'axis_radius':[p['axis_radius'],0,0],'connector_length':[p['connector_length'],0,0]}
  for dim,vector in vectors.items():
   vals=[float(prop('Witness_'+dim,k).find('Float').attrib['value'])/1000 for k in ['X1','Y1','Z1','X2','Y2','Z2']]
   assert all(abs(vals[i+3]-vals[i]-vector[i])<1e-8 for i in range(3)),('XML_WITNESS_DIRECTION',dim)
  assert 'Scale 1:16.667' in (d/'page-template.svg').read_text() and 'Two unconnected' not in (d/'page-template.svg').read_text()
  a=json.loads((d/'cad-audit.json').read_text());assert a['step_reopened'] and a['parameter_edit_save_reopen'];assert a['pose']==pose;assert a['pose_parameter_edit_save_reopen']=={'angle_degrees':30,'reopened_angle_degrees':30,'restored_degrees':pose['angle_degrees']}
  for phase in ['created','fcstd_reopened']:
   parts(a[phase]['components']);assert a[phase]['solids']==7 and len(a[phase]['components'])==7 and len(a[phase]['pairwise_clearances'])==21
   assert all(v['overlap_mm3']<1e-4 and v['distance_m']>=0 for v in a[phase]['pairwise_clearances'])
  n=json.loads((d/'native-audit.json').read_text());assert n['created']==n['reopened']==n['restored'];assert len(n['restored'])==8;assert next(x for x in n['parameter_variation_reopened'] if x['id']=='post-height')['value_m']==2.3;assert len(n['fault_controls'])==2 and all(x['result']=='REJECT' for x in n['fault_controls'])
  b=json.loads((d/'blender-audit.json').read_text())
  for phase in ['created','blend_reopened','glb_reopened']:
   parts(b[phase]['components']);assert b[phase]['objects']==7
   for c in b[phase]['components']:
    e=next(x for x in a['created']['components'] if x['id']==c['id']);assert c['part_id']==e['part_id'] and c['revision']==e['revision'];assert all(abs(x-y)<1e-5 for x,y in zip(c['bounds_m'],e['bounds_m']))
  count+=1
 c=json.loads((out/'connection-audit.json').read_text());assert len(c['rows'])==3 and {x['pose'] for x in c['rows']}=={'B0','B1','B2'}
 for r in c['rows']:
  assert len(r['post_contacts'])==2 and {x['side'] for x in r['post_contacts']}=={'left','right'}
  assert all(x['contact_area_m2']>0 and x['overlap_mm3']<1e-4 for x in r['post_contacts'])
  assert len(r['connections'])==2 and {x['side'] for x in r['connections']}=={'left','right'}
  for x in r['connections']:assert x['pair_tests']==49 and x['penetration']=='NONE' and 0<=x['upper_rail_connector_distance_m']<1e-9
 faults=json.loads((out/'fault-audit.json').read_text());assert len(faults['cases'])==5 and all(x['actual']=='REJECT' for x in faults['cases'])
 return {'status':'PASS','poses':count,'gate_parts_per_pose':7,'native_dimensions_per_pose':8,'gate_pair_checks':63,'fence_pair_checks':294,'native_dimension_fault_controls':6,'additional_fault_controls':5,'native_execution':'recorded separately; this checker is portable'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
