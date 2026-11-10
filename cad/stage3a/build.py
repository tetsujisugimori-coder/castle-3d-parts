"""Real FreeCAD + Qt TechDraw. Prototype D; mm native, m interchange."""
import sys,os,json,math,tempfile,hashlib
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part,TechDraw
G.showMainWindow()
import TechDrawGui
ROOT=Path(__file__).resolve().parents[2]
SPEC=json.loads((ROOT/'cad/stage3a/spec.json').read_text())
NAMES=['GATE_Post_Left','GATE_Post_Right','GATE_Beam','GATE_Door','GATE_Axis','GATE_Connector_Left','GATE_Connector_Right']
def rec(d):d.recompute();q.processEvents();d.recompute();q.processEvents()
def check_spec(s):
 p=s['parameters'];assert set(p)==set(SPEC['parameters'])
 assert all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>0 for v in p.values()),'INVALID_DIMENSION'
 assert p['door_width']+p['axis_inset']<p['opening'] and p['door_height']+p['ground_clearance']<p['post_height'],'CLEARANCE'
 assert p['axis_radius']<p['axis_inset']/2,'AXIS_CLEARANCE'
 assert s['basis']=='D' and s['cad_eligibility']=='reference_only'
def audit(d):
 os=[d.getObject(n) for n in NAMES];assert all(os),'PART_MISSING'
 assert sorted(o.Name for o in d.Objects if 'PartID' in o.PropertiesList)==sorted(NAMES),'PART_SET'
 shapes=[o.Shape for o in os];assert all(s.isValid() and len(s.Solids)==1 for s in shapes)
 overlap=[];clear=[]
 for i in range(len(os)):
  for j in range(i):
   volume=shapes[i].common(shapes[j]).Volume;assert volume<1e-4,('INTERFERENCE',os[i].Name,os[j].Name,volume)
   clear.append({'a':os[i].Name,'b':os[j].Name,'distance_m':shapes[i].distToShape(shapes[j])[0]/1000,'overlap_mm3':volume})
 b=Part.Compound(shapes).optimalBoundingBox(False,False)
 return {'solids':7,'dimensions_m':[b.XLength/1000,b.YLength/1000,b.ZLength/1000],'components':[{'id':o.Name,'part_id':o.PartID,'revision':o.Revision,'bounds_m':[getattr(o.Shape.optimalBoundingBox(False,False),k)/1000 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]} for o in os],'pairwise_clearances':clear}
def equivalent(a,b):
 assert a['solids']==b['solids']
 for x,y in zip(a['components'],b['components']):
  assert x['id']==y['id'] and x['part_id']==y['part_id'] and x['revision']==y['revision']
  assert all(abs(v-w)<1e-8 for v,w in zip(x['bounds_m'],y['bounds_m']))
 assert all(abs(v-w)<1e-8 for v,w in zip(a['dimensions_m'],b['dimensions_m']))
def ready(d):
 for v in ['front','top','side','pivot','connection']:G.activeDocument().getObject(v.capitalize()+'Page').show();rec(d)
def dimensions(d):
 return [('beam-length','front','GATE_Beam','Length'),('post-height','front','GATE_Post_Left','Height'),('opening','front','Parameters','opening'),('door-width','front','GATE_Door','Length'),('door-height','side','GATE_Door','Height'),('door-thickness','top','GATE_Door','Width'),('axis-radius','pivot','GATE_Axis','Radius'),('connector-length','connection','GATE_Connector_Left','Length')]
def witness_expressions(id):
 def pos(n,k):return n+'.Placement.Base.'+k
 def point(n):return [pos(n,k) for k in 'xyz']
 def span(n,axis,length):
  a=point(n);b=a.copy();b[axis]+=' + '+length;return a+b
 if id=='beam-length':return span('GATE_Beam',0,'GATE_Beam.Length')
 if id=='post-height':return span('GATE_Post_Left',2,'GATE_Post_Left.Height')
 if id=='opening':return [pos('GATE_Post_Left','x')+' + GATE_Post_Left.Length','0 mm','0 mm',pos('GATE_Post_Right','x'),'0 mm','0 mm']
 if id=='door-height':return span('GATE_Door',2,'GATE_Door.Height')
 if id in ['door-width','door-thickness']:
  a=point('GATE_Door');b=a.copy();ang='Parameters.pose_angle'
  if id=='door-width':b[0]+=' + GATE_Door.Length*cos('+ang+')';b[1]+=' + GATE_Door.Length*sin('+ang+')'
  else:b[0]+=' - GATE_Door.Width*sin('+ang+')';b[1]+=' + GATE_Door.Width*cos('+ang+')'
  return a+b
 if id=='axis-radius':return span('GATE_Axis',0,'GATE_Axis.Radius')
 if id=='connector-length':return span('GATE_Connector_Left',0,'GATE_Connector_Left.Length')
 raise AssertionError(id)
def dimcheck(d):
 out=[]
 for id,view,obj,prop in dimensions(d):
  w=d.getObject('Witness_'+id.replace('-','_'));n=d.getObject('Dim_'+id.replace('-','_'));expected=getattr(d.getObject(obj),prop).Value
  assert n and w and n.MeasureType=='True' and not n.Arbitrary and n.FormatSpec=='%.1f','DIMENSION_CONTRACT'
  assert [(a.Name,list(b)) for a,b in n.References3D]==[(w.Name,['Edge1'])],'REFERENCE'
  assert {k:''.join(v.split()) for k,v in w.ExpressionEngine}=={k:''.join(v.split()) for k,v in zip(['X1','Y1','Z1','X2','Y2','Z2'],witness_expressions(id))},('EXPRESSION',id,dict(w.ExpressionEngine),witness_expressions(id))
  assert abs(n.getRawValue()-expected)<1e-6 and abs(w.Shape.Length-expected)<1e-6,('DIMENSION_VALUE',id,n.getRawValue(),w.Shape.Length,expected)
  out.append({'id':id,'view':view,'part_ids':(NAMES[:2] if obj in ['Parameters','GATE_Post_Left'] else NAMES[5:] if obj=='GATE_Connector_Left' else [obj]),'value_m':expected/1000,'native_object':n.Name,'witness':w.Name,'expression':obj+'.'+prop,'witness_expressions':dict(w.ExpressionEngine)})
 return out
def build(pose,out):
 check_spec(SPEC);out.mkdir(parents=True,exist_ok=False);d=A.newDocument('Gate'+pose['id']);d.TransientDir=tempfile.mkdtemp(prefix='gate-native-')+'/'
 par=d.addObject('App::FeaturePython','Parameters')
 for k,v in SPEC['parameters'].items():par.addProperty('App::PropertyLength',k,'Prototype D');setattr(par,k,v*1000)
 par.addProperty('App::PropertyAngle','pose_angle','Prototype D');par.pose_angle=pose['angle_degrees']
 def box(n,ex):
  o=d.addObject('Part::Box',n)
  for k,v in ex.items():o.setExpression(k,v)
  return o
 P=lambda s:'Parameters.'+s
 w=P('post_width');h=P('post_height');op=P('opening');cl=P('connector_length');ch=P('connector_height');cd=P('connector_depth')
 box(NAMES[0],{'Length':w,'Width':w,'Height':h,'Placement.Base.x':'-'+op+'/2 - '+w,'Placement.Base.y':'-'+w+'/2'})
 box(NAMES[1],{'Length':w,'Width':w,'Height':h,'Placement.Base.x':op+'/2','Placement.Base.y':'-'+w+'/2'})
 box(NAMES[2],{'Length':op+' + 2*'+w,'Width':w,'Height':w,'Placement.Base.x':'-'+op+'/2 - '+w,'Placement.Base.y':'-'+w+'/2','Placement.Base.z':h})
 # Door origin is pivot + a radial clearance; rotate rigidly about fixed pivot.
 ax='-'+op+'/2 + '+P('axis_inset');rad=P('axis_radius')+' + 2 mm';ang=P('pose_angle')
 door=box(NAMES[3],{'Length':P('door_width'),'Width':P('door_thickness'),'Height':P('door_height'),'Placement.Base.x':ax+' + ('+rad+')*cos('+ang+')','Placement.Base.y':'('+rad+')*sin('+ang+')','Placement.Base.z':P('ground_clearance')})
 door.Placement.Rotation=A.Rotation(A.Vector(0,0,1),pose['angle_degrees'])
 door.setExpression('Placement.Rotation.Angle',ang)
 axis=d.addObject('Part::Cylinder',NAMES[4]);axis.setExpression('Radius',P('axis_radius'));axis.setExpression('Height',P('door_height'));axis.setExpression('Placement.Base.x',ax);axis.setExpression('Placement.Base.z',P('ground_clearance'))
 for n,x in [(NAMES[5],'-'+op+'/2 - '+cl),(NAMES[6],op+'/2')]:box(n,{'Length':cl,'Width':cd,'Height':ch,'Placement.Base.x':x,'Placement.Base.y':'-'+w+'/2 - '+cd,'Placement.Base.z':h+'*2/3 - '+ch+'/2'})
 for n in NAMES:
  o=d.getObject(n);o.addProperty('App::PropertyString','PartID');o.PartID=n;o.addProperty('App::PropertyString','Revision');o.Revision='GATE-SIMPLE-01/'+pose['id'];o.addProperty('App::PropertyString','Basis');o.Basis='D / reference_only'
 rec(d);before=audit(d)
 # Reference-only fence solids appear in the connection drawing, not the gate assembly/export.
 fence=A.openDocument(str(ROOT/'cad/stage2c/generated/B0/assembly.FCStd'))
 refs=[]
 for fname in ['U01_Post_005','U01_Rail_002']:
  shape=fence.getObject(fname).Shape.copy();shape.translate(A.Vector(-3525,0,0));refs.append((fname,shape))
 A.closeDocument(fence.Name);A.setActiveDocument(d.Name)
 for fname,shape in refs:
  ref=d.addObject('Part::Feature','Reference_'+fname);ref.Shape=shape;ref.Label='Fence B0 reference '+fname;ref.Visibility=False
 (out/'page-template.svg').write_text((ROOT/'cad/stage2c/template.svg').read_text().replace('PAL-ASSEMBLY / Stage 2-C / D','GATE-SIMPLE-01 / '+pose['id']+' / D').replace('Scale 1:40','Scale 1:16.667').replace('Two unconnected prototype units.','Gate with schematic pivot. Connection view includes reference fence B0.'))
 for view,direction in [('front',(0,-1,0)),('top',(0,0,1)),('side',(1,0,0)),('pivot',(0,0,1)),('connection',(0,-1,0))]:
  page=d.addObject('TechDraw::DrawPage',view.capitalize()+'Page');t=d.addObject('TechDraw::DrawSVGTemplate',view.capitalize()+'Template');t.Template=str(out/'page-template.svg');page.Template=t
  v=d.addObject('TechDraw::DrawViewPart',view.capitalize()+'View');v.Source=[d.getObject(n) for n in (NAMES if view in ['front','top','side'] else [NAMES[3],NAMES[4]] if view=='pivot' else [NAMES[0],NAMES[5],'Reference_U01_Post_005','Reference_U01_Rail_002'])];v.Direction=A.Vector(*direction);v.ScaleType='Custom';v.Scale=.06;v.X=180;v.Y=140;page.addView(v)
 rec(d)
 for i,(id,view,obj,prop) in enumerate(dimensions(d)):
  wtn=d.addObject('Part::Line','Witness_'+id.replace('-','_'));
  for key,expr in zip(['X1','Y1','Z1','X2','Y2','Z2'],witness_expressions(id)):wtn.setExpression(key,expr)
  rec(d);wtn.Visibility=False
  n=d.addObject('TechDraw::DrawViewDimension','Dim_'+id.replace('-','_'));n.Type='Distance';n.MeasureType='True';n.FormatSpec='%.1f';n.References3D=[(wtn,('Edge1',))];n.References2D=[(d.getObject(view.capitalize()+'View'),('',))];d.getObject(view.capitalize()+'Page').addView(n);n.X,n.Y={'beam-length':(0,90),'post-height':(-70,0),'opening':(0,-85),'door-width':(0,-65),'door-height':(-40,0),'door-thickness':(0,-40),'axis-radius':(0,-65),'connector-length':(0,-85)}[id]
 rec(d);created=dimcheck(d);d.saveAs(str(out/'assembly.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'assembly.FCStd'));ready(d);after=audit(d);equivalent(after,before);reopened=dimcheck(d);assert created==reopened
 par=d.getObject('Parameters');original_angle=par.pose_angle.Value;par.pose_angle=30;rec(d)
 assert abs(d.getObject('GATE_Door').Placement.Rotation.Angle*180/math.pi-30)<1e-8,'POSE_ROTATION'
 d.saveAs(str(out/'pose-variation.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'pose-variation.FCStd'));ready(d)
 assert abs(d.getObject('GATE_Door').Placement.Rotation.Angle*180/math.pi-30)<1e-8,'POSE_REOPEN'
 d.getObject('Parameters').pose_angle=original_angle;rec(d);equivalent(audit(d),before)
 par=d.getObject('Parameters');old=par.post_height.Value;par.post_height=old+100;rec(d);changed=dimcheck(d);assert next(x for x in changed if x['id']=='post-height')['value_m']==(old+100)/1000
 d.saveAs(str(out/'parameter-variation.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'parameter-variation.FCStd'));ready(d);assert dimcheck(d)==changed;d.getObject('Parameters').post_height=old;rec(d);assert dimcheck(d)==created
 controls=[]
 for name,mut in [('arbitrary',lambda n:setattr(n,'Arbitrary',True)),('missing-reference',lambda n:setattr(n,'References3D',[]))]:
  n=d.getObject('Dim_post_height');ref=n.References3D;mut(n);rec(d)
  try:dimcheck(d)
  except (AssertionError,ValueError):controls.append({'id':name,'result':'REJECT'})
  else:raise AssertionError('FAULT_ACCEPTED')
  n.Arbitrary=False;n.References3D=ref;rec(d)
 for view in ['front','top','side','pivot','connection']:
  page=d.getObject(view.capitalize()+'Page');G.activeDocument().getObject(page.Name).show();rec(d);TechDrawGui.exportPageAsSvg(page,str(out/('native-'+view+'.svg')))
 d.saveAs(str(out/'assembly.FCStd'));objs=[d.getObject(n) for n in NAMES];Part.export(objs,str(out/'assembly.step'));st=A.newDocument('Step'+pose['id']);Part.insert(str(out/'assembly.step'),st.Name);rec(st);ss=[o for o in st.Objects if hasattr(o,'Shape') and len(o.Shape.Solids)>0];assert len(ss)==7
 meshes=[]
 for o,s in zip(objs,ss):
  assert abs(o.Shape.Volume-s.Shape.Volume)<.01
  assert all(abs(getattr(o.Shape.optimalBoundingBox(False,False),k)-getattr(s.Shape.optimalBoundingBox(False,False),k))<1e-5 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
  vs,fs=s.Shape.tessellate(.001);meshes.append({'name':o.Name,'part_id':o.PartID,'revision':o.Revision,'vertices_m':[[v.x/1000,v.y/1000,v.z/1000] for v in vs],'faces':list(fs)})
 (out/'mesh-transfer.json').write_text(json.dumps({'unit':'m','up':'Z','derived_from':'reopened assembly.step','revision':'GATE-SIMPLE-01/'+pose['id'],'objects':meshes},indent=2))
 (out/'cad-audit.json').write_text(json.dumps({'software':A.Version(),'mode':'real FreeCAD with Qt offscreen; manual GUI NOT_TESTED','pose':pose,'created':before,'fcstd_reopened':after,'step_reopened':True,'parameter_edit_save_reopen':True,'pose_parameter_edit_save_reopen':{'angle_degrees':30,'reopened_angle_degrees':30,'restored_degrees':original_angle},'axis_m':[-SPEC['parameters']['opening']/2+SPEC['parameters']['axis_inset'],0,SPEC['parameters']['ground_clearance']]},indent=2))
 (out/'native-audit.json').write_text(json.dumps({'native_linked_dimensions':'PASS','created':created,'reopened':reopened,'parameter_variation_reopened':changed,'restored':dimcheck(d),'fault_controls':controls,'manual_gui':'NOT_TESTED'},indent=2))
 A.closeDocument(st.Name);A.closeDocument(d.Name)
if __name__=='__main__':
 try:
  for pose in SPEC['poses']:build(pose,Path(sys.argv[1])/pose['id'])
 except BaseException:
  import traceback;traceback.print_exc();sys.stderr.flush();os._exit(1)
