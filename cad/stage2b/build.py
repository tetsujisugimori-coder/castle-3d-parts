"""Actual FreeCAD headless generation. Geometry in mm, public contract metres."""
import sys,json,hashlib,tempfile,math
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A, Part, TechDraw
ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'cad/stage2b/spec.json'
def audit(objects):
 s=[o.Shape for o in objects]; c=Part.Compound(s); b=c.BoundBox
 assert all(x.isValid() and len(x.Solids)==1 for x in s)
 overlaps=[{'a':objects[i].Name,'b':objects[j].Name,'volume_mm3':s[i].common(s[j]).Volume} for i in range(len(s)) for j in range(i) if s[i].BoundBox.intersect(s[j].BoundBox)]
 assert all(x['volume_mm3']<1e-4 for x in overlaps),overlaps
 return {'dimensions_m':[b.XLength/1000,b.YLength/1000,b.ZLength/1000], 'bounds_m':[b.XMin/1000,b.YMin/1000,b.ZMin/1000,b.XMax/1000,b.YMax/1000,b.ZMax/1000], 'solids':len(c.Solids),'volume_mm3':c.Volume,'components':[{'id':o.Name,'part_id':o.PartID,'revision':o.Revision,'bounds_m':[getattr(o.Shape.BoundBox,k)/1000 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]} for o in objects], 'intersection_checks':len(s)*(len(s)-1)//2,'max_overlap_mm3':max([x['volume_mm3'] for x in overlaps]+[0])}
def run(rev,out):
 out.mkdir(parents=True,exist_ok=False); d=A.newDocument('Assembly'+rev['id']); objs=[]
 for u in rev['units']:
  p=u['parameters']; uid=u['instance_id']; c=d.addObject('App::FeaturePython',uid+'_Parameters')
  for key,val in p.items(): c.addProperty('App::PropertyFloat' if key in ['count','rails'] else 'App::PropertyLength',key,'Prototype D');setattr(c,key,val*1000 if key not in ['count','rails'] else val)
  for ax,val in zip('XYZ',u['position_m']):c.addProperty('App::PropertyLength','Offset'+ax,'Placement');setattr(c,'Offset'+ax,val*1000)
  for kind,n in [('Post',int(p['count'])),('Rail',int(p['rails']))]:
   for i in range(n):
    o=d.addObject('Part::Box',f'{uid}_{kind}_{i+1:03d}');o.addProperty('App::PropertyString','PartID');o.PartID=f'PAL-{kind.upper()}';o.addProperty('App::PropertyString','Revision');o.Revision=u['unit_revision'];o.addProperty('App::PropertyString','Basis');o.Basis='D / reference_only / prototype'
    pre=c.Name+'.'
    expr={'Length':'width','Width':'width','Height':'height','Placement.Base.x':f'OffsetX + ({i} - (count - 1) / 2) * spacing - width / 2','Placement.Base.y':'OffsetY - width / 2','Placement.Base.z':'OffsetZ'} if kind=='Post' else {'Length':'(count - 1) * spacing + width','Width':'width * .66','Height':'width * .56','Placement.Base.x':'OffsetX - ((count - 1) * spacing + width) / 2','Placement.Base.y':'OffsetY - width / 2 - width * .66','Placement.Base.z':f'OffsetZ + height * {i+1} / (rails + 1) - width * .28'}
    import re
    for prop,e in expr.items():o.setExpression(prop,re.sub(r'\b(height|width|count|spacing|rails|OffsetX|OffsetY|OffsetZ)\b',lambda m:pre+m[0],e))
    objs.append(o)
 d.recompute(); before=audit(objs);d.TransientDir=tempfile.mkdtemp(prefix='s2b-drawing-')+'/'
 page=d.addObject('TechDraw::DrawPage','Drawing');t=d.addObject('TechDraw::DrawSVGTemplate','Template');t.Template=str(ROOT/'cad/prototype-v1/template.svg');page.Template=t
 views=[]
 for name,direction,pos in [('Front',(0,-1,0),(130,145)),('Top',(0,0,1),(130,65)),('Side',(1,0,0),(265,145))]:
  v=d.addObject('TechDraw::DrawViewPart',name+'View');v.Source=objs;v.Direction=A.Vector(*direction);v.ScaleType='Custom';v.Scale=.02;page.addView(v);v.X,v.Y=pos;views.append(v)
 d.recompute();dims=[]
 # Native dimension extraction is unavailable in this headless build (zero projected vertices).
 # Do not retain invalid zero dimensions; standalone SVG uses actual CAD bounds.
 from drawing import render
 dimensions=render(rev,objs,out)
 view_names=[v.Name for v in views];dim_names=[x.Name for x in dims];d.saveAs(str(out/'assembly.FCStd'));A.closeDocument(d.Name);d=A.openDocument(str(out/'assembly.FCStd'));objs=[o for o in d.Objects if 'PartID' in o.PropertiesList];reopened=audit(objs);assert reopened==before
 # Independent editable unit and reusable part originals, copied without changing assembly.
 unit=A.newDocument('Unit'+rev['id'])
 for o in objs[:7]:unit.copyObject(o,True)
 unit.recompute();unit.saveAs(str(out/'unit.FCStd'));Part.export([o for o in unit.Objects if 'PartID' in o.PropertiesList],str(out/'unit.step'));A.closeDocument(unit.Name)
 # Actual edit/recompute/revert proving expressions survive native reload.
 par=d.getObject(rev['units'][0]['instance_id']+'_Parameters');old=par.height.Value;par.height=old+100;d.recompute();edited=audit(objs);assert edited!=before;par.height=old;d.recompute();assert audit(objs)==before
 Part.export(objs,str(out/'assembly.step'));st=A.newDocument('STEP'+rev['id']);Part.insert(str(out/'assembly.step'),st.Name);st.recompute();ss=[o for o in st.Objects if hasattr(o,'Shape') and len(o.Shape.Solids)>0];assert len(ss)==len(objs),(len(ss),len(objs))
 meshes=[]
 for original, imported in zip(objs,ss):
  assert abs(original.Shape.Volume-imported.Shape.Volume)<.01
  assert all(abs(getattr(original.Shape.BoundBox,k)-getattr(imported.Shape.BoundBox,k))<1e-5 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
  vs,fs=imported.Shape.tessellate(.1);meshes.append({'name':original.Name,'part_id':original.PartID,'revision':original.Revision,'vertices_m':[[v.x/1000,v.y/1000,v.z/1000] for v in vs],'faces':list(fs)})
 (out/'mesh-transfer.json').write_text(json.dumps({'unit':'m','up':'Z','derived_from':'reopened assembly.step','revision':rev['id'],'objects':meshes},indent=2))
 result={'software':A.Version(),'mode':'headless real FreeCAD; GUI NOT_TESTED','created':before,'fcstd_reopened':reopened,'edit_recompute_revert':True,'step_reopened':True,'step_components':len(ss),'techdraw':{'views':view_names,'native_dimensions':dim_names,'svg':'TechDraw.projectToSVG from actual geometry','dimension_bounds_m':before['dimensions_m'],'svg_dimensions':dimensions,'native_scale':.02,'native_linked_dimensions':'NOT_TESTED: headless projected vertex extraction returns no vertices; invalid zero dimensions removed'}}
 (out/'cad-audit.json').write_text(json.dumps(result,indent=2));A.closeDocument(st.Name);A.closeDocument(d.Name)
if __name__=='__main__':
 import subprocess
 subprocess.run(['node',str(ROOT/'scripts/stage2b.mjs'),'preflight'],cwd=ROOT,check=True)
 spec=json.loads(SPEC.read_text());root=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'cad/stage2b/generated'
 for rev in spec['revisions']:run(rev,root/rev['id'])
