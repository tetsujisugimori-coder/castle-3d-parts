"""Native TechDraw dimensions linked to actual circular CAD edges."""
import sys,os,json,time,tempfile
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets,QtCore
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import TechDrawGui
out=Path(sys.argv[1]).resolve();d=A.openDocument(str(out/'assembly.FCStd'));d.TransientDir=tempfile.mkdtemp(prefix='gate3b-draw-')+'/'
def rec():d.recompute();q.processEvents(QtCore.QEventLoop.AllEvents,100)
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=True
for view in ['Front','Top','Side','Bearing','Trajectory']:
 text=(out/'template.svg').read_text().replace('Two unconnected prototype units.','Prototype D. Ideal joints; strength/history unverified.')
 if view=='Bearing':text=text.replace('Scale 1:16.667','Scale 2:1');d.getObject('BearingView').Scale=2
 (out/('template-'+view.lower()+'.svg')).write_text(text);d.getObject(view+'Template').Template=str(out/('template-'+view.lower()+'.svg'))
 d.getObject(view+'View').touch()
for _ in range(10):rec()
def circle(obj,r):
 for i,e in enumerate(obj.Shape.Edges):
  if hasattr(e.Curve,'Radius') and abs(e.Curve.Radius-r)<1e-6:return 'Edge'+str(i+1)
 raise AssertionError(('CIRCLE_MISSING',obj.Name,r))
rows=[]
for name,objname,r,y in [('ShaftRadius','GATE_Spindle_Lower',12,-45),('BoreRadius','GATE_Bearing_Lower',12.5,-65)]:
 obj=d.getObject(objname);edge=circle(obj,r)
 if d.getObject(name):d.removeObject(name);rec()
 n=d.addObject('TechDraw::DrawViewDimension',name);n.Type='Radius';n.MeasureType='True';n.FormatSpec='R %.2f';n.References3D=[(obj,(edge,))];n.References2D=[(d.getObject('BearingView'),('',))];d.getObject('BearingPage').addView(n);n.X=-50 if name=='ShaftRadius' else 50;n.Y=45 if name=='ShaftRadius' else -65
 G.activeDocument().getObject('BearingPage').show();deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  n.touch();rec()
  if abs(n.getRawValue()-r)<1e-6:break
 assert abs(n.getRawValue()-r)<1e-6,(name,n.getRawValue(),r)
 rows.append({'id':name,'object':objname,'edge':edge,'radius_mm':n.getRawValue(),'source':'actual CAD circular edge'})
# Range is expressed as two CAD-parameter-driven witness lines, measured as native angle.
p=d.getObject('Mechanism')
lines=[]
for name,param in [('LowerLimitRay','MinimumAngle'),('UpperLimitRay','MaximumAngle')]:
 if d.getObject(name):d.removeObject(name);rec()
 w=d.addObject('Part::Line',name);w.setExpression('X1','Mechanism.PivotX');w.setExpression('Y1','Mechanism.PivotY');w.setExpression('X2','Mechanism.PivotX + 800 mm*cos(Mechanism.'+param+')');w.setExpression('Y2','Mechanism.PivotY + 800 mm*sin(Mechanism.'+param+')');w.Z1=w.Z2=100;lines.append(w)
rec();v=d.getObject('TrajectoryView');v.Source=v.Source+lines;rec()
if d.getObject('OpeningRange'):d.removeObject('OpeningRange');rec()
n=d.addObject('TechDraw::DrawViewDimension','OpeningRange');n.Type='Angle';n.MeasureType='True';n.FormatSpec='%.1f deg';n.References3D=[(x,('Edge1',)) for x in lines];n.References2D=[(v,('',))];d.getObject('TrajectoryPage').addView(n);n.X=60;n.Y=70
G.activeDocument().getObject('TrajectoryPage').show();deadline=time.monotonic()+30
while time.monotonic()<deadline:
 n.touch();rec()
 if abs(n.getRawValue()-90)<1e-6:break
assert abs(n.getRawValue()-90)<1e-6,('ANGLE_DIMENSION',n.getRawValue())
p.MaximumAngle=60;p.MinimumAngle=10
for _ in range(10):n.touch();rec()
assert abs(n.getRawValue()-50)<1e-6,('ANGLE_DIMENSION_EDIT',n.getRawValue())
p.MinimumAngle=0;p.MaximumAngle=90;rec()
rows.append({'id':'OpeningRange','value_degrees':90,'edited_value_degrees':50,'parameters':[10,60]})
for view in ['Front','Top','Side','Bearing','Trajectory']:
 G.activeDocument().getObject(view+'Page').show();rec();TechDrawGui.exportPageAsSvg(d.getObject(view+'Page'),str(out/('native-'+view.lower()+'.svg')))
for key in ['PivotX','PivotY','PivotZ','RadialGap']:p.setEditorMode(key,1)
d.saveAs(str(out/'assembly.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'assembly.FCStd'))
for row in rows:
 name=row['id'];G.activeDocument().getObject(('Trajectory' if name=='OpeningRange' else 'Bearing')+'Page').show();n=d.getObject(name);expected=90 if name=='OpeningRange' else row['radius_mm'];deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  n.touch();rec()
  if abs(n.getRawValue()-expected)<1e-6:break
 assert abs(n.getRawValue()-expected)<1e-6,('REOPEN_DIMENSION',name,n.getRawValue())
(out/'drawing-audit.json').write_text(json.dumps({'native_dimensions':rows,'saved_reopened':True,'manual_gui':'NOT_TESTED','radial_gap_mm':rows[1]['radius_mm']-rows[0]['radius_mm']},indent=2));print('DRAWINGS PASS',flush=True);os._exit(0)
