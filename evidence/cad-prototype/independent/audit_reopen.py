import sys,json,importlib.util
sys.path.append('/usr/lib/freecad/lib');import FreeCAD as A,Part
from pathlib import Path
root=Path('/tmp/castle-cad-independent/repo');spec=importlib.util.spec_from_file_location('builder',root/'cad/prototype-v1/build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
d=A.openDocument(str(root/'cad/prototype-v1/generated/palisade.FCStd'))
names=[o.Name for o in d.Objects if o.Name.startswith(('Post_','Rail_'))];assert names==['Post_001','Post_002','Post_003','Post_004','Post_005','Rail_001','Rail_002']
assert d.Drawing.TypeId=='TechDraw::DrawPage' and d.FrontView.TypeId=='TechDraw::DrawViewPart'
assert len(d.FrontView.Source)==7
rows=[]
for count,rails,h,s,w in [(2,0,.3,.2,.05),(9,4,3.1,.7,.12),(5,2,2,1.2,.15)]:
 d.Parameters.Count=count;d.Parameters.Rails=rails;d.Parameters.Height=h*1000;d.Parameters.Spacing=s*1000;d.Parameters.Width=w*1000
 d,objs=b.regenerate(d); shapes=[o.Shape for o in objs];total=Part.Compound(shapes);bb=total.BoundBox
 assert len(total.Solids)==count+rails and abs(bb.XLength-((count-1)*s+w)*1000)<1e-6
 assert len(d.FrontView.Source)==count+rails
 rows.append({'count':count,'rails':rails,'xyz_mm':[bb.XLength,bb.YLength,bb.ZLength],'valid':total.isValid()})
d.saveAs('/tmp/castle-cad-independent/variant.FCStd');A.closeDocument(d.Name);d=A.openDocument('/tmp/castle-cad-independent/variant.FCStd');assert d.Parameters.Count==5
step=Part.Shape();step.read(str(root/'cad/prototype-v1/generated/palisade.step'));assert len(step.Solids)==7
sizes=sorted([[round(s.BoundBox.XLength,4),round(s.BoundBox.YLength,4),round(s.BoundBox.ZLength,4)]for s in step.Solids]);assert sizes==sorted([[150,150,2000]]*5+[[4950,99,84]]*2)
# Invalid regeneration must not remove pre-existing component geometry.
count_before=len(d.Objects);d.Parameters.Count=1
try:b.regenerate(d);raise AssertionError('accepted')
except ValueError as e:assert str(e)=='COUNT'
assert len(d.Objects)==count_before
out={'independent_variants':rows,'saved_reopened':True,'step_component_sizes_mm':sizes,'invalid_regeneration_keeps_components':True,'techdraw_reopened':True}
Path('/tmp/castle-cad-independent/independent-cad.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
