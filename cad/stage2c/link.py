"""Generate semantic SVG and link manifest from reopened CAD and measured native dims."""
import sys,json,hashlib,html,re
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part,TechDraw
ROOT=Path(__file__).resolve().parents[2]
BASE='d1c367ca4b143cacc45ba8848b026701abf03b9c'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def generate(out,rev):
 data=json.loads((out/'native-audit.json').read_text());dims=data['restored'];d=A.openDocument(str(out/'assembly.FCStd'));objs=[o for o in d.Objects if 'PartID' in o.PropertiesList];comp=Part.Compound([o.Shape for o in objs]);bb=comp.BoundBox;scale=.025
 # All views share local X/Y page coordinates; UI hides two view groups.
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="340mm" viewBox="0 0 420 340" data-revision="{rev}">']
 transforms={'front':f'matrix(0 {scale} {-scale} 0 {35-bb.XMin*scale} 110)','top':f'matrix({scale} 0 0 {scale} {35-bb.XMin*scale} 80)','side':f'matrix(0 {-scale} {scale} 0 70 110)'}
 dirs={'front':(0,-1,0),'top':(0,0,1),'side':(1,0,0)}
 for view in dirs:
  svg.append(f'<g data-view="{view}" id="view-{view}"><rect x="0" y="0" width="420" height="340" fill="white"/><text x="10" y="14" font-family="sans-serif" font-size="6">PAL-ASSEMBLY / {rev} / {view.upper()} / mm / D prototype</text>')
  for o in objs:
   geom=TechDraw.projectToSVG(o.Shape,A.Vector(*dirs[view])).replace('stroke-width="1.0"','stroke-width="8"')
   geom=re.sub(r'<\?xml[^>]*\?>','',geom);geom=re.sub(r'\s+id\s*=\s*"[^"]*"','',geom)
   svg.append(f'<g id="{view}-{o.Name}" data-part-id="{o.Name}" transform="{transforms[view]}">{geom}</g>')
  # Values are native getRawValue, not nominal spec text. Each witness span is scaled.
  for i,x in enumerate(x for x in dims if x['view']==view):
   y=145+i*17;value=x['value_mm'];svg.append(f'<g id="dimension-{view}-{x["id"]}" data-dimension-id="{x["id"]}" data-value-m="{x["value_m"]}" data-kind="true" font-family="sans-serif" font-size="3.8"><text x="12" y="{y}">{html.escape(x["label"])}: {value:.1f} mm (true 3D)</text><path d="M12 {y+5} h{value*scale} M12 {y+3} v4 M{12+value*scale} {y+3} v4" stroke="#145a80" stroke-width=".25" fill="none"/></g>')
  svg.append('<text x="10" y="328" font-family="sans-serif" font-size="3.5">Projection 1:40. Native linked measurements with scale witnesses below. Geometry is prototype D.</text></g>')
 svg.append('</svg>');(out/'drawing.svg').write_text(''.join(svg))
 refs=[{'id':r['id'],'path':r['path']} for r in json.loads((ROOT/'design/stage2b/research-snapshot.json').read_text())['records']]
 parts=[]
 for o in objs:
  b=o.Shape.BoundBox;parts.append({'id':o.Name,'unit_id':o.Name.split('_')[0],'label':('柱' if '_Post_' in o.Name else '横木'),'freecad_object':o.Name,'step_object':o.Name,'glb_node':o.Name,'svg_ids':{v:v+'-'+o.Name for v in dirs},'dimension_ids':[x['id'] for x in dims if o.Name in x['part_ids']],'bounds_m':[getattr(b,k)/1000 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']],'research_refs':refs})
 md=[{k:x[k] for k in ['id','label','value_m','kind','part_ids']} for x in dims]
 prior={'B0':None,'B1':'B0','B2':'B1'}[rev];changes=[]
 if prior:
  previous=json.loads((out.parent/prior/'link-manifest.json').read_text());old={x['id']:x['value_m'] for x in previous['dimensions']}
  changes=[{'dimension_id':x['id'],'before_m':old[x['id']],'after_m':x['value_m']} for x in md if abs(old[x['id']]-x['value_m'])>1e-9]
 m={'schema_version':1,'revision':rev,'basis':'D','cad_eligibility':'reference_only','assembly_id':'PAL-ASSEMBLY','source_commit':BASE,'previous_revision':prior,'changes':changes,'files':{'glb':{'path':'assembly.glb','sha256':h(out/'assembly.glb')},'svg':{'path':'drawing.svg','sha256':h(out/'drawing.svg')}},'parts':parts,'dimensions':md,'native_svg_exports':{v:{'path':'native-'+v+'.svg','sha256':h(out/('native-'+v+'.svg'))} for v in dirs},'research_snapshot_sha256':h(ROOT/'design/stage2b/research-snapshot.json')}
 (out/'link-manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
 source=['cad/stage2b/build.py','cad/stage2b/drawing.py','blender/stage2b/build.py','cad/stage2c/native.py','cad/stage2c/link.py','cad/stage2c/run.py','cad/stage2c/template.svg']
 outputs={p.name:h(p) for p in sorted(out.iterdir()) if p.is_file() and p.suffix not in ['.FCStd1','.FCBak'] and p.name!='generation-manifest.json'}
 (out/'generation-manifest.json').write_text(json.dumps({'revision':rev,'source_commit':BASE,'spec_sha256':h(ROOT/'cad/stage2b/spec.json'),'source_scripts':{p:h(ROOT/p) for p in source},'outputs':outputs},indent=2)+'\n');A.closeDocument(d.Name)
if __name__=='__main__':generate(Path(sys.argv[1]),sys.argv[2])
