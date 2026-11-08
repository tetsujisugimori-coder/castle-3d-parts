"""Consume reopened-STEP tessellation in metres; save/reopen both deliverables."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector
out = Path(sys.argv[sys.argv.index('--')+1])
p = json.loads((out/'validated-application.json').read_text())['parameters']
data = json.loads((out/'mesh-transfer.json').read_text())
assert data['unit']=='m' and data['up']=='Z' and data['derived_from']=='reopened palisade.step'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('Stage2A_D_provisional_wood')
mat.diffuse_color=(.43,.255,.12,1)
for entry in data['objects']:
    mesh=bpy.data.meshes.new(entry['name'])
    mesh.from_pydata(entry['vertices_m'],[],entry['faces'])
    mesh.update()
    obj=bpy.data.objects.new(entry['name'],mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj['basis']='D; working_copy_only; not historical measurement'
    obj['cad_source']='reopened STEP: '+entry['name']
def audit():
    objects=sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name)
    points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    dims=[max(v[i] for v in points)-min(v[i] for v in points) for i in range(3)]
    expected=[(p['count']-1)*p['spacing']+p['width'],p['width']*(1.66 if p['rails'] else 1),p['height']]
    assert all(abs(a-b)<1e-5 for a,b in zip(dims,expected)),(dims,expected)
    assert len(objects)==p['count']+p['rails']
    assert sum(o.name.startswith('Post_') for o in objects)==p['count']
    assert sum(o.name.startswith('Rail_') for o in objects)==p['rails']
    for o in objects:o.data.calc_loop_triangles()
    return {'dimensions_m_z_up':dims,'names':[o.name for o in objects], 'objects':len(objects),'posts':p['count'],'rails':p['rails'],'triangles':sum(len(o.data.loop_triangles) for o in objects)}
r={'version':bpy.app.version_string,'mode':'background; GUI NOT_TESTED','created':audit()}
bpy.ops.wm.save_as_mainfile(filepath=str(out/'palisade.blend'),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(out/'palisade.blend'))
r['blend_reopened']=audit()
bpy.ops.export_scene.gltf(filepath=str(out/'palisade.glb'),export_format='GLB',export_yup=True,export_extras=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(out/'palisade.glb'))
r['glb_reopened']=audit()
(out/'blender-audit.json').write_text(json.dumps(r,indent=2)+'\n')
