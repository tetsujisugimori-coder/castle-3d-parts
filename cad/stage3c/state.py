"""CAD state authority. Web consumes the same JSON contract; direct edits require validation."""
import json,math,tempfile,os
from pathlib import Path
SPEC=json.loads((Path(__file__).parent/'spec.json').read_text())
def validate_state(angle_degrees,bolt_m):
 if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in [angle_degrees,bolt_m]):raise ValueError('NONFINITE')
 lo,hi=SPEC['angle_range_deg'];blo,bhi=SPEC['bolt']['travel_m']
 if not lo<=angle_degrees<=hi or not blo<=bolt_m<=bhi:raise ValueError('RANGE')
 if angle_degrees!=0 and bolt_m!=0:raise ValueError('INTERLOCK')
 return True
def validate_document(doc):
 p=doc.getObject('Mechanism');l=doc.getObject('LockMechanism')
 if not p or not l:raise ValueError('MISSING_MECHANISM')
 validate_state(p.Angle.Value,l.BoltPosition.Value/1000)
 if any(abs(getattr(p,'Pivot'+axis).Value/1000-v)>1e-9 for axis,v in zip('XYZ',SPEC['pivot_m'])) or [p.MinimumAngle.Value,p.MaximumAngle.Value]!=SPEC['angle_range_deg']:raise ValueError('AXIS_LIMIT_MISMATCH')
 if abs(l.BoltTravel.Value/1000-SPEC['bolt']['lock_m'])>1e-9:raise ValueError('TRAVEL_MISMATCH')
 if not 880<=l.BoltLength.Value<=900 or not 18<=l.BoltWidth.Value<=22 or not 35<=l.BoltHeight.Value<=45 or not .5<=l.GuideGap.Value<=2:raise ValueError('DIMENSION_BOUNDS')
 ids=[o.PartID for o in doc.Objects if 'PartID' in o.PropertiesList]
 if set(ids)!=set(SPEC['part_ids']) or len(ids)!=len(SPEC['part_ids']):raise ValueError('PART_IDS')
 for id in ids:
  o=doc.getObject(id)
  if not o or not o.Shape.isValid() or len(o.Shape.Solids)!=1:raise ValueError('INVALID_SHAPE')
 for name in ['GATE_BoltGuide_Left','GATE_BoltGuide_Right','GATE_BoltReceiver']:
  hole=doc.getObject(name+'Bore')
  if not hole or abs(hole.Width.Value-l.BoltWidth.Value-2*l.GuideGap.Value)>1e-7 or abs(hole.Height.Value-l.BoltHeight.Value-2*l.GuideGap.Value)>1e-7:raise ValueError('BORE_FOLLOW')
 return True
def transition(doc,angle_degrees,bolt_m):
 validate_state(angle_degrees,bolt_m)
 # atomic validation before property mutation; no auto unlocking or closing.
 p=doc.getObject('Mechanism');l=doc.getObject('LockMechanism');old=(p.Angle.Value,l.BoltPosition.Value)
 try:
  p.Angle=angle_degrees;l.BoltPosition=bolt_m*1000;doc.recompute();validate_document(doc)
 except Exception:
  p.Angle=old[0];l.BoltPosition=old[1];doc.recompute();raise
 return {'angle_degrees':angle_degrees,'bolt_m':bolt_m}
def load_document(path,name='GateLockReload'):
 """Restore embedded templates without depending on the original template paths.
 FreeCAD Python openDocument in this environment leaves TransientDir empty.
 Explicit documented restore uses a caller-owned writable transient directory.
 """
 import FreeCAD as A
 doc=A.newDocument(name);doc.TransientDir=tempfile.mkdtemp(prefix='gate3c-restore-')+'/';doc.FileName=str(Path(path).resolve());doc.restore();doc.recompute();return doc
