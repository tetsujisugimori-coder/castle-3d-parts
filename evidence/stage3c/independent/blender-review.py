import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,kdtree
root=Path.cwd();out=root/'evidence/stage3c/independent';gen=root/'cad/stage3c/generated';data=json.loads((gen/'mesh-transfer.json').read_text());pivot=data['pivot_m'];results=[]
for fmt in ['blend','glb']:
 if fmt=='blend':bpy.ops.wm.open_mainfile(filepath=str(gen/'assembly.blend'))
 else:
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(gen/'assembly.glb'))
 gate=bpy.data.objects['GatePivot'];slide=bpy.data.objects['BoltSlide'];gate.animation_data_clear();slide.animation_data_clear();gate.rotation_mode='XYZ';slide.rotation_mode='XYZ'
 origin=slide.location.copy()
 for angle,bolt in [(0,0),(0,.0375),(0,.14),(.125,0),(22.5,0),(45,0),(89.9,0),(90,0)]:
  gate.rotation_euler=(0,0,math.radians(angle));slide.location=origin+Vector((bolt,0,0));bpy.context.view_layer.update();row={'format':fmt,'angle_degrees':angle,'bolt_m':bolt,'parts':[]}
  for e in data['objects']:
   o=bpy.data.objects.get(e['id']);assert o and o.type=='MESH';actual=[o.matrix_world@v.co for v in o.data.vertices];kd=kdtree.KDTree(len(actual))
   for i,v in enumerate(actual):kd.insert(v,i)
   kd.balance();maxerr=0
   for v in e['vertices_m']:
    x,y,z=v
    if e['id']=='GATE_Bolt':x+=bolt
    if e['moving']:
     a=math.radians(angle);dx=x-pivot[0];dy=y-pivot[1];x=pivot[0]+dx*math.cos(a)-dy*math.sin(a);y=pivot[1]+dx*math.sin(a)+dy*math.cos(a)
    _,_,err=kd.find(Vector((x,y,z)));maxerr=max(maxerr,err)
   assert maxerr<1e-4,(fmt,angle,bolt,e['id'],maxerr)
   row['parts'].append({'id':e['id'],'max_vertex_distance_m':maxerr})
  results.append(row)
(out/'blender-review.json').write_text(json.dumps({'method':'Independent transformed STEP vertices vs imported blend/GLB KD nearest vertices','tolerance_m':1e-4,'samples':results,'hashes':{n:hashlib.sha256((gen/n).read_bytes()).hexdigest() for n in ['assembly.blend','assembly.glb','mesh-transfer.json']}},indent=2)+'\n');print('INDEPENDENT BLENDER PASS',len(results))
