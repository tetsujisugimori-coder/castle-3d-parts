import os,sys,json,hashlib,tempfile,itertools,math
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import TechDrawGui
A.ConfigSet("AppTempPath",tempfile.gettempdir()+"/")
ROOT=Path.cwd();OUT=ROOT/'evidence/stage3c/independent';gen=ROOT/'cad/stage3c/generated'
import shutil
isolated=OUT/'tmp'/'portable';isolated.mkdir(parents=True,exist_ok=True)
shutil.copy2(gen/'assembly.FCStd',isolated/'only.FCStd')
d=A.openDocument(str(isolated/'only.FCStd'));d.recompute();
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
p=d.getObject('Mechanism');l=d.getObject('LockMechanism');objs=[o for o in d.Objects if 'PartID' in o.PropertiesList]
assert len(objs)==23 and len(set(o.PartID for o in objs))==23
p.Angle=0;l.BoltPosition=0;d.recompute();base={o.Name:o.Shape.copy() for o in objs};legacy=A.openDocument(str(ROOT/'cad/stage3b/generated/assembly.FCStd'));preserve=[]
for o in legacy.Objects:
 if 'PartID' not in o.PropertiesList:continue
 n=d.getObject(o.Name);delta=n.Shape.cut(o.Shape).Volume+o.Shape.cut(n.Shape).Volume;assert delta<.001,(o.Name,delta);preserve.append({'id':o.Name,'symmetric_difference_mm3':delta})
A.closeDocument(legacy.Name)
rows=[]
for angle,bolt in [(0,0),(0,0.5),(0,1.5),(0,37.5),(0,70),(0,139.5),(0,140),(.125,0),(.5,0),(22.5,0),(45,0),(67.5,0),(89.9,0),(90,0)]:
 p.Angle=angle;l.BoltPosition=bolt;d.recompute();pairs=[]
 for o in objs:
  s=base[o.Name].copy()
  if o.Name=='GATE_Bolt':s.translate(A.Vector(bolt,0,0))
  if o.Moving:s.rotate(A.Vector(-540,0,100),A.Vector(0,0,1),angle)
  delta=s.cut(o.Shape).Volume+o.Shape.cut(s).Volume;assert delta<.01,(angle,bolt,o.Name,delta)
  assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,'solid')
 for a,b in itertools.combinations(objs,2):
  v=a.Shape.common(b.Shape).Volume;dist=a.Shape.distToShape(b.Shape)[0];pairs.append({'a':a.Name,'b':b.Name,'distance_mm':dist,'intersection_mm3':v,'state':'INTERFERENCE' if v>1e-4 else 'CONTACT' if dist<1e-5 else 'CLEAR'})
 rows.append({'angle_degrees':angle,'bolt_mm':bolt,'pairs':pairs})
(OUT/'native-pairs.json').write_text(json.dumps({'poses':rows,'original_members':preserve},indent=2))
# Save a nonzero candidate and reload without modifying generated original.
p.Angle=0;l.BoltPosition=70;d.recompute();temp=OUT/'review-half-bolt.FCStd';d.saveAs(str(temp));A.closeDocument(d.Name);d=A.openDocument(str(temp));d.recompute();assert d.LockMechanism.BoltPosition.Value==70
assert abs(d.GATE_Bolt.Shape.BoundBox.XMin-(-400+70))<1e-5
A.closeDocument(d.Name)
result={'method':'Independent FreeCAD BRep common and distToShape; absolute base-shape rotation/translation cross-check','source_sha256':hashlib.sha256((gen/'assembly.FCStd').read_bytes()).hexdigest(),'original_members':preserve,'parts':23,'poses':rows,'save_reload_half_bolt':True,'continuous_path':'UNKNOWN','physical_strength':'NOT_TESTED','tolerance_mm3':1e-4}
(OUT/'native-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'poses':len(rows),'pairs':sum(len(r['pairs']) for r in rows),'penetrations':[(r['angle_degrees'],r['bolt_mm'],p) for r in rows for p in r['pairs'] if p['state']=='INTERFERENCE']}))
