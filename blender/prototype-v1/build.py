import bpy, json, math, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'blender/prototype-v1';ASSET=ROOT/'site/cad/palisade.glb'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
data=json.loads((ROOT/'cad/prototype-v1/generated/mesh-transfer.json').read_text())
assert data['unit']=='m' and data['up']=='Z'
# Original generated wood grain D. No third-party texture assets.
image=bpy.data.images.new('Original_D_woodgrain',width=256,height=256)
rng=random.Random(13);pixels=[]
for y in range(256):
    for x in range(256):
        g=.92+.055*math.sin(x*.5+math.sin(y*.035))+.025*rng.random()
        pixels.extend([.43*g,.255*g,.12*g,1])
image.pixels=pixels;image.file_format='PNG';image.filepath_raw=str(OUT/'woodgrain.png');image.save();image.pack()
mat=bpy.data.materials.new('Wood_D_original_texture');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.88
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
for entry in data['objects']:
    mesh=bpy.data.meshes.new(entry['name']);mesh.from_pydata(entry['vertices_m'],[],entry['faces']);mesh.update()
    obj=bpy.data.objects.new(entry['name'],mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
    uv=mesh.uv_layers.new(name='WoodUV')
    for polygon in mesh.polygons:
        for li in polygon.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(v.x*3+v.y*3,v.z*.5) if entry['name'].startswith('Post') else (v.z*3+v.y*3,v.x*.2)
    obj['basis']='D / prototype_only';obj['cad_source']=entry['name']

def audit():
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    points=[o.matrix_world@Vector(p) for o in objs for p in o.bound_box]
    dims=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    assert len(objs)==7 and sum(o.name.startswith('Post_') for o in objs)==5 and sum(o.name.startswith('Rail_') for o in objs)==2
    assert all(abs(a-b)<1e-5 for a,b in zip(dims,[4.95,.249,2])),dims
    return {'dimensions_m_z_up':dims,'objects':len(objs),'posts':5,'rails':2,'triangles':sum(len(o.data.polygons) for o in objs),'names':[o.name for o in objs]}
r={'blender_version':bpy.app.version_string,'mode':'background','created':audit()}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'palisade.blend'),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'palisade.blend'),compress=True);r['blend_reopened']=audit()
bpy.ops.export_scene.gltf(filepath=str(ASSET),export_format='GLB',export_yup=True,export_extras=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ASSET));r['glb_reopened']=audit()
(ROOT/'evidence/cad-prototype/blender.json').write_text(json.dumps(r,indent=2)+'\n')
