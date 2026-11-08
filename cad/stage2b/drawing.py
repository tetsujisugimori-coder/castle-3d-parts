"""Deterministic CAD-derived SVG rendering; does not edit native documents."""
import json
import FreeCAD as A, Part, TechDraw
def render(rev,objs,out):
 # True orthographic projections: FreeCAD's projection coordinate basis differs per view.
 comp=Part.Compound([o.Shape for o in objs]); bb=comp.BoundBox; scale=.02
 fx=25-bb.XMin*scale; fy=115.; sx=335-bb.YMin*scale; ty=175.
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="2" markerHeight="2" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#145a80"/></marker></defs><rect width="420" height="297" fill="white"/><g font-family="sans-serif" font-size="4">',f'<text x="10" y="12">PAL-ASSEMBLY / {rev["id"]} / D prototype / reference_only / mm / scale 1:50</text>']
 projections=[('FRONT',(0,-1,0),f'matrix(0 {scale} {-scale} 0 {fx} {fy})',25,38),('TOP',(0,0,1),f'matrix({scale} 0 0 {scale} {fx} {ty})',25,155),('SIDE',(1,0,0),f'matrix(0 {-scale} {scale} 0 {sx} {fy})',330,38)]
 for name,direction,transform,lx,ly in projections:
  projection=TechDraw.projectToSVG(comp,A.Vector(*direction)).replace('stroke-width="1.0"','stroke-width="12.5"')
  svg.extend([f'<text x="{lx}" y="{ly}">{name}</text>',f'<g id="projection-{name}" transform="{transform}">{projection}</g>'])
 dimensions=[]
 def hdim(key,x1,x2,origin_y,y,value):
  assert x2>x1
  svg.append(f'<g stroke="#145a80" stroke-width=".2" fill="none"><path d="M{x1} {origin_y} V{y+2} M{x2} {origin_y} V{y+2}"/><path marker-start="url(#arrow)" marker-end="url(#arrow)" d="M{x1} {y} H{x2}"/></g><text x="{(x1+x2)/2}" y="{y-2}" text-anchor="middle" fill="#145a80">{value:.1f}</text>')
  dimensions.append({'id':key,'axis':'X','value_mm':value,'endpoints_page_mm':[[x1,y],[x2,y]],'span_page_mm':x2-x1,'scale':scale})
 def vdim(key,y1,y2,origin_x,x,value):
  assert y2>y1
  svg.append(f'<g stroke="#145a80" stroke-width=".2" fill="none"><path d="M{origin_x} {y1} H{x+2} M{origin_x} {y2} H{x+2}"/><path marker-start="url(#arrow)" marker-end="url(#arrow)" d="M{x} {y1} V{y2}"/></g><text transform="translate({x-2} {(y1+y2)/2}) rotate(-90)" text-anchor="middle" fill="#145a80">{value:.1f}</text>')
  dimensions.append({'id':key,'axis':'vertical','value_mm':value,'endpoints_page_mm':[[x,y1],[x,y2]],'span_page_mm':y2-y1,'scale':scale})
 hdim('overall-width',fx+bb.XMin*scale,fx+bb.XMax*scale,fy,133,bb.XLength)
 vdim('overall-height',fy-bb.ZMax*scale,fy-bb.ZMin*scale,25,15,bb.ZLength)
 # Actual component centres, not nominal strings, establish spacing and rail elevation witnesses.
 for u in rev['units']:
  posts=[o for o in objs if o.Name.startswith(u['instance_id']+'_Post_')];a,b=posts[:2];xa=a.Shape.BoundBox.Center.x;xb=b.Shape.BoundBox.Center.x
  hdim(u['instance_id']+'-post-centres',fx+xa*scale,fx+xb*scale,fy-a.Shape.BoundBox.ZMax*scale,51,xb-xa)
  svg.append(f'<text x="{fx+xa*scale}" y="43" font-size="3">{u["instance_id"]} / {u["unit_revision"]} post centres</text>')
 first=rev['units'][0]['instance_id'];rails=[o for o in objs if o.Name.startswith(first+'_Rail_')]
 for i,o in enumerate(rails):
  z=o.Shape.BoundBox.Center.z;vdim(first+'-rail-centre-'+str(i+1),fy-z*scale,fy,335,352+i*14,z)
 svg.append('<text x="330" y="128" font-size="3">Rail centre elevations above Z=0</text>')
 hdim('side-depth',sx+bb.YMin*scale,sx+bb.YMax*scale,fy,143,bb.YLength)
 svg.append(f'<text x="25" y="194">Plan: overall depth {bb.YLength:.1f} mm (side dimension above).</text>')
 svg.append('<text x="10" y="225">Blue dimensions use actual CAD bounding edges / post and rail centres.</text><text x="10" y="235">PAL-POST: 10 / PAL-RAIL: 4 / PAL-UNIT: U01 + U02. D trial; unconnected units.</text><text x="10" y="245">Native TechDraw linked dimensions NOT_TESTED; SVG regenerated from CAD geometry.</text><text x="10" y="255">Drawing ID PAL-ASM-'+rev['id']+' / Units mm / Front X-Z, Top X-Y, Side Y-Z</text>')
 svg.append('</g></svg>');(out/'drawing.svg').write_text(''.join(svg))
 for dim in dimensions:assert abs(dim['span_page_mm']/scale-dim['value_mm'])<1e-6
 (out/'drawing-measurements.json').write_text(json.dumps({'revision':rev['id'],'scale':scale,'unit':'mm','dimensions':dimensions,'projection_basis':'FreeCAD TechDraw.projectToSVG, per-view transforms'},indent=2))
 return dimensions
if __name__=='__main__':
 import sys
 from pathlib import Path
 # Invoke with FreeCAD library on PYTHONPATH: drawing.py FCStd spec.json B0 new-output-dir.
 doc=A.openDocument(sys.argv[1]);rev=next(r for r in json.loads(Path(sys.argv[2]).read_text())['revisions'] if r['id']==sys.argv[3]);out=Path(sys.argv[4]);out.mkdir(parents=True,exist_ok=False)
 render(rev,[o for o in doc.Objects if 'PartID' in o.PropertiesList],out);A.closeDocument(doc.Name)
