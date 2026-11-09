"""Real Qt/TechDraw 3D reference dimensions; CAD mm, exported public values m.
No projected Edge numbering is a persistent identity: semantic datum lines use
expressions bound to named CAD objects, and are checked against independent bounds.
"""
import sys,os,json,math,tempfile,hashlib
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part,TechDraw
G.showMainWindow()
import TechDrawGui
ROOT=Path(__file__).resolve().parents[2]
def recompute(d):
 d.recompute();q.processEvents();d.recompute();q.processEvents()
def specs(d):
 out=[]
 def add(id,label,view,parts,start,end,expected):out.append(dict(id=id,label=label,view=view,part_ids=parts,start=start,end=end,expected=expected))
 for u in ['U01','U02']:
  posts=[f'{u}_Post_{i:03d}' for i in range(1,6)]; rails=[f'{u}_Rail_{i:03d}' for i in range(1,3)];a,b=posts[:2];last=posts[-1]
  def o(n):return d.getObject(n)
  def bb(n):return o(n).Shape.BoundBox
  x=lambda n:f'{n}.Placement.Base.x';y=lambda n:f'{n}.Placement.Base.y';z=lambda n:f'{n}.Placement.Base.z'
  add(u+'-post-height',u+' post height','front',posts,[x(a),y(a),z(a)],[x(a),y(a),z(a)+' + '+a+'.Height'],lambda a=a:bb(a).ZLength)
  add(u+'-post-centres',u+' post centres','front',posts,[x(a)+' + '+a+'.Length / 2',y(a),z(a)],[x(b)+' + '+b+'.Length / 2',y(a),z(a)],lambda a=a,b=b:bb(b).Center.x-bb(a).Center.x)
  add(u+'-post-width',u+' post section X','top',posts,[x(a),y(a),z(a)],[x(a)+' + '+a+'.Length',y(a),z(a)],lambda a=a:bb(a).XLength)
  add(u+'-post-depth',u+' post section Y','side',posts,[x(a),y(a),z(a)],[x(a),y(a)+' + '+a+'.Width',z(a)],lambda a=a:bb(a).YLength)
  add(u+'-unit-width',u+' unit width','top',posts+rails,[x(a),y(a),z(a)],[x(last)+' + '+last+'.Length',y(a),z(a)],lambda a=a,last=last:bb(last).XMax-bb(a).XMin)
  for r in rails:
   add(r+'-length',r+' length','front',[r],[x(r),y(r),z(r)],[x(r)+' + '+r+'.Length',y(r),z(r)],lambda r=r:bb(r).XLength)
   add(r+'-elevation',r+' centre elevation','side',[r],[x(r),y(r),z(a)],[x(r),y(r),z(r)+' + '+r+'.Height / 2'],lambda r=r,a=a:bb(r).Center.z-bb(a).ZMin)
 add('assembly-width','Assembly width','top',[o.Name for o in d.Objects if 'PartID' in o.PropertiesList],['U01_Post_001.Placement.Base.x','0 mm','0 mm'],['U02_Post_005.Placement.Base.x + U02_Post_005.Length','0 mm','0 mm'],lambda:d.getObject('U02_Post_005').Shape.BoundBox.XMax-d.getObject('U01_Post_001').Shape.BoundBox.XMin)
 return out

def native_name(id):return 'Dim_'+id.replace('-','_')
def witness_name(id):return 'Witness_'+id.replace('-','_')
def validate(d):
 records=[]
 expected_parts=[f'{u}_{kind}_{i:03d}' for u in ['U01','U02'] for kind,n in [('Post',5),('Rail',2)] for i in range(1,n+1)]
 assert sorted(o.Name for o in d.Objects if 'PartID' in o.PropertiesList)==sorted(expected_parts),'PART_SET'
 for name,direction in [('front',(0,-1,0)),('top',(0,0,1)),('side',(1,0,0))]:
  view=d.getObject(name.capitalize()+'View');page=d.getObject(name.capitalize()+'Page')
  assert view is not None and page is not None,'VIEW_MISSING'
  assert sorted(o.Name for o in view.Source)==sorted(expected_parts),'VIEW_SOURCE '+name
  assert tuple(view.Direction)==direction,'VIEW_DIRECTION '+name
  assert view.ScaleType=='Custom' and abs(view.Scale-.025)<1e-10,'VIEW_SCALE '+name
  assert [o.Name for o in page.Views]==[view.Name]+[native_name(x['id']) for x in specs(d) if x['view']==name],'PAGE_LINKS '+name
 for s in specs(d):
  n=native_name(s['id']);w=d.getObject(witness_name(s['id']));dim=d.getObject(n)
  assert w is not None and dim is not None,'DIMENSION_MISSING '+s['id']
  expected_expr=dict(zip(['X1','Y1','Z1','X2','Y2','Z2'],s['start']+s['end']))
  assert dict(w.ExpressionEngine)==expected_expr,'WITNESS_EXPRESSION '+s['id']
  assert [(a.Name,list(b)) for a,b in dim.References3D]==[(w.Name,['Edge1'])],'REFERENCE_BROKEN '+s['id']
  assert [(a.Name,list(b)) for a,b in dim.References2D]==[(s['view'].capitalize()+'View',[''])],'VIEW_REFERENCE '+s['id']
  assert dim.MeasureType=='True' and dim.Type=='Distance' and not dim.Arbitrary,'MEASURE_KIND '+s['id']
  assert dim.FormatSpec=='%.1f','FORMAT_OVERRIDE '+s['id']
  assert len(w.Shape.Edges)==1,'TOPOLOGY '+s['id']
  expected=s['expected']();raw=dim.getRawValue();edge=w.Shape.Edges[0].Length
  assert expected>0 and math.isfinite(raw) and abs(raw-expected)<1e-6 and abs(edge-expected)<1e-6,('DIMENSION_VALUE',s['id'],raw,expected,edge)
  records.append({k:v for k,v in s.items() if k not in ['expected','start','end']}|{'value_mm':raw,'value_m':raw/1000,'kind':'true','native_object':n,'witness':w.Name,'expressions':expected_expr,'references3d':[[w.Name,'Edge1']],'independent_bounds_mm':expected})
 return records

def open_ready(path):
 d=A.openDocument(str(path));d.TransientDir=tempfile.mkdtemp(prefix='s2c-native-')+'/';recompute(d)
 for name in ['FrontPage','TopPage','SidePage']:
  G.activeDocument().getObject(name).show();recompute(d)
 return d

def enhance(out,revision):
 d=A.openDocument(str(out/'assembly.FCStd'));d.TransientDir=tempfile.mkdtemp(prefix='s2c-native-')+'/'
 for name in ['FrontView','TopView','SideView','Drawing','Template']:
  if d.getObject(name):d.removeObject(name)
 objs=[o for o in d.Objects if 'PartID' in o.PropertiesList]
 (out/'page-template.svg').write_text((ROOT/'cad/stage2c/template.svg').read_text().replace('Stage 2-C / D','Stage 2-C / '+revision+' / D'))
 for name,direction in [('front',(0,-1,0)),('top',(0,0,1)),('side',(1,0,0))]:
  page=d.addObject('TechDraw::DrawPage',name.capitalize()+'Page');template=d.addObject('TechDraw::DrawSVGTemplate',name.capitalize()+'Template');template.Template=str(out/'page-template.svg');page.Template=template
  v=d.addObject('TechDraw::DrawViewPart',name.capitalize()+'View');v.Source=objs;v.Direction=A.Vector(*direction);v.ScaleType='Custom';v.Scale=.025;page.addView(v);v.X=210;v.Y=200
 recompute(d)
 counts={v:0 for v in ['front','top','side']}
 for s in specs(d):
  w=d.addObject('Part::Line',witness_name(s['id']));w.Label=s['label']+' (D expression witness)'
  for prop,e in zip(['X1','Y1','Z1','X2','Y2','Z2'],s['start']+s['end']):w.setExpression(prop,e)
  recompute(d);w.Visibility=False;dim=d.addObject('TechDraw::DrawViewDimension',native_name(s['id']));dim.Label=s['label'];dim.Type='Distance';dim.MeasureType='True';dim.FormatSpec='%.1f';dim.References3D=[(w,('Edge1',))];dim.References2D=[(d.getObject(s['view'].capitalize()+'View'),('',))]
  d.getObject(s['view'].capitalize()+'Page').addView(dim);i=counts[s['view']];counts[s['view']]+=1;dim.X=-145 if s['id'].startswith('U01') else 150;dim.Y=55
  if s['view']=='front' and s['id'].endswith('length'):dim.Y=-55-(15 if '_002-' in s['id'] else 0)
  if s['view']=='front' and s['id'].endswith('height'):dim.Y=0
  if s['view']=='side':dim.X=-25-i*16;dim.Y=0
  if s['view']=='top':dim.Y=-25-i*15
 for name in ['FrontPage','TopPage','SidePage']:G.activeDocument().getObject(name).show();recompute(d)
 created=validate(d);d.saveAs(str(out/'assembly.FCStd'));A.closeDocument(d.Name);d=open_ready(out/'assembly.FCStd');reopened=validate(d);assert created==reopened
 # In-place sequential parameter changes, not rebuilding labels or witnesses.
 baseline=reopened;u=d.getObject('U01_Parameters');v=d.getObject('U02_Parameters');h=u.height.Value;sp=v.spacing.Value
 u.height=h+200;recompute(d);edited_height=validate(d);assert next(x for x in edited_height if x['id']=='U01-post-height')['value_mm']==h+200
 v.spacing=sp+100;recompute(d);edited_both=validate(d);assert next(x for x in edited_both if x['id']=='U02-post-centres')['value_mm']==sp+100
 u.height=h;v.spacing=sp;recompute(d);assert validate(d)==baseline
 controls=[]
 for id,mutate in [('missing-reference',lambda dim,w:setattr(dim,'References3D',[])),('wrong-edge',lambda dim,w:setattr(dim,'References3D',[(w,('Edge999',))])),('wrong-dimension-reference',lambda dim,w:setattr(dim,'References3D',[(d.getObject(witness_name('U01-post-width')),('Edge1',))])),('arbitrary-label',lambda dim,w:setattr(dim,'Arbitrary',True))]:
  dim=d.getObject(native_name('U01-post-height'));w=d.getObject(witness_name('U01-post-height'));old=dim.References3D;arb=dim.Arbitrary
  try:
   mutate(dim,w);recompute(d);validate(d);raise RuntimeError('CONTROL_NOT_REJECTED '+id)
  except (AssertionError,IndexError,ValueError) as e:controls.append({'case':id,'expected':'REJECT','actual':'REJECT','reason':str(e),'exit':1})
  dim.References3D=old;dim.Arbitrary=arb;recompute(d);assert validate(d)==baseline
 for name in ['front','top','side']:
  page=d.getObject(name.capitalize()+'Page');G.activeDocument().getObject(page.Name).show();recompute(d);TechDrawGui.exportPageAsSvg(page,str(out/('native-'+name+'.svg')))
  svg=(out/('native-'+name+'.svg')).read_text();assert '<svg' in svg
  for r in baseline:
   if r['view']==name:assert f'>{r["value_mm"]:.1f}<' in svg,('SVG_NATIVE_VALUE',r['id'])
 # Preserve actual references in final native file after restoration.
 d.saveAs(str(out/'assembly.FCStd'));A.closeDocument(d.Name);d=open_ready(out/'assembly.FCStd');final=validate(d);assert final==baseline
 result={'revision':revision,'software':A.Version(),'mode':'Qt offscreen with real FreeCADGui/TechDraw; no GUI hand-operation','native_linked_dimensions':'PASS','measure_type':'True 3D','created':created,'reopened':reopened,'sequential_height':edited_height,'sequential_height_spacing':edited_both,'restored':final,'fault_controls':controls,'native_svg_exports':['native-front.svg','native-top.svg','native-side.svg'],'gui_manual':'NOT_TESTED','gpu':'NOT_TESTED'}
 (out/'native-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 original=json.loads((out/'cad-audit.json').read_text());(out/'pre-enhancement-cad-audit.json').write_text(json.dumps(original,indent=2)+'\n')
 original['techdraw']={'views':['FrontView','TopView','SideView'],'pages':['FrontPage','TopPage','SidePage'],'native_scale':.025,'native_linked_dimensions':'PASS','native_dimensions':[x['native_object'] for x in final],'dimension_bounds_m':original['created']['dimensions_m'],'measure_type':'True','verification':'native-audit.json'}
 (out/'cad-audit.json').write_text(json.dumps(original,indent=2)+'\n')
 (out/'drawing-measurements.json').rename(out/'pre-enhancement-drawing-measurements.json')
 (out/'drawing-measurements.json').write_text(json.dumps({'revision':revision,'scale':.025,'unit':'mm','dimension_source':'actual reopened native TechDraw getRawValue True 3D','dimensions':final},indent=2)+'\n')
 A.closeDocument(d.Name)
 return result
if __name__=='__main__':
 try:enhance(Path(sys.argv[1]),sys.argv[2])
 except BaseException:
  import traceback;traceback.print_exc();sys.stderr.flush();os._exit(1)
