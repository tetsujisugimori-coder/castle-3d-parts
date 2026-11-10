"""Independent exact BRep gate/fence static-assembly interference checks."""
import sys,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
root=Path(__file__).resolve().parents[2]
def check(out):
 f=A.openDocument(str(root/'cad/stage2c/generated/B0/assembly.FCStd'));unit=[o for o in f.Objects if 'PartID' in o.PropertiesList and o.Name.startswith('U01_')];assert len(unit)==7
 results=[]
 for pose in ['B0','B1','B2']:
  d=A.openDocument(str(out/pose/'assembly.FCStd'));gate=[o for o in d.Objects if 'PartID' in o.PropertiesList];assert len(gate)==7
  rows=[]
  post_contacts=[]
  for side in ['Left','Right']:
   connector=d.getObject('GATE_Connector_'+side).Shape;post=d.getObject('GATE_Post_'+side).Shape
   area=sum(f.common(g).Area for f in connector.Faces for g in post.Faces);assert area>1e-6,('NO_POST_CONTACT_FACE',side,area)
   assert connector.common(post).Volume<1e-4
   post_contacts.append({'side':side.lower(),'contact_area_m2':area/1e6,'overlap_mm3':connector.common(post).Volume})
  for side,dx,connector in [('left',-3525,'GATE_Connector_Left'),('right',3525,'GATE_Connector_Right')]:
   shapes=[]
   for o in unit:
    shape=o.Shape.copy();shape.translate(A.Vector(dx,0,0));shapes.append((o.Name,shape))
    for g in gate:
     vol=shape.common(g.Shape).Volume;assert vol<1e-4,(pose,side,o.Name,g.Name,vol)
   rail=next(s for n,s in shapes if n=='U01_Rail_002');c=d.getObject(connector).Shape;distance=rail.distToShape(c)[0];assert distance<1e-6
   rows.append({'side':side,'translation_m':[dx/1000,0,0],'fence_unit':'U01','fence_revision':'B0','pair_tests':49,'upper_rail_connector_distance_m':distance/1000,'penetration':'NONE'})
  results.append({'pose':pose,'connections':rows,'post_contacts':post_contacts});A.closeDocument(d.Name)
 A.closeDocument(f.Name)
 (out/'connection-audit.json').write_text(json.dumps({'basis':'D','static_only':True,'rows':results,'fence_source':'cad/stage2c/generated/B0/assembly.FCStd','historical_position':'UNKNOWN'},indent=2))
if __name__=='__main__':check(Path(sys.argv[1]))
