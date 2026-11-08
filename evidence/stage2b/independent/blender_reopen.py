import bpy,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]);rows=[]
for rev in ['B0','B1','B2']:
 for typ in ['blend','glb']:
  p=root/'cad/stage2b/generated'/rev/('assembly.'+typ)
  if typ=='blend':bpy.ops.wm.open_mainfile(filepath=str(p))
  else:
   bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(p))
  os=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(os)==14
  expect={'B0':(2.2,1.2),'B1':(2.4,1.2),'B2':(2.4,1.3)}[rev];points=[]
  for o in os:
   pts=[o.matrix_world@Vector(v) for v in o.bound_box];points+=pts
   assert o['basis']=='D' and o['cad_eligibility']=='reference_only'
   assert o['assembly_revision']==rev
   if '_Post_' in o.name:
    unit,index=o.name.split('_Post_');n=int(index)-1;spacing=expect[1] if unit=='U02' else 1.2;x=(6 if unit=='U02' else 0)+(n-2)*spacing
    assert abs((min(v.x for v in pts)+max(v.x for v in pts))/2-x)<1e-5
    assert abs(max(v.z for v in pts)-expect[0])<1e-5
   assert o['revision']==('B1' if rev=='B2' and o.name.startswith('U01') else rev)
  dims=[max(v[i]for v in points)-min(v[i]for v in points)for i in range(3)];rows.append({'revision':rev,'type':typ,'meshes':len(os),'dims_z_up':dims,'part_ids':sorted(o.name for o in os)})
(root/'evidence/stage2b/independent/blender-results.json').write_text(json.dumps({'software':bpy.app.version_string,'mode':'independent background actual original read; not GUI','rows':rows},indent=2))
