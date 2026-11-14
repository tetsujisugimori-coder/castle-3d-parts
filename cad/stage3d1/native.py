"""Read-only, bounded native CAD evidence. Numerical OCC distances are NOT certified."""
import sys,os,json,hashlib,math,platform,subprocess
from pathlib import Path
sys.path.extend(['/usr/lib/freecad-python3/lib','/usr/lib/freecad/lib'])
import FreeCAD as A
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cad/stage3c'))
from state import load_document,transition
from intervals import classify,validate_cover
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
source=ROOT/'cad/stage3c/generated/assembly.FCStd';before=hashlib.sha256(source.read_bytes()).hexdigest()
d=load_document(source)
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
ids=sorted(o.PartID for o in d.Objects if 'PartID' in o.PropertiesList)
assert len(ids)==23
pairs=[('door','GATE_Door','GATE_Doorstop'),('door','GATE_Spindle_Upper','GATE_Bearing_Upper'),('door','GATE_Door','GATE_Post_Right'),('door','GATE_Door','GATE_Joint_Right'),('door','GATE_Door','GATE_Stop_Open'),('bolt','GATE_Bolt','GATE_BoltGuide_Left'),('bolt','GATE_Bolt','GATE_BoltGuide_Right'),('bolt','GATE_Bolt','GATE_BoltReceiver')]
old=json.loads((ROOT/'cad/stage3c/generated/collision.json').read_text());results=[];consistency=[]
for mode,aid,bid in pairs:
 transition(d,0,0);sa=d.getObject(aid).Shape;box=sa.BoundBox;px=d.getObject('Mechanism').PivotX.Value;py=d.getObject('Mechanism').PivotY.Value
 # L1 radius upper bound avoids an underestimated square root; 22/7 bounds pi.
 radius=max(abs(box.XMin-px),abs(box.XMax-px))+max(abs(box.YMin-py),abs(box.YMax-py))
 speed=radius*22/7/180 if mode=='door' else 1
 def sample(x):
  transition(d,float(x) if mode=='door' else 0,0 if mode=='door' else float(x)/1000)
  a,b=d.getObject(aid).Shape,d.getObject(bid).Shape
  if any(not s.isValid() or len(s.Solids)!=1 for s in (a,b)):raise ValueError('INVALID_SOLID')
  distance=a.distToShape(b)[0];volume=a.common(b).Volume
  if not all(math.isfinite(v) and v>=0 for v in (distance,volume)):raise ValueError('INVALID_OCC_RESULT')
  return {'distance':str(distance),'absolute_error':None,'certified':False,'penetration_proven':False,'observed_overlap_mm3':volume,'observed_violation':volume>1e-4,'contact':'PENETRATION_OBSERVED' if volume>1e-4 else 'TOUCHING_OBSERVED' if distance<1e-5 else 'CLEAR_OBSERVED','method':'OCC distToShape/common; absolute numerical error is not certified'}
 hi=90 if mode=='door' else 140
 rows=classify(0,hi,sample,speed,max_depth=4);validate_cover(rows,0,hi)
 baselines=old['samples'] if mode=='door' else old['bolt_samples']
 # Existing 91/141 records remain authoritative only as discrete observations.
 for index in (0,len(baselines)//2,len(baselines)-1):
  entry=baselines[index];position=entry['angle_degrees'] if mode=='door' else entry['bolt_m']*1000
  previous=next(r for r in entry['pairs'] if {r['a'],r['b']}=={aid,bid});now=sample(position)
  consistency.append({'mode':mode,'pair':[aid,bid],'position':position,'distance_delta_mm':abs(float(now['distance'])-previous['distance_m']*1000),'volume_delta_mm3':abs(now['observed_overlap_mm3']-previous['overlap_mm3'])})
 results.append({'mode':mode,'pair':[aid,bid],'unit':'degrees' if mode=='door' else 'mm','last_sample_bounds_mm':{name:[getattr(d.getObject(name).Shape.BoundBox,k) for k in ('XMin','YMin','ZMin','XMax','YMax','ZMax')] for name in (aid,bid)},'radius_upper_mm':radius,'speed_bound_mm_per_unit':speed,'intervals':rows})
 print(mode,aid,bid,'complete',flush=True)
assert all(r['distance_delta_mm']<1e-5 and r['volume_delta_mm3']<1e-4 for r in consistency)
interlocks=[]
for angle,bolt in [(1,.001),(90,.14),(45,.07)]:
 try:transition(d,angle,bolt)
 except ValueError:interlocks.append({'angle':angle,'bolt_m':bolt,'rejected':True})
 else:raise AssertionError('INTERLOCK_ACCEPTED')
A.closeDocument(d.Name)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
report={'schema':1,'source_sha256':before,'part_ids':ids,'freecad':A.Version(),'platform':platform.platform(),'git':subprocess.check_output(['git','show','-s','--format=%H %T'],cwd=ROOT,text=True).strip(),'baseline_counts':{'angles':len(old['samples']),'positions':len(old['bolt_samples']),'pairs':sum(len(x['pairs']) for x in old['samples']+old['bolt_samples'])+len(old['fixed_pairs'])},'results':results,'discrete_crosschecks':consistency,'interlocks':interlocks,'source_unchanged':True,'scope':'8 representative pairs; no all-parts or physical safety claim','cad_continuous':'UNKNOWN','reason':'OCC distance absolute error lacks a validated bound; motion bound alone does not certify geometry','manual_gui':'NOT_TESTED'}
(out/'native.json').write_text(json.dumps(report,indent=2));print('NATIVE EVIDENCE COMPLETE',flush=True)
# Native finalizer may crash in some installations; avoid implicit Qt teardown after evidence flush.
os._exit(0)
