"""Fresh headless reload, independent rigid transform oracle, deliberate geometry faults."""
import sys,os,json,math
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]).resolve();d=A.openDocument(str(out/'assembly.FCStd'));p=d.getObject('Mechanism')
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
old=A.openDocument(str(root/'cad/stage3a/generated/B0/assembly.FCStd'));base=old.getObject('GATE_Door').Shape.copy();A.closeDocument(old.Name)
def rec():d.recompute()
def check(a):
 assert 0<=p.MinimumAngle.Value<=a<=p.MaximumAngle.Value<=90
 assert sorted(o.Name for o in d.Objects if 'PartID' in o.PropertiesList)==sorted(ids)
 assert abs(p.PivotX.Value+540)<1e-9 and abs(p.PivotY.Value)<1e-9 and abs(p.PivotZ.Value-100)<1e-9
 assert p.RadialGap.Value==.5
 assert all(d.getObject(n).PartID==n for n in ids)
 p.Angle=a;rec();expected=base.copy();expected.rotate(A.Vector(-540,0,100),A.Vector(0,0,1),a);actual=d.getObject('GATE_Door').Shape
 assert actual.cut(expected).Volume+expected.cut(actual).Volume<1e-3,'POSE_MISMATCH'
 assert all(o.Shape.isValid() for o in d.Objects if 'PartID' in o.PropertiesList)
 for a,b in [('GATE_Axis','GATE_Coupler_Lower'),('GATE_Axis','GATE_Coupler_Upper'),('GATE_Door','GATE_Coupler_Lower'),('GATE_Door','GATE_Coupler_Upper'),('GATE_Spindle_Lower','GATE_Bearing_Lower'),('GATE_Post_Left','GATE_Bearing_Lower'),('GATE_Post_Left','GATE_Bearing_Upper')]:
  x=d.getObject(a).Shape;y=d.getObject(b).Shape;assert x.common(y).Volume<1e-4,(a,b,'penetration');assert x.distToShape(y)[0]<1e-6,(a,b,'missing contact')
 return True
ids=['GATE_Post_Left','GATE_Post_Right','GATE_Beam','GATE_Door','GATE_Axis','GATE_Connector_Left','GATE_Connector_Right','GATE_Spindle_Lower','GATE_Spindle_Upper','GATE_Bearing_Lower','GATE_Bearing_Upper','GATE_Coupler_Lower','GATE_Coupler_Upper','GATE_Stop_Closed','GATE_Stop_Open']
angles=[0,45,90,45,0,37,89,12,0]*3
for a in angles:check(a)
contacts=[]
for a,b in [('GATE_Spindle_Lower','GATE_Bearing_Lower'),('GATE_Axis','GATE_Coupler_Lower'),('GATE_Door','GATE_Coupler_Lower'),('GATE_Post_Left','GATE_Bearing_Lower')]:
 x=d.getObject(a).Shape;y=d.getObject(b).Shape;area=sum(f.common(g).Area for f in x.Faces for g in y.Faces);assert area>1e-6;contacts.append({'a':a,'b':b,'contact_area_m2':area/1e6,'overlap_mm3':x.common(y).Volume})
faults=[]
def rejects(name,fn):
 try:fn()
 except (AssertionError,ValueError):faults.append({'id':name,'result':'REJECT'})
 else:raise AssertionError(('FAULT_ACCEPTED',name))
rejects('angle-overrun',lambda:check(91));rejects('negative-angle',lambda:check(-1))
p.PivotX=-530;rejects('axis-shift',lambda:check(0));p.PivotX=-540
p.RadialGap=0;rejects('gap-metadata-mismatch',lambda:check(0));p.RadialGap=.5
support=d.getObject('GATE_Bearing_Lower');original=support.Shape.copy();support.Shape=Part.makeBox(100,100,100,A.Vector(-560,-20,80));rejects('support-penetration',lambda:check(0));support.Shape=original
# Frozen old failing artifact is independently rejected against same transform oracle.
failed=A.openDocument(str(root/'cad/stage3b/evidence/before-pivot-fix.FCStd'));bad=failed.getObject('GATE_Door').Shape;assert bad.cut(base).Volume+base.cut(bad).Volume>1e-3;A.closeDocument(failed.Name);faults.append({'id':'before-pivot-fix','result':'REJECT'})
check(0)
(out/'native-tests.json').write_text(json.dumps({'fresh_reload':True,'oracle':'independent rotation of preserved Stage3A B0 solid','poses_tested':angles,'faults':faults,'contacts':contacts,'strength':'NOT_TESTED','physical_joint_function':'NOT_TESTED'},indent=2));print('NATIVE TESTS PASS',flush=True);os._exit(0)
