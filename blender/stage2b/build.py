import bpy,json,sys
from pathlib import Path
from mathutils import Vector
out=Path(sys.argv[sys.argv.index('--')+1]);data=json.loads((out/'mesh-transfer.json').read_text());expected=json.loads((out/'cad-audit.json').read_text())['created']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
m=bpy.data.materials.new('D_provisional_wood');m.diffuse_color=(.43,.255,.12,1)
for e in data['objects']:
 mesh=bpy.data.meshes.new(e['name']);mesh.from_pydata(e['vertices_m'],[],e['faces']);mesh.update();o=bpy.data.objects.new(e['name'],mesh);bpy.context.collection.objects.link(o);o.data.materials.append(m)
 for k in ['part_id','revision']:o[k]=e[k]
 o['basis']='D';o['cad_eligibility']='reference_only';o['assembly_revision']=data['revision']
def audit():
 os=sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name);pts=[o.matrix_world@Vector(p) for o in os for p in o.bound_box];dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
 assert len(os)==expected['solids'];assert all(abs(a-b)<1e-5 for a,b in zip(dims,expected['dimensions_m'])),(dims,expected)
 components=[]
 for o in os:
  p=[o.matrix_world@Vector(v) for v in o.bound_box];bounds=[min(v[i] for v in p) for i in range(3)]+[max(v[i] for v in p) for i in range(3)];e=next(e for e in expected['components'] if e['id']==o.name);assert all(abs(a-b)<1e-5 for a,b in zip(bounds,e['bounds_m']));assert o['part_id']==e['part_id'] and o['revision']==e['revision'];components.append({'id':o.name,'part_id':o['part_id'],'revision':o['revision'],'bounds_m':bounds})
 return {'dimensions_m':dims,'components':components,'objects':len(os)}
r={'software':bpy.app.version_string,'mode':'background; GUI NOT_TESTED','created':audit()};bpy.ops.wm.save_as_mainfile(filepath=str(out/'assembly.blend'),compress=True);bpy.ops.wm.open_mainfile(filepath=str(out/'assembly.blend'));r['blend_reopened']=audit();bpy.ops.export_scene.gltf(filepath=str(out/'assembly.glb'),export_format='GLB',export_yup=True,export_extras=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(out/'assembly.glb'));r['glb_reopened']=audit();(out/'blender-audit.json').write_text(json.dumps(r,indent=2))
