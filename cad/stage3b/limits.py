"""Save and reopen a reduced permitted range without replacing the canonical model."""
import sys,os,tempfile,json
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G
G.showMainWindow()
out=Path(sys.argv[1]).resolve();d=A.openDocument(str(out/'assembly.FCStd'))
for view in ['Front','Top','Side','Bearing','Trajectory']:
 t=d.getObject(view+'Template');src=out/('template-'+view.lower()+'.svg');dest=out/('limits-template-'+view.lower()+'.svg');dest.write_bytes(src.read_bytes());t.Template=str(dest)
p=d.getObject('Mechanism');p.MinimumAngle=10;p.MaximumAngle=60;p.Angle=35;d.recompute();q.processEvents();d.saveAs(str(out/'range-variation.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'range-variation.FCStd'));p=d.getObject('Mechanism');assert [p.MinimumAngle.Value,p.MaximumAngle.Value,p.Angle.Value]==[10,60,35]
rows=[]
for a,stop in [(10,'GATE_Stop_Closed'),(60,'GATE_Stop_Open')]:
 p.Angle=a;d.recompute();x=d.getObject('GATE_Door').Shape;y=d.getObject(stop).Shape;v=x.common(y).Volume;gap=x.distToShape(y)[0];assert v<1e-4 and gap<1e-6;rows.append({'angle_degrees':a,'stop':stop,'overlap_mm3':v,'gap_m':gap/1000})
(out/'limit-audit.json').write_text(json.dumps({'saved_reopened_range':[10,60],'saved_reopened_angle':35,'endpoint_contacts':rows,'other_parameter_edits':'NOT_TESTED'},indent=2));print('LIMIT RELOAD PASS',flush=True);os._exit(0)
