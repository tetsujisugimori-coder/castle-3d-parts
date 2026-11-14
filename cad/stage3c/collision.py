"""BRep sampled collision, all candidate pairs, reference fences and ground."""
import sys,json,math,os,itertools
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as A,Part
from state import transition
R=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]);d=A.openDocument(str(out/'assembly.FCStd'));p=d.getObject('Mechanism');l=d.getObject('LockMechanism');objs=[o for o in d.Objects if 'PartID' in o.PropertiesList]
for o in d.Objects:
 if 'KeepUpdated' in o.PropertiesList:o.KeepUpdated=False
moving=[o.Name for o in objs if o.Moving]
f=A.openDocument(str(R/'cad/stage2c/generated/B0/assembly.FCStd'));fixed=[]
for side,dx in [('Left',-3525),('Right',3525)]:
 for o in f.Objects:
  if 'PartID' in o.PropertiesList and o.Name.startswith('U01_'):
   s=o.Shape.copy();s.translate(A.Vector(dx,0,0));fixed.append(('FENCE_'+side+'_'+o.Name,s))
A.closeDocument(f.Name);fixed.append(('GROUND',Part.makeBox(12000,12000,10,A.Vector(-6000,-6000,-10))))
def setpose(a,b):transition(d,a,b/1000)
def measure(a,sa,b,sb):
 if not sa.isValid() or not sb.isValid() or not sa.Solids or not sb.Solids:raise ValueError('INVALID_SOLID')
 # Disjoint boxes prove zero intersection; overlapping boxes always use exact BRep Boolean.
 ba=sa.BoundBox;bb=sb.BoundBox;disjoint=any(getattr(ba,k+'Max')<getattr(bb,k+'Min') or getattr(bb,k+'Max')<getattr(ba,k+'Min') for k in 'XYZ')
 dist=sa.distToShape(sb)[0]/1000;v=0.0 if disjoint else sa.common(sb).Volume
 if not math.isfinite(v) or not math.isfinite(dist) or v<0 or dist<0:raise ValueError('INVALID_NUMBER')
 return {'a':a,'b':b,'distance_m':dist,'overlap_mm3':v,'linear_penetration_depth':'NOT_COMPUTED','contact':'PENETRATION' if v>1e-4 else 'TOUCHING' if dist<1e-8 else 'CLEAR'}
def sample(a,b,only=None):
 setpose(a,b);shapes=[(o.Name,o.Shape) for o in objs]+fixed;rows=[]
 for i,(aid,sa) in enumerate(shapes):
  for bid,sb in shapes[:i]:
   if only is not None and aid not in only and bid not in only:continue
   rows.append(measure(aid,sa,bid,sb))
 return rows
fail=[];samples=[]
for a in range(91):
 rows=sample(a,0,moving);fail += [[a,0,r['a'],r['b'],r['overlap_mm3']] for r in rows if r['contact']=='PENETRATION'];samples.append({'angle_degrees':a,'bolt_m':0,'pairs':rows});print('angle',a,'failures',len(fail),flush=True)
fixedrows=[x for x in sample(0,0) if x['a'] not in moving and x['b'] not in moving];fail += [[0,0,r['a'],r['b'],r['overlap_mm3']] for r in fixedrows if r['contact']=='PENETRATION']
bolts=[]
# 1mm samples across the complete 140mm parameter interval, no continuous proof.
for b in range(141):
 rows=sample(0,b,['GATE_Bolt']);fail += [[0,b/1000,r['a'],r['b'],r['overlap_mm3']] for r in rows if r['contact']=='PENETRATION'];bolts.append({'angle_degrees':0,'bolt_m':b/1000,'position_m':b/1000,'pairs':rows})
(out/'collision.json').write_text(json.dumps({'generator_sha256':__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),'cad_sha256':__import__('hashlib').sha256((out/'assembly.FCStd').read_bytes()).hexdigest(),'method':'OpenCASCADE BRep common volume and distToShape; disjoint AABB proves zero volume only, overlapping AABB always exact Boolean','tolerance_mm3':1e-4,'distance_tolerance_m':1e-8,'continuous_path':'UNKNOWN','contact_note':'TOUCHING is geometric contact, not strength or load transfer proof.','samples':samples,'bolt_samples':bolts,'fixed_pairs':fixedrows,'failures':fail,'sampling':{'door_degrees':1,'bolt_m':.001,'range_deg':[0,90],'range_m':[0,.14],'unsampled_intervals':'UNKNOWN'}},separators=(',',':')))
print('FAILURES',fail[:30],flush=True)
# Fail closed state counterexamples and geometry mutation without saving over source.
faults=[]
for a,b in [(1,140),(45,1),(-1,0),(91,0),(0,-1),(0,141),(float('nan'),0)]:
 try:setpose(a,b)
 except ValueError:faults.append({'input':[str(a),b],'detected':True})
 else:raise AssertionError('INVALID_STATE_ACCEPTED')
setpose(0,0);o=d.getObject('GATE_Bolt');shift=o.Shape.copy();shift.translate(A.Vector(0,30,0));bad=measure('shifted_bolt',shift,'guide',d.getObject('GATE_BoltGuide_Right').Shape);assert bad['overlap_mm3']>1e-4;faults.append({'fault':'bolt_axis_shift_30mm','detected':True,'overlap_mm3':bad['overlap_mm3']})
# Width above bore clearance produces real interference, no zero-clearance loophole.
l.BoltWidth=24;d.recompute();bore=d.getObject('GATE_BoltGuide_RightBore');bore.setExpression('Width',None);bore.Width=22;d.recompute();bad=measure('wide_bolt',o.Shape,'guide',d.getObject('GATE_BoltGuide_Right').Shape);assert bad['overlap_mm3']>1e-4;faults.append({'fault':'bolt_width_exceeds_guide','detected':True,'overlap_mm3':bad['overlap_mm3']});l.BoltWidth=20;bore.setExpression('Width','LockMechanism.BoltWidth + 2*LockMechanism.GuideGap');d.recompute()
# Forced rotation while engaged geometrically obstructs receiver, beyond software guard.
l.BoltPosition=140;p.Angle=1;d.recompute();bad=measure('forced_locked_rotation',o.Shape,'receiver',d.getObject('GATE_BoltReceiver').Shape);assert bad['overlap_mm3']>1e-4;faults.append({'fault':'forced_locked_rotation_1deg','detected':True,'overlap_mm3':bad['overlap_mm3']});setpose(0,0)
(out/'native-tests.json').write_text(json.dumps({'faults':faults,'state_contract':'PASS','source_saved':False,'continuous_path':'UNKNOWN'},indent=2))
assert not fail,fail[:20]
print('COLLISION PASS',flush=True);os._exit(0)
