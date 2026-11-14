import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
out=Path(sys.argv[sys.argv.index('--')+1]);data=json.loads((out/'mesh-transfer.json').read_text());spec=json.loads((Path(__file__).parent/'spec.json').read_text());pivot=Vector(data['pivot_m'])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parent=bpy.data.objects.new('GatePivot',None);bpy.context.collection.objects.link(parent);parent.location=pivot;parent['cad_pivot_m']=list(pivot);parent['axis']='Z'
slide=bpy.data.objects.new('BoltSlide',None);bpy.context.collection.objects.link(slide);slide.parent=parent;slide['cad_travel_m']=[0,.14];slide['cad_axis']=[1,0,0]
mat=bpy.data.materials.new('Trial_D_Timber');mat.diffuse_color=(.43,.255,.12,1)
for e in data['objects']:
 mesh=bpy.data.meshes.new(e['id']);vertices=[list(Vector(v)-pivot) if e['moving'] else v for v in e['vertices_m']];mesh.from_pydata(vertices,[],e['faces']);mesh.update();o=bpy.data.objects.new(e['id'],mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mat);o['part_id']=e['id'];o['basis']='D';o['movement']=e['movement']
 if e['moving']:o.parent=slide if e['movement']=='bolt' else parent
# Animate legal cycle: lock/unlock at closed, then swing/return. Never interpolate locked swing.
poses=[(1,0,0),(31,0,.14),(61,0,0),(106,45,0),(151,90,0),(241,0,0)]
for frame,angle,b in poses:
 parent.rotation_euler.z=math.radians(angle);slide.location.x=b;parent.keyframe_insert(data_path='rotation_euler',frame=frame);slide.keyframe_insert(data_path='location',frame=frame)
for obj in [parent,slide]:
 for fc in obj.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='LINEAR'
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=241;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def audit():
 rows=[]
 for frame,angle,b in poses:
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
  for e in data['objects']:
   o=bpy.data.objects.get(e['id']);assert o and o.get('part_id')==e['id'];expected=[]
   for raw in e['vertices_m']:
    x,y,z=raw
    if e['moving']:
     dx=x-pivot.x+(b if e['movement']=='bolt' else 0);dy=y-pivot.y;x=pivot.x+dx*c-dy*s;y=pivot.y+dx*s+dy*c
    expected.append((x,y,z))
   target=[min(v[i] for v in expected) for i in range(3)]+[max(v[i] for v in expected) for i in range(3)];vs=[o.matrix_world@v.co for v in o.data.vertices];actual=[min(v[i] for v in vs) for i in range(3)]+[max(v[i] for v in vs) for i in range(3)];assert max(abs(a-b) for a,b in zip(actual,target))<1e-5,(frame,e['id'],actual,target)
   expected_parent='BoltSlide' if e['movement']=='bolt' else 'GatePivot' if e['moving'] else None
   assert (o.parent.name if o.parent else None)==expected_parent
  rows.append({'frame':frame,'angle_degrees':angle,'bolt_m':b,'parts':len(data['objects']),'bounds_and_hierarchy':'PASS'})
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();return rows
r={'version':bpy.app.version_string,'created':audit(),'manual_gui':'NOT_TESTED'}
bpy.ops.wm.save_as_mainfile(filepath=str(out/'assembly.blend'),compress=True);bpy.ops.wm.open_mainfile(filepath=str(out/'assembly.blend'));r['blend_reopened']=audit()
bpy.ops.export_scene.gltf(filepath=str(out/'assembly.glb'),export_format='GLB',export_yup=True,export_extras=True,export_animations=True,export_animation_mode="ACTIVE_ACTIONS")
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out/'assembly.glb'));r['glb_reopened']=audit();(out/'blender-audit.json').write_text(json.dumps(r,indent=2))
print('BLENDER PASS')
