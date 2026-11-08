import sys,json,math,tempfile
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import TechDrawGui
from pathlib import Path
root=Path(__file__).resolve().parents[3]/'cad/stage2c/generated'
result=[]
for rev,spacing,height in [('B0',1200,2200),('B1',1200,2400),('B2',1300,2400)]:
 d=A.openDocument(str(root/rev/'assembly.FCStd')); d.TransientDir=tempfile.mkdtemp(prefix='ind-s2c-')+'/';d.recompute();q.processEvents();d.recompute();q.processEvents()
 for page in ['FrontPage','TopPage','SidePage']:
  G.activeDocument().getObject(page).show();d.recompute();q.processEvents();d.recompute();q.processEvents()
 parts=[o for o in d.Objects if hasattr(o,'PartID')]
 assert len(parts)==14
 rows=[]
 for p in parts:
  b=p.Shape.BoundBox
  if '_Post_' in p.Name: assert abs(b.ZLength-height)<1e-6
  rows.append({'id':p.PartID,'bbox_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]})
 expected={'U01-post-height':height,'U02-post-height':height,'U01-post-centres':1200,'U02-post-centres':spacing}
 audit=json.loads((root/rev/'native-audit.json').read_text())
 for x in audit['restored']:
  if x['id'] in expected: print(rev,x['id'],d.getObject(x['native_object']).getRawValue(),expected[x['id']],flush=True);assert abs(d.getObject(x['native_object']).getRawValue()-expected[x['id']])<1e-6
 step=Part.Shape();step.read(str(root/rev/'assembly.step'))
 assert len(step.Solids)==14
 for ax in ['XLength','YLength','ZLength']:
  axis=ax[0];extent=max(getattr(p.Shape.BoundBox,axis+'Max') for p in parts)-min(getattr(p.Shape.BoundBox,axis+'Min') for p in parts);assert abs(extent-getattr(step.BoundBox,ax))<1e-6
 result.append({'revision':rev,'cad_parts':14,'step_solids':14,'height_mm':height,'u02_spacing_mm':spacing,'part_bounds':rows,'status':'PASS'})
 A.closeDocument(d.Name)
print('RESULT_JSON='+json.dumps(result))
