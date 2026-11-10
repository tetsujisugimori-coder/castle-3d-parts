"""Native trial D closure mechanism; preserve Stage3B source, use live expressions."""
import sys,os,json,math,tempfile,time
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets,QtCore
import faulthandler
faulthandler.dump_traceback_later(40,repeat=True)
q=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
A.ConfigSet("AppTempPath",tempfile.gettempdir()+"/")
G.showMainWindow()
import TechDrawGui
from state import transition,load_document
ROOT=Path(__file__).resolve().parents[2];OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=False)
spec=json.loads((Path(__file__).parent/'spec.json').read_text())
print('OPEN_SOURCE',flush=True)
src=A.openDocument(str(ROOT/spec['source']),True);d=A.newDocument('GateLock');d.Label='GATE-LOCK-01 / Prototype D';d.TransientDir=tempfile.mkdtemp(prefix='gate3c-')+'/'
d.copyObject(src.getObject('Mechanism'),False)
for old in src.Objects:
 if 'PartID' in old.PropertiesList:d.copyObject(old,False)
A.closeDocument(src.Name);print('SOURCE_COPIED',flush=True)
# Inherited drawing pages stay in the copied candidate. Old files remain byte-identical.
p=d.getObject('Mechanism');p.Angle=0
l=d.addObject('App::FeaturePython','LockMechanism')
for k,v in [('BoltPosition',0),('BoltTravel',140),('BoltLength',900),('BoltWidth',20),('BoltHeight',40),('GuideGap',1)]:l.addProperty('App::PropertyLength',k);setattr(l,k,v)
l.addProperty('App::PropertyString','StateContract');l.StateContract=spec['state_contract']
def rec():d.recompute();q.processEvents(QtCore.QEventLoop.AllEvents,100)
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,A.Vector(x,y,z))
def part(name,shape,moving=False):
 o=d.addObject('Part::Feature',name);o.Shape=shape;o.addProperty('App::PropertyString','PartID');o.PartID=name;o.addProperty('App::PropertyString','Basis');o.Basis='D / reference_only';o.addProperty('App::PropertyBool','Moving');o.Moving=moving;return o
# A native parametric box provides geometry-derived dimensions, not labels.
bolt=d.addObject('Part::Box','GATE_Bolt');bolt.addProperty('App::PropertyString','PartID');bolt.PartID=bolt.Name;bolt.addProperty('App::PropertyString','Basis');bolt.Basis='D / reference_only';bolt.addProperty('App::PropertyBool','Moving');bolt.Moving=True
bolt.setExpression('Length','LockMechanism.BoltLength');bolt.setExpression('Width','LockMechanism.BoltWidth');bolt.setExpression('Height','LockMechanism.BoltHeight')
# Local offset is rotated analytically from CAD pivot; no accumulated rotation.
bolt.setExpression('Placement.Base.x','Mechanism.PivotX + (140 mm + LockMechanism.BoltPosition)*cos(Mechanism.Angle) + 115 mm*sin(Mechanism.Angle)')
bolt.setExpression('Placement.Base.y','Mechanism.PivotY + (140 mm + LockMechanism.BoltPosition)*sin(Mechanism.Angle) - 115 mm*cos(Mechanism.Angle)')
bolt.setExpression('Placement.Base.z','Mechanism.PivotZ + 900 mm');bolt.setExpression('Placement.Rotation.Angle','Mechanism.Angle')
def guide(name,x,width,depth,moving):
 # Native Boolean with parameter-driven bore. Tool objects have no PartID.
 base=part(name+'Stock',box(x+(540 if moving else 0),-130,890 if moving else 990,width,depth,60));base.PartID='';base.removeProperty('PartID')
 hole=d.addObject('Part::Box',name+'Bore');hole.Length=width+2;hole.setExpression('Width','LockMechanism.BoltWidth + 2*LockMechanism.GuideGap');hole.setExpression('Height','LockMechanism.BoltHeight + 2*LockMechanism.GuideGap');hole.Placement.Base.x=x-1+(540 if moving else 0);hole.setExpression('Placement.Base.y','-115 mm - LockMechanism.GuideGap');hole.setExpression('Placement.Base.z',('900' if moving else '1000')+' mm - LockMechanism.GuideGap')
 o=d.addObject('Part::Cut',name);o.Base=base;o.Tool=hole;o.addProperty('App::PropertyString','PartID');o.PartID=name;o.addProperty('App::PropertyString','Basis');o.Basis='D / reference_only';o.addProperty('App::PropertyBool','Moving');o.Moving=moving
 if moving:
  for axis in 'XYZ':o.setExpression('Placement.Base.'+axis.lower(),'Mechanism.Pivot'+axis)
  o.setExpression('Placement.Rotation.Angle','Mechanism.Angle')
 base.Visibility=False;hole.Visibility=False
for name,x in [('Left',-200),('Right',300)]:guide('GATE_BoltGuide_'+name,x,20,130,True)
guide('GATE_BoltReceiver',600,80,55,False)
part('GATE_Doorstop',box(574,-15,700,26,15,700))
for name,x in [('Left',-720),('Right',620)]:part('GATE_Joint_'+name,box(x,75,2100,100,20,150))
# Upper keeper is a removable trial cap over the spindle, attached only geometrically to support.
part('GATE_AxialKeeper',Part.makeCylinder(25,5,A.Vector(-540,0,2020)))
rec();objs=[o for o in d.Objects if 'PartID' in o.PropertiesList];assert len(objs)==23
for o in objs:
 if 'Movement' not in o.PropertiesList:o.addProperty('App::PropertyString','Movement')
 o.Movement='bolt' if o.Name=='GATE_Bolt' else 'door' if o.Moving else 'fixed'
def state(angle,position):transition(d,angle,position/1000);rec()
def bounds(s):b=s.optimalBoundingBox(False,False);return [getattr(b,k)/1000 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]
# Detail clipping is derived from the unchanged source solids, not independent geometry.
for oldname,newname in [('GATE_Post_Left','JointDetailPost'),('GATE_Beam','JointDetailBeam')]:
 ref=d.addObject('Part::Feature',newname);ref.Shape=d.getObject(oldname).Shape.common(box(-760,-80,2050,200,180,260));ref.addProperty('App::PropertyString','SourceID');ref.SourceID=oldname;ref.Visibility=False
# Native linked dimension on bolt X edge.
for name,ids,direction,scale in [('Assembly',[o.Name for o in objs],(0,-1,0),.065),('Bolt',['GATE_Bolt','GATE_BoltReceiver'],(0,-1,0),.18),('Positions',['GATE_Bolt','GATE_BoltReceiver','GATE_BoltGuide_Right'],(0,0,1),.18),('Doorstop',['GATE_Door','GATE_Doorstop'],(0,0,1),.18),('Support',['GATE_Spindle_Upper','GATE_Bearing_Upper','GATE_AxialKeeper'],(0,-1,0),1.5),('Joinery',['JointDetailPost','JointDetailBeam','GATE_Joint_Left'],(0,-1,0),.45)]:
 tpath=OUT/('template-'+name.lower()+'.svg');tpath.write_text((ROOT/'cad/stage2c/template.svg').read_text().replace('PAL-ASSEMBLY / Stage 2-C / D','GATE LOCK / '+name+' / D').replace('Scale 1:40', 'Scale '+str(scale)+':1').replace('Two unconnected prototype units.','Prototype D. Geometry only. Strength/history unverified.'))
 page=d.addObject('TechDraw::DrawPage','Lock'+name+'Page');t=d.addObject('TechDraw::DrawSVGTemplate','Lock'+name+'Template');t.Template=str(tpath);page.Template=t
 v=d.addObject('TechDraw::DrawViewPart','Lock'+name+'View');v.Source=[d.getObject(i) for i in ids];v.Direction=A.Vector(*direction);v.ScaleType='Custom';v.Scale=scale;v.X=180;v.Y=140;page.addView(v)
rec()
edge=next('Edge'+str(i+1) for i,e in enumerate(bolt.Shape.Edges) if abs(e.Length-900)<1e-6)
n=d.addObject('TechDraw::DrawViewDimension','BoltLengthDimension');n.Type='Distance';n.MeasureType='True';n.FormatSpec='%.1f mm';n.References3D=[(bolt,(edge,))];n.References2D=[(d.getObject('LockBoltView'),('',))];d.getObject('LockBoltPage').addView(n);n.X=0;n.Y=-50
G.activeDocument().getObject('LockBoltPage').show()
def dimwait(expected):
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  n.touch();rec()
  if abs(n.getRawValue()-expected)<1e-6:return
 raise AssertionError(('DIM',expected,n.getRawValue()))
dimwait(900);l.BoltLength=880;rec();dimwait(880);assert abs(bolt.Shape.Volume-880*20*40)<1e-5;l.BoltLength=900;rec();dimwait(900)
dimension_rows=[{'id':'BoltLengthDimension','before_mm':900,'changed_mm':880,'reloaded_mm':900}]
for dimname,objname,value,pagename,y in [('BoltWidthDimension','GATE_Bolt',20,'Positions',-45),('BoltHeightDimension','GATE_Bolt',40,'Bolt',-70),('DoorstopDepthDimension','GATE_Doorstop',15,'Doorstop',-50),('JointThicknessDimension','GATE_Joint_Left',20,'Joinery',-50)]:
 obj=d.getObject(objname);ed=next('Edge'+str(i+1) for i,e in enumerate(obj.Shape.Edges) if abs(e.Length-value)<1e-6)
 nd=d.addObject('TechDraw::DrawViewDimension',dimname);nd.Type='Distance';nd.MeasureType='True';nd.FormatSpec='%.2f mm';nd.References3D=[(obj,(ed,))];nd.References2D=[(d.getObject('Lock'+pagename+'View'),('',))];d.getObject('Lock'+pagename+'Page').addView(nd);nd.X=0;nd.Y=y
 G.activeDocument().getObject('Lock'+pagename+'Page').show();deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  nd.touch();rec()
  if abs(nd.getRawValue()-value)<1e-6:break
 assert abs(nd.getRawValue()-value)<1e-6,(dimname,nd.getRawValue())
 dimension_rows.append({'id':dimname,'value_mm':value,'source':'actual CAD edge'})
w=d.addObject('Part::Line','BoltTravelWitness');w.X1=0;w.setExpression('X2','LockMechanism.BoltTravel');w.Y1=w.Y2=-140;w.Z1=w.Z2=980;rec()
v=d.getObject('LockPositionsView');v.Source=v.Source+[w];rec()
nd=d.addObject('TechDraw::DrawViewDimension','BoltTravelDimension');nd.Type='Distance';nd.MeasureType='True';nd.FormatSpec='%.1f mm';nd.References3D=[(w,('Edge1',))];nd.References2D=[(v,('',))];d.getObject('LockPositionsPage').addView(nd);nd.X=0;nd.Y=-70
G.activeDocument().getObject('LockPositionsPage').show()
for _ in range(10):nd.touch();rec()
assert abs(nd.getRawValue()-140)<1e-6
dimension_rows.append({'id':'BoltTravelDimension','value_mm':nd.getRawValue(),'source':'CAD translation-limit witness edge'})
# Live cross-section and guide clearance change together, then restore nominal geometry.
paramrows=[]
for width,height,gap in [(18,35,.5),(22,45,2),(20,40,1)]:
 l.BoltWidth=width;l.BoltHeight=height;l.GuideGap=gap;rec()
 for guideid in ['GATE_BoltGuide_Left','GATE_BoltGuide_Right','GATE_BoltReceiver']:
  hole=d.getObject(guideid+'Bore');assert abs(hole.Width.Value-(width+2*gap))<1e-8 and abs(hole.Height.Value-(height+2*gap))<1e-8
  if guideid!='GATE_BoltReceiver':assert abs(bolt.Shape.distToShape(d.getObject(guideid).Shape)[0]-gap)<1e-6
 paramrows.append({'width_mm':width,'height_mm':height,'gap_mm':gap,'guide_follow':'PASS'})
for name in ['Assembly','Bolt','Positions','Doorstop','Support','Joinery']:
 G.activeDocument().getObject('Lock'+name+'Page').show();rec();TechDrawGui.exportPageAsSvg(d.getObject('Lock'+name+'Page'),str(OUT/('native-'+name.lower()+'.svg')))
state(0,140);G.activeDocument().getObject('LockPositionsPage').show();rec();TechDrawGui.exportPageAsSvg(d.getObject('LockPositionsPage'),str(OUT/'native-positions-locked.svg'))
state(0,0);d.saveAs(str(OUT/'assembly.FCStd'));names=[o.Name for o in objs];A.closeDocument(d.Name);d=load_document(OUT/'assembly.FCStd');p=d.getObject('Mechanism');l=d.getObject('LockMechanism');bolt=d.getObject('GATE_Bolt');n=d.getObject('BoltLengthDimension');objs=[d.getObject(i) for i in names];rec();G.activeDocument().getObject('LockBoltPage').show();dimwait(900)
rows=[]
for angle,position in [(0,0),(0,70),(0,140),(45,0),(90,0),(0,0)]:
 state(angle,position);rows.append({'angle_degrees':angle,'bolt_m':position/1000,'parts':[{'id':o.Name,'bounds_m':bounds(o.Shape)} for o in objs]})
state(0,0);Part.export(objs,str(OUT/'assembly.step'));st=A.newDocument('ReloadStep');Part.insert(str(OUT/'assembly.step'),st.Name);st.recompute();ss=[o for o in st.Objects if hasattr(o,'Shape') and o.Shape.Solids];assert len(ss)==23
meshes=[]
for o,s in zip(objs,ss):
 assert max(abs(a-b) for a,b in zip(bounds(o.Shape),bounds(s.Shape)))<1e-7,(o.Name,'BOUNDS')
 assert abs(o.Shape.Volume-s.Shape.Volume)<.01
 vs,fs=s.Shape.tessellate(.1);meshes.append({'id':o.Name,'moving':o.Moving,'movement':o.Movement,'motion':o.Movement,'vertices_m':[[v.x/1000,v.y/1000,v.z/1000] for v in vs],'faces':fs,'bounds_m':bounds(o.Shape)})
(OUT/'mesh-transfer.json').write_text(json.dumps({'objects':meshes,'pivot_m':spec['pivot_m'],'bolt':spec['bolt']},separators=(',',':')))
(OUT/'cad-audit.json').write_text(json.dumps({'FreeCAD':A.Version(),'parts':23,'fcstd_reloaded':True,'step_reloaded':True,'native_dimension_edit':True,'dimension_before_mm':900,'dimension_changed_mm':880,'dimension_reloaded_mm':n.getRawValue(),'native_dimensions':dimension_rows,'parameter_variations':paramrows,'pose_bounds':rows,'manual_gui':'NOT_TESTED'},indent=2))
print('NATIVE PASS',flush=True);os._exit(0)
