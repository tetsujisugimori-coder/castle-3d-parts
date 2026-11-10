"""Headless BRep collision, separately from Qt drawing event loop."""
import sys,os,json,math,tempfile
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
ROOT=Path(__file__).resolve().parents[2];OUT=Path(sys.argv[1]).resolve()
d=A.openDocument(str(OUT/'assembly.FCStd'));p=d.getObject('Mechanism');objs=[o for o in d.Objects if 'PartID' in o.PropertiesList]
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
MOVING=[o.Name for o in objs if o.Moving]
legacy=json.loads((OUT/'native-stage-audit.json').read_text())['legacy_poses']
def rec(d):d.recompute()
def pose(a):
 if not isinstance(a,(int,float)) or not math.isfinite(a) or not p.MinimumAngle.Value<=a<=p.MaximumAngle.Value:raise ValueError('ANGLE_RANGE')
 assert 0<=p.MinimumAngle.Value<p.MaximumAngle.Value<=90,'LIMIT_RANGE'
 p.Angle=a;rec(d)
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,A.Vector(x,y,z))
# Exact BRep collision at 1 degree, including reference fence solids and ground.
f=A.openDocument(str(ROOT/'cad/stage2c/generated/B0/assembly.FCStd'));fences=[]
for side,dx in [('Left',-3525),('Right',3525)]:
 for o in f.Objects:
  if 'PartID' in o.PropertiesList and o.Name.startswith('U01_'):
   s=o.Shape.copy();s.translate(A.Vector(dx,0,0));fences.append(('FENCE_'+side+'_'+o.Name,s))
A.closeDocument(f.Name)
rows=[];fail=[]
for angle in range(91):
 pose(angle);pairs=[];shapes=[(o.Name,o.Shape) for o in objs]+fences+[('GROUND',box(-6000,-6000,-10,12000,12000,10))]
 for i,(a,sa) in enumerate(shapes):
  for b,sb in shapes[:i]:
   if angle!=0 and a not in MOVING and b not in MOVING:continue
   volume=sa.common(sb).Volume;distance=sa.distToShape(sb)[0]/1000
   pairs.append({'a':a,'b':b,'distance_m':distance,'overlap_mm3':volume,'linear_penetration_depth':'NOT_COMPUTED','contact':'PENETRATION' if volume>1e-4 else 'TOUCHING' if distance<1e-8 else 'CLEAR'})
   if volume>1e-4:fail.append([angle,a,b,volume])
 rows.append({'angle_degrees':angle,'pairs':pairs})
 print('sample',angle,'fail',len(fail),flush=True)
fixed_pairs=[p for p in rows[0]['pairs'] if p['a'] not in MOVING and p['b'] not in MOVING]
rows[0]['pairs']=[p for p in rows[0]['pairs'] if p not in fixed_pairs]
(OUT/'collision.json').write_text(json.dumps({'method':'OpenCASCADE BRep common volume and distToShape; 1 degree samples','tolerance_mm3':1e-4,'continuous_path':'UNKNOWN','contact_note':'Zero-distance geometric contact is not proof of load-bearing or joint function.','samples':rows,'fixed_pairs':fixed_pairs,'failures':fail},separators=(',',':')))
assert not fail,fail[:10]
p.MinimumAngle=10;p.MaximumAngle=60
for a,stop in [(10,'GATE_Stop_Closed'),(60,'GATE_Stop_Open')]:
 pose(a);door=d.getObject('GATE_Door').Shape;fixture=d.getObject(stop).Shape
 assert door.common(fixture).Volume<1e-4 and door.distToShape(fixture)[0]<1e-6,'LIMIT_CONTACT'
p.MinimumAngle=0;p.MaximumAngle=90;pose(0)
for key in ['PivotX','PivotY','PivotZ','RadialGap']:p.setEditorMode(key,1)
# Native document is saved by drawings.py after all embedded templates are replaced.
manifest={'schema_version':1,'part_id':'GATE-MECHANISM-01','basis':'D','cad_eligibility':'reference_only','unit':'m','up':'Z','pivot_m':[-.54,0,.1],'gltf_pivot_m':[-.54,.1,0],'moving_parent':'GatePivot','moving_ids':MOVING,'angle_bounds':[0,90],'poses':[0,45,90],'collision_ids':[name for name,_ in shapes],'parts':[{'id':o.Name,'moving':o.Moving} for o in objs],'glb':'assembly.glb','collision':'collision.json','native_drawings':['native-'+x+'.svg' for x in ['front','top','side','bearing','trajectory']],'verification':{'sampled_angles':'0..90 inclusive at 1 degree','continuous_path':'UNKNOWN','strength':'NOT_TESTED','historical_structure':'UNKNOWN','manual_gui':'NOT_TESTED'},'legacy_poses':legacy}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'cad-audit.json').write_text(json.dumps({'FreeCAD':A.Version(),'parts':len(objs),'fcstd_reloaded':True,'step_reloaded':True,'native_dimension_edit':True,'legacy_poses':legacy,'pivot_m':manifest['pivot_m']},indent=2))
print('COMPLETE',flush=True)
os._exit(0)
