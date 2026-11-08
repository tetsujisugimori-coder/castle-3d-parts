import sys,json,hashlib,subprocess
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
root=Path.cwd(); results=[]
for rev in ['B0','B1','B2']:
 base=root/'cad/stage2b/generated'/rev;d=A.openDocument(str(base/'assembly.FCStd'));objs=[o for o in d.Objects if 'PartID' in o.PropertiesList];b=Part.Compound([o.Shape for o in objs]).BoundBox
 expected={'B0':[10.95,.249,2.2],'B1':[10.95,.249,2.4],'B2':[11.15,.249,2.4]}[rev]
 dims=[b.XLength/1000,b.YLength/1000,b.ZLength/1000];assert len(objs)==14 and all(abs(x-y)<1e-6 for x,y in zip(dims,expected))
 st=Part.Shape();st.read(str(base/'assembly.step'));assert len(st.Solids)==14
 assert all(abs(getattr(st.BoundBox,k)-getattr(b,k))<1e-5 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
 views=[]
 for n in ['FrontView','TopView','SideView']:
  v=d.getObject(n);assert v and len(v.Source)==14;views.append({'name':n,'direction':list(v.Direction),'scale':v.Scale,'source_count':len(v.Source)})
 ids=[o.Name for o in objs];assert len(set(ids))==14
 p=d.getObject('U01_Parameters');old=p.height.Value;p.height=old+50;d.recompute();assert abs(d.getObject('U01_Post_001').Shape.BoundBox.ZLength-old-50)<1e-6
 A.closeDocument(d.Name);results.append({'revision':rev,'dimensions_m':dims,'step_solids':len(st.Solids),'views':views,'edit_recompute':True})
# Compare existing bytes with actual fixed git commit, independent of supplied manifest.
files=subprocess.check_output(['git','ls-tree','-r','--name-only','34f43b3b1765de7a52994adb7175dc2c146f8db3']).decode().splitlines()
for p in files:assert subprocess.check_output(['git','show','34f43b3b1765de7a52994adb7175dc2c146f8db3:'+p])==(root/p).read_bytes(),p
out={'mode':'independent FreeCAD module reopen, not GUI','software':A.Version(),'preserved_originals':len(files),'rows':results}
(root/'evidence/stage2b/independent/reopen-results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
