"""Prototype D mechanism. FreeCAD BRep is authoritative; no strength/history claim."""
import sys,os,json,math,tempfile,hashlib,time
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets,QtCore
q=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import TechDrawGui
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=False)
def rec(d):d.recompute();q.processEvents();d.recompute()
src=A.openDocument(str(ROOT/'cad/stage3a/generated/B0/assembly.FCStd'))
d=A.newDocument('GateMechanism');d.TransientDir=tempfile.mkdtemp(prefix='gate3b-')+'/'
base=[o for o in src.Objects if 'PartID' in o.PropertiesList];base_names=[o.Name for o in base]
for o in base:
 n=d.addObject('Part::Feature',o.Name);n.Shape=o.Shape.copy()
A.closeDocument(src.Name)
p=d.addObject('App::FeaturePython','Mechanism')
for k,v in [('PivotX',-540),('PivotY',0),('PivotZ',100),('RadialGap',.5)]:p.addProperty('App::PropertyDistance',k);setattr(p,k,v)
for k,v in [('Angle',0),('MinimumAngle',0),('MaximumAngle',90)]:p.addProperty('App::PropertyAngle',k);setattr(p,k,v)
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,A.Vector(x,y,z))
def cyl(r,z,h):return Part.makeCylinder(r,h,A.Vector(-540,0,z))
def add(n,s):o=d.addObject('Part::Feature',n);o.Shape=s;return o
for label,z in [('Lower',80),('Upper',2000)]:add('GATE_Spindle_'+label,cyl(12,z,20))
for label,z in [('Lower',80),('Upper',2005)]:
 # Ring and arm are one rigid fixed support, meeting left post face x=-600.
 s=cyl(25,z,15).fuse(box(-600,-25,z,60,50,15)).cut(cyl(12.5,z-1,17))
 if label=='Lower':s=s.fuse(cyl(25,75,5))
 add('GATE_Bearing_'+label,s)
for label,z in [('Lower',400),('Upper',1600)]:
 s=cyl(14,z,30).fuse(box(-540,-20,z,50,20,30)).cut(cyl(12,z-1,32))
 add('GATE_Coupler_'+label,s)
add('GATE_Stop_Closed',box(200,-10,0,20,10,600))
add('GATE_Stop_Open',box(-595,300,0,10,20,600))
MOVING=['GATE_Door','GATE_Axis','GATE_Spindle_Lower','GATE_Spindle_Upper','GATE_Coupler_Lower','GATE_Coupler_Upper']
objs=[o for o in d.Objects if hasattr(o,'Shape')]
for o in objs:
 o.addProperty('App::PropertyString','PartID');o.PartID=o.Name
 o.addProperty('App::PropertyString','Basis');o.Basis='D / reference_only'
 o.addProperty('App::PropertyBool','Moving');o.Moving=o.Name in MOVING
# All moving geometry stored relative to source CAD pivot, placement expressions persisted.
for o in objs:
 if o.Moving:
  s=o.Shape.copy();s.translate(A.Vector(540,0,-100));o.Shape=Part.Compound([s])
  for axis in 'XYZ':o.setExpression('Placement.Base.'+axis.lower(),'Mechanism.Pivot'+axis)
  o.Placement.Rotation=A.Rotation(A.Vector(0,0,1),0);o.setExpression('Placement.Rotation.Angle','Mechanism.Angle')
# Limit fixtures follow the CAD limit parameters around the same pivot.
for name,param,offset in [('GATE_Stop_Closed','MinimumAngle',0),('GATE_Stop_Open','MaximumAngle',90)]:
 o=d.getObject(name);s=o.Shape.copy();s.translate(A.Vector(540,0,-100));o.Shape=Part.Compound([s])
 for axis in 'XYZ':o.setExpression('Placement.Base.'+axis.lower(),'Mechanism.Pivot'+axis)
 o.Placement.Rotation=A.Rotation(A.Vector(0,0,1),0);o.setExpression('Placement.Rotation.Angle','Mechanism.'+param+' - '+str(offset)+' deg')
rec(d)
def pose(a):
 if not isinstance(a,(int,float)) or not math.isfinite(a) or not p.MinimumAngle.Value<=a<=p.MaximumAngle.Value:raise ValueError('ANGLE_RANGE')
 assert 0<=p.MinimumAngle.Value<p.MaximumAngle.Value<=90,'LIMIT_RANGE'
 p.Angle=a;rec(d)
def bounds(s):b=s.optimalBoundingBox(False,False);return [getattr(b,k)/1000 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]
# Native drawings with linked dimensional witnesses.
(OUT/'template.svg').write_text((ROOT/'cad/stage2c/template.svg').read_text().replace('PAL-ASSEMBLY / Stage 2-C / D','GATE MECHANISM / Stage 3-B / D').replace('Scale 1:40','Scale 1:16.667').replace('Two unconnected prototype units.','Prototype D. Ideal joints; strength/history unverified.'))
for name,direction in [('Front',(0,-1,0)),('Top',(0,0,1)),('Side',(1,0,0)),('Bearing',(0,0,1)),('Trajectory',(0,0,1))]:
 page=d.addObject('TechDraw::DrawPage',name+'Page');t=d.addObject('TechDraw::DrawSVGTemplate',name+'Template');t.Template=str(OUT/'template.svg');page.Template=t
 v=d.addObject('TechDraw::DrawViewPart',name+'View');v.Source=objs if name!='Bearing' else [d.getObject('GATE_Bearing_Lower'),d.getObject('GATE_Spindle_Lower')];v.Direction=A.Vector(*direction);v.ScaleType='Custom';v.Scale=.06;v.X=180;v.Y=140;page.addView(v)
 if name=='Trajectory':
  arc=d.addObject('Part::Feature','Reference_Trajectory');arc.Shape=Part.Arc(A.Vector(594,0,100),A.Vector(-540+1134/math.sqrt(2),1134/math.sqrt(2),100),A.Vector(-540,1134,100)).toShape();v.Source=objs+[arc]
rec(d)
w=d.addObject('Part::Line','PivotWitness');w.setExpression('X1','Mechanism.PivotX');w.setExpression('X2','0 mm');w.Y1=w.Y2=0;w.Z1=w.Z2=0;rec(d)
n=d.addObject('TechDraw::DrawViewDimension','PivotDimension');n.Type='Distance';n.MeasureType='True';n.FormatSpec='%.1f';n.References3D=[(w,('Edge1',))];n.References2D=[(d.getObject('FrontView'),('',))];d.getObject('FrontPage').addView(n);n.X=0;n.Y=-85
G.activeDocument().getObject('FrontPage').show()
deadline=time.monotonic()+30
while time.monotonic()<deadline:
 n.touch();rec(d);q.processEvents(QtCore.QEventLoop.AllEvents,100)
 if abs(n.getRawValue()-540)<1e-6:break
assert abs(n.getRawValue()-540)<1e-6,('NATIVE_DIMENSION',n.getRawValue())
p.PivotX=-530;rec(d);assert abs(n.getRawValue()-530)<1e-6;p.PivotX=-540;rec(d)
for name in ['Front','Top','Side','Bearing','Trajectory']:
 G.activeDocument().getObject(name+'Page').show();rec(d);TechDrawGui.exportPageAsSvg(d.getObject(name+'Page'),str(OUT/('native-'+name.lower()+'.svg')))
names=[o.Name for o in objs];pose(0);d.saveAs(str(OUT/'assembly.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(OUT/'assembly.FCStd'));p=d.getObject('Mechanism');objs=[d.getObject(name) for name in names];rec(d)
G.activeDocument().getObject('FrontPage').show()
deadline=time.monotonic()+30
while time.monotonic()<deadline:
 d.getObject('PivotDimension').touch();rec(d);q.processEvents(QtCore.QEventLoop.AllEvents,100)
 if abs(d.getObject('PivotDimension').getRawValue()-540)<1e-6:break
assert abs(d.getObject('PivotDimension').getRawValue()-540)<1e-6
# Independent legacy geometric agreement at three named poses.
legacy=[]
for label,a in [('B0',0),('B1',45),('B2',90)]:
 pose(a);s=A.openDocument(str(ROOT/('cad/stage3a/generated/'+label+'/assembly.FCStd')))
 for name in base_names:
  x=d.getObject(name).Shape;y=s.getObject(name).Shape
  assert x.cut(y).Volume+y.cut(x).Volume<1e-3,(label,name)
 legacy.append({'pose':label,'angle_degrees':a,'seven_original_members':'MATCH'});A.closeDocument(s.Name)
pose(0);Part.export(objs,str(OUT/'assembly.step'));st=A.newDocument('StepReload');Part.insert(str(OUT/'assembly.step'),st.Name);rec(st)
ss=[o for o in st.Objects if hasattr(o,'Shape') and o.Shape.Solids];assert len(ss)==len(objs)
meshes=[]
for o,s in zip(objs,ss):
 assert max(abs(a-b) for a,b in zip(bounds(o.Shape),bounds(s.Shape)))<1e-8
 assert abs(o.Shape.Volume-s.Shape.Volume)<.01
 vs,fs=s.Shape.tessellate(.05);meshes.append({'id':o.Name,'moving':o.Moving,'vertices_m':[[v.x/1000,v.y/1000,v.z/1000] for v in vs],'faces':fs,'bounds_m':bounds(o.Shape)})
(OUT/'mesh-transfer.json').write_text(json.dumps({'objects':meshes,'pivot_m':[-.54,0,.1]},indent=2))
A.closeDocument(st.Name);A.setActiveDocument(d.Name)
(OUT/'native-stage-audit.json').write_text(json.dumps({'legacy_poses':legacy,'fcstd_reloaded':True,'step_reloaded':True,'native_dimension_edit':True},indent=2))
print('NATIVE COMPLETE',flush=True)
os._exit(0)
