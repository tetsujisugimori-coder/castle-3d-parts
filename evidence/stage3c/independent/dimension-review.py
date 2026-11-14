import sys,json,tempfile,time
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import TechDrawGui
root=Path.cwd();out=root/'evidence/stage3c/independent';d=A.newDocument('DimensionAudit');d.TransientDir=tempfile.mkdtemp(dir=out/'tmp')+'/';d.FileName=str(root/'cad/stage3c/generated/assembly.FCStd');d.restore();d.recompute()
rows=[]
for length,width,height,gap in [(900,20,40,1),(880,18,35,.5),(900,22,45,2)]:
 l=d.LockMechanism;l.BoltLength=length;l.BoltWidth=width;l.BoltHeight=height;l.GuideGap=gap;d.recompute()
 for page in ['LockBoltPage','LockPositionsPage']:G.activeDocument().getObject(page).show()
 for _ in range(40):
  for k in ['BoltLengthDimension','BoltWidthDimension','BoltHeightDimension']:d.getObject(k).touch()
  d.recompute();q.processEvents();time.sleep(.05)
 vals=[d.getObject(k).getRawValue() for k in ['BoltLengthDimension','BoltWidthDimension','BoltHeightDimension']]
 assert all(abs(x-y)<1e-5 for x,y in zip(vals,[length,width,height])),vals
 for k in ['GATE_BoltGuide_LeftBore','GATE_BoltGuide_RightBore','GATE_BoltReceiverBore']:
  o=d.getObject(k);assert abs(o.Width.Value-(width+2*gap))<1e-6 and abs(o.Height.Value-(height+2*gap))<1e-6
 rows.append({'length':length,'width':width,'height':height,'gap':gap,'native_measurements':vals,'bores_follow':'PASS'})
(out/'dimension-review.json').write_text(json.dumps({'cases':rows,'full_clearance_for_modified_dimensions':'NOT_TESTED'},indent=2))
