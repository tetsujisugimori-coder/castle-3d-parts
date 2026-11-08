import bpy,json
from mathutils import Vector
from pathlib import Path
root=Path('/tmp/castle-cad-independent/repo')
results=[]
for kind,path in [('blend',root/'blender/prototype-v1/palisade.blend'),('glb',root/'site/cad/palisade.glb')]:
 if kind=='blend':bpy.ops.wm.open_mainfile(filepath=str(path))
 else:
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path))
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objs)==7
 rows=[]
 for o in objs:
  v=[o.matrix_world@Vector(p) for p in o.bound_box];dims=[max(p[i]for p in v)-min(p[i]for p in v) for i in range(3)]
  expected=[.15,.15,2] if o.name.startswith('Post') else [4.95,.099,.084]
  assert max(abs(a-b)for a,b in zip(dims,expected))<1e-5
  assert len(o.data.materials)==1
  rows.append({'name':o.name,'dimensions_m':dims,'faces':len(o.data.polygons)})
 assert len([x for x in rows if x['name'].startswith('Post_')])==5
 results.append({'kind':kind,'rows':rows})
Path('/tmp/castle-cad-independent/independent-blender.json').write_text(json.dumps(results,indent=2))
