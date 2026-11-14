"""Reopen CAD, validate persisted state/geometry and explicitly measure contact chain."""
import sys,os,json,math,tempfile
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
A.ConfigSet("AppTempPath",tempfile.gettempdir()+"/")
from state import validate_document,transition,load_document
out=Path(sys.argv[1]);d=load_document(out/'assembly.FCStd');p=d.getObject('Mechanism');l=d.getObject('LockMechanism')
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
IDS=[o.Name for o in d.Objects if 'PartID' in o.PropertiesList]
def validate():return validate_document(d)
validate();faults=[]
for a,b in [(45,140),(90,70),(0,141),(91,0)]:
 p.Angle=a;l.BoltPosition=b;d.recompute();dest=out/('counterexample-%s-%s.FCStd'%(a,b));d.saveAs(str(dest));A.closeDocument(d.Name);d=load_document(dest);p=d.getObject('Mechanism');l=d.getObject('LockMechanism')
 try:validate()
 except ValueError as e:faults.append({'angle_degrees':a,'bolt_mm':b,'saved_reloaded':True,'rejected':str(e)})
 else:raise AssertionError('PERSISTED_INVALID_ACCEPTED')
p.Angle=0;l.BoltPosition=0;d.recompute()
contacts=[]
for aid,bid in [('GATE_BoltGuide_Left','GATE_Door'),('GATE_BoltGuide_Right','GATE_Door'),('GATE_BoltReceiver','GATE_Post_Right'),('GATE_Doorstop','GATE_Post_Right'),('GATE_Doorstop','GATE_Door'),('GATE_Joint_Left','GATE_Post_Left'),('GATE_Joint_Left','GATE_Beam'),('GATE_Joint_Right','GATE_Post_Right'),('GATE_Joint_Right','GATE_Beam'),('GATE_AxialKeeper','GATE_Bearing_Upper'),('GATE_AxialKeeper','GATE_Spindle_Upper')]:
 sa=d.getObject(aid).Shape;sb=d.getObject(bid).Shape;dist=sa.distToShape(sb)[0];vol=sa.common(sb).Volume;assert dist<1e-6 and vol<=1e-4,(aid,bid,dist,vol);contacts.append({'a':aid,'b':bid,'distance_m':dist/1000,'overlap_mm3':vol,'contact':'TOUCHING','load_transfer':'NOT_TESTED'})
# Direct tuple pair check at modified dimensions; native bores follow and bolt has clearance.
variants=[]
for length,width,height,gap in [(880,18,35,.5),(900,22,45,2),(900,20,40,1)]:
 l.BoltLength=length;l.BoltWidth=width;l.BoltHeight=height;l.GuideGap=gap;l.BoltPosition=140;d.recompute();validate()
 rows=[]
 for name in ['GATE_BoltGuide_Left','GATE_BoltGuide_Right','GATE_BoltReceiver']:
  a=d.getObject('GATE_Bolt').Shape;b=d.getObject(name).Shape;dist=a.distToShape(b)[0];vol=a.common(b).Volume;assert abs(dist-gap)<1e-6 and vol<=1e-4,(name,dist,gap,vol);rows.append({'id':name,'gap_mm':dist,'overlap_mm3':vol})
 variants.append({'length_mm':length,'width_mm':width,'height_mm':height,'gap_mm':gap,'parts':rows,'receiver_engagement_mm':max(0,min(d.getObject('GATE_Bolt').Shape.BoundBox.XMax,d.getObject('GATE_BoltReceiver').Shape.BoundBox.XMax)-max(d.getObject('GATE_Bolt').Shape.BoundBox.XMin,d.getObject('GATE_BoltReceiver').Shape.BoundBox.XMin)),'engagement_basis':'BRep axial bounding interval overlap; not contact/load transfer'})
l.BoltPosition=0;l.BoltWidth=24;d.recompute()
try:transition(d,10,0)
except ValueError as e:
 assert p.Angle.Value==0 and l.BoltPosition.Value==0
 atomic={'invalid_dimension':24,'rejected':str(e),'unchanged_angle':p.Angle.Value,'unchanged_bolt_mm':l.BoltPosition.Value}
else:raise AssertionError('INVALID_DIMENSION_ACCEPTED')
l.BoltWidth=20;d.recompute()
(out/'state-audit.json').write_text(json.dumps({'atomic_rejection':atomic,'persisted_faults':faults,'contacts':contacts,'parameter_variants':variants,'manual_editor_interlock':'NOT_ENFORCED; validator rejects invalid persisted combinations','continuous_path':'UNKNOWN'},indent=2))
print('STATE CONTACT PASS',flush=True);os._exit(0)
