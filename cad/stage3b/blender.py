import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
out=Path(sys.argv[sys.argv.index('--')+1]);data=json.loads((out/'mesh-transfer.json').read_text());pivot=Vector(data['pivot_m'])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parent=bpy.data.objects.new('GatePivot',None);bpy.context.collection.objects.link(parent);parent.location=pivot;parent['cad_pivot_m']=list(pivot);parent['axis']='Z';parent['min_angle_deg']=0;parent['max_angle_deg']=90
mat=bpy.data.materials.new('Prototype_D_Timber');mat.diffuse_color=(.43,.255,.12,1)
for e in data['objects']:
 mesh=bpy.data.meshes.new(e['id']);vertices=[list(Vector(v)-pivot) if e['moving'] else v for v in e['vertices_m']];mesh.from_pydata(vertices,[],e['faces']);mesh.update();o=bpy.data.objects.new(e['id'],mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mat);o['part_id']=e['id'];o['basis']='D';o['moving']=e['moving']
 if e['moving']:o.parent=parent
for frame,angle in [(1,0),(46,45),(91,90),(181,0)]:parent.rotation_euler.z=math.radians(angle);parent.keyframe_insert(data_path='rotation_euler',frame=frame)
for fc in parent.animation_data.action.fcurves:
 for kp in fc.keyframe_points:kp.interpolation='LINEAR'
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=181;bpy.context.scene.frame_set(1)
def audit():
 p=bpy.data.objects.get('GatePivot');assert p is not None
 assert (p.location-pivot).length<1e-6
 ans=[]
 for e in data['objects']:
  o=bpy.data.objects.get(e['id']);assert o and o['part_id']==e['id'];assert bool(o.parent and o.parent.name=='GatePivot')==e['moving']
  vs=[o.matrix_world@Vector(v) for v in o.bound_box];b=[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)];assert max(abs(a-c) for a,c in zip(b,e['bounds_m']))<1e-5,(e['id'],b,e['bounds_m']);ans.append({'id':e['id'],'bounds_m':b})
 return ans
def motion_audit():
 result=[]
 for frame,angle in [(1,0),(46,45),(91,90),(181,0)]:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();a=math.radians(angle);c=math.cos(a);sn=math.sin(a)
  for e in data['objects']:
   expected=[]
   for v in e['vertices_m']:
    x,y,z=v
    if e['moving']:
     dx=x-pivot.x;dy=y-pivot.y;x=pivot.x+dx*c-dy*sn;y=pivot.y+dx*sn+dy*c
    expected.append((x,y,z))
   target=[min(v[i] for v in expected) for i in range(3)]+[max(v[i] for v in expected) for i in range(3)]
   o=bpy.data.objects.get(e['id']);actual=[o.matrix_world@v.co for v in o.data.vertices];b=[min(v[i] for v in actual) for i in range(3)]+[max(v[i] for v in actual) for i in range(3)]
   assert max(abs(x-y) for x,y in zip(target,b))<1e-5,('ANIMATION_POSE',frame,e['id'],target,b)
  result.append({'frame':frame,'angle_degrees':angle,'parts':len(data['objects']),'independent_vertex_rotation':'PASS'})
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();return result
bpy.context.view_layer.update();r={'version':bpy.app.version_string,'created':audit(),'mode':'background; manual GUI NOT_TESTED'}
bpy.ops.wm.save_as_mainfile(filepath=str(out/'assembly.blend'),compress=True);bpy.ops.wm.open_mainfile(filepath=str(out/'assembly.blend'));bpy.context.scene.frame_set(1);r['blend_reopened']=audit();r['blend_animation']=motion_audit()
bpy.ops.export_scene.gltf(filepath=str(out/'assembly.glb'),export_format='GLB',export_yup=True,export_extras=True,export_animations=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out/'assembly.glb'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();r['glb_reopened']=audit();r['glb_animation']=motion_audit();(out/'blender-audit.json').write_text(json.dumps(r,indent=2))
m=json.loads((out/'manifest.json').read_text());m['collision']={'path':'collision.json','sha256':hashlib.sha256((out/'collision.json').read_bytes()).hexdigest()};m['angle_range_deg']=m['angle_bounds'];m['sampled_angles_deg']=list(range(91));m['glb']={'path':'assembly.glb','sha256':hashlib.sha256((out/'assembly.glb').read_bytes()).hexdigest()};m['native_drawings']=[x if isinstance(x,dict) else {'label':x,'path':x} for x in m['native_drawings']]
for e in m['parts']:e['bounds_m']=next(x['bounds_m'] for x in data['objects'] if x['id']==e['id'])
m['evidence_hashes']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name not in ['manifest.json'] and not f.name.endswith(('FCStd1','FCBak','blend1')) and '.FCStd.' not in f.name}
m['source_hashes']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [*Path(__file__).parent.glob('*.py'),Path(__file__).parent/'spec.json']}
(out/'manifest.json').write_text(json.dumps(m,indent=2))
