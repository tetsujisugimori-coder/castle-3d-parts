"""Portable artifact verification, NOT a substitute for real CAD execution."""
import json,hashlib,math,sys,zipfile,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def same(a,b):assert a==b,(a,b)
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def expected(rev):
 s=next(x for x in json.loads((ROOT/'cad/stage2b/spec.json').read_text())['revisions'] if x['id']==rev);out={}
 for u in s['units']:
  uid=u['instance_id'];p=u['parameters'];height=p['height'];width=p['width'];L=(p['count']-1)*p['spacing']+width
  out.update({uid+'-post-height':height,uid+'-post-centres':p['spacing'],uid+'-post-width':width,uid+'-post-depth':width,uid+'-unit-width':L})
  for i in range(1,3):out[uid+f'_Rail_{i:03d}-length']=L;out[uid+f'_Rail_{i:03d}-elevation']=height*i/3
 lo=min(u['position_m'][0]-((u['parameters']['count']-1)*u['parameters']['spacing']+u['parameters']['width'])/2 for u in s['units']);hi=max(u['position_m'][0]+((u['parameters']['count']-1)*u['parameters']['spacing']+u['parameters']['width'])/2 for u in s['units']);out['assembly-width']=hi-lo
 return out

def validate_dimensions(rows,rev,field='value_m',scale=1):
 ex=expected(rev);same(len(rows),19);same(set(x['id'] for x in rows),set(ex))
 for d in rows:assert finite(d[field]) and abs(d[field]/scale-ex[d['id']])<1e-8,d['id'];same(d['kind'],'true')

def validate_xml(xml,rows):
 r=E.fromstring(xml);objs={o.attrib['name']:o for o in r.findall('./ObjectData/Object')}
 def prop(obj,p):return objs[obj].find(f'./Properties/Property[@name="{p}"]')
 for d in rows:
  n=d['native_object'];w=d['witness'];same([(x.attrib['obj'],x.attrib['sub']) for x in prop(n,'References3D').findall('.//Link')],[(w,'Edge1')]);same([(x.attrib['obj'],x.attrib['sub']) for x in prop(n,'References2D').findall('.//Link')],[(d['view'].capitalize()+'View','')]);same(prop(n,'MeasureType').find('Integer').attrib['value'],'0');same(prop(n,'Arbitrary').find('Bool').attrib['value'],'false');same(prop(n,'FormatSpec').find('String').attrib['value'],'%.1f')
  expr={x.attrib['path']:x.attrib['expression'] for x in prop(w,'ExpressionEngine').findall('.//Expression')};same(expr,d['expressions'])
  pts=[float(prop(w,k).find('Float').attrib['value']) for k in ['X1','Y1','Z1','X2','Y2','Z2']];assert abs(math.dist(pts[:3],pts[3:])-d['value_mm'])<1e-6
 return True

def check(root=ROOT,outputs=None):
 same(h(root/'design/stage2c/baseline.json'),'57f2855f39fb1642be5d838f53dd226e02a1e024505d912dedda69d79d53d47a');base=json.loads((root/'design/stage2c/baseline.json').read_text());same(base['commit'],'d1c367ca4b143cacc45ba8848b026701abf03b9c');same(len(base['hashes']),839)
 for p,hash in base['hashes'].items():
  if h(root/p)==hash:continue
  allowed={'.github/workflows/pages.yml','scripts/research-cad.mjs','scripts/stage2b.mjs','tests/hypothesis-preservation.test.mjs','scripts/cad-prototype.mjs','scripts/design-register.mjs','scripts/verification-register.mjs','scripts/hypothesis-evidence.mjs','cad/stage2c/check.py'}
  assert p in allowed,('ORIGINAL_CHANGED',p)
  migration=json.loads((root/'design/stage2d/code-migrations.json').read_text())['files'];same(set(migration),allowed);entry=migration[p]
  same(entry['archive'],'design/stage2d/originals/'+p+'.txt');same(h(root/entry['archive']),hash);same(entry['before_sha256'],hash);same(h(root/p),entry['after_sha256'])
 results=[];outputs=outputs or root/'cad/stage2c/generated'
 for rev in ['B0','B1','B2']:
  p=outputs/rev;m=json.loads((p/'generation-manifest.json').read_text());same(m['revision'],rev);same(m['source_commit'],base['commit']);same(m['spec_sha256'],h(root/'cad/stage2b/spec.json'))
  required=['assembly.FCStd','assembly.step','assembly.blend','assembly.glb','native-audit.json','link-manifest.json','drawing.svg','native-front.svg','native-top.svg','native-side.svg']
  assert all(k in m['outputs'] for k in required)
  for f,hash in m['outputs'].items():assert Path(f).name==f;same(h(p/f),hash)
  for f,hash in m['source_scripts'].items():same(h(root/f),hash)
  a=json.loads((p/'native-audit.json').read_text());same(a['revision'],rev);same(a['native_linked_dimensions'],'PASS')
  for phase in ['created','reopened','restored']:validate_dimensions(a[phase],rev,'value_mm',1000)
  same(a['created'],a['restored']);same(len(a['fault_controls']),4);assert all(c['actual']=='REJECT' and c['exit']==1 for c in a['fault_controls'])
  with zipfile.ZipFile(p/'assembly.FCStd') as z:assert z.testzip() is None;validate_xml(z.read('Document.xml'),a['restored'])
  lm=json.loads((p/'link-manifest.json').read_text());same(lm['revision'],rev);same(lm['basis'],'D');same(lm['cad_eligibility'],'reference_only');validate_dimensions(lm['dimensions'],rev)
  svg=E.fromstring((p/'drawing.svg').read_text());same(svg.attrib['data-revision'],rev);labels=[e for e in svg.iter() if 'data-dimension-id' in e.attrib];same(len(labels),19)
  for e in labels:val=expected(rev)[e.attrib['data-dimension-id']];assert abs(float(e.attrib['data-value-m'])-val)<1e-8;same(e.attrib['data-kind'],'true');text=''.join(e.itertext());assert f'{val*1000:.1f} mm' in text
  same(len(lm['parts']),14);same(len(set(x['id'] for x in lm['parts'])),14)
  for part in lm['parts']:
   for view,id in part['svg_ids'].items():matches=[e for e in svg.iter() if e.attrib.get('id')==id];same(len(matches),1);same(matches[0].attrib['data-part-id'],part['id'])
  ba=json.loads((p/'blender-audit.json').read_text());ca=json.loads((p/'cad-audit.json').read_text())
  for phase in ['created','blend_reopened','glb_reopened']:
   same(ba[phase]['objects'],14)
   for v,w in zip(ba[phase]['dimensions_m'],ca['created']['dimensions_m']):assert abs(v-w)<1e-5
  results.append({'revision':rev,'dimensions':19,'parts':14,'native_archive':'PASS','cad_execution':'recorded separate real FreeCAD audit','outputs':len(m['outputs'])})
 return {'status':'PASS','preserved_files':839,'revisions':results}
if __name__=='__main__':print(json.dumps(check(),indent=2))
