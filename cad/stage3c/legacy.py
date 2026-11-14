import sys,os,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
out=Path(sys.argv[1]);root=Path(__file__).resolve().parents[2];old=A.openDocument(str(root/'cad/stage3b/generated/assembly.FCStd'));new=A.openDocument(str(out/'assembly.FCStd'))
for d in [old,new]:
 for o in d.Objects:
  if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
ids=[o.Name for o in old.Objects if 'PartID' in o.PropertiesList];rows=[]
for angle in [0,45,90]:
 for d in [old,new]:d.getObject('Mechanism').Angle=angle;d.recompute()
 for id in ids:
  a=old.getObject(id).Shape;b=new.getObject(id).Shape;difference=a.cut(b).Volume+b.cut(a).Volume;assert difference<1e-4,(angle,id,difference);rows.append({'id':id,'angle_degrees':angle,'symmetric_difference_mm3':difference})
(out/'legacy-audit.json').write_text(json.dumps({'part_count':len(ids),'rows':rows,'result':'PASS'},indent=2));print('LEGACY PASS',flush=True);os._exit(0)
