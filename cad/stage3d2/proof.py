"""Exact rational AABB-union model certificates. Never certifies imported BRep."""
from fractions import Fraction as Q
from math import isqrt
import hashlib,json

def number(x):
 if type(x) not in (int,str):raise ValueError('EXACT_NUMBER_REQUIRED')
 return Q(x)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def box(b):
 if not isinstance(b,list) or len(b)!=6:raise ValueError('BOX')
 b=list(map(number,b))
 if any(b[i]>=b[i+3] for i in range(3)):raise ValueError('DEGENERATE_BOX')
 return b
def translated(b,v,t):return [b[i]+v[i%3]*t for i in range(6)]
def squared(a,b):return sum(max(a[i]-b[i+3],b[i]-a[i+3],Q(0))**2 for i in range(3))
def sqrt_enclosure(q):
 if q<0:raise ValueError('NEGATIVE_SQUARE')
 scale=2**32;k=isqrt(q.numerator*scale**2//q.denominator);lo=Q(k,scale)
 return lo,lo if lo*lo==q else Q(k+1,scale)
def verify(c,expected_digest,observed_sources,max_depth=8):
 if type(max_depth) is not int or not 0<=max_depth<=10:raise ValueError('DEPTH')
 if digest(c)!=expected_digest:raise ValueError('CONTRACT_BINDING')
 if c.get('schema')!='aabb-union-translation-v1' or c.get('unit')!='mm':raise ValueError('UNSUPPORTED_MODEL_OR_UNIT')
 if not c.get('sources') or c['sources']!=observed_sources:raise ValueError('SOURCE_BINDING')
 if c.get('parts')!=['GATE_Bolt','GATE_BoltGuide_Left']:raise ValueError('PART_BINDING')
 if number(c['door_degrees'])!=0:raise ValueError('DOOR_STATE')
 a=box(c['moving_box']);bs=[box(b) for b in c['obstacle_boxes']]
 if not bs:raise ValueError('EMPTY_OBSTACLE')
 va=list(map(number,c['moving_velocity']));vb=list(map(number,c['obstacle_velocity']))
 if len(va)!=3 or len(vb)!=3:raise ValueError('VELOCITY')
 start,end=map(number,c['range']);required=number(c['required_clearance'])
 if start>=end or required<0:raise ValueError('RANGE_CLEARANCE')
 L=sum(abs(x-y) for x,y in zip(va,vb));rows=[]
 def visit(l,h,depth):
  m=(l+h)/2;aa=translated(a,va,m);ob=[translated(b,vb,m) for b in bs]
  sq=min(squared(aa,b) for b in ob);lo,hi=sqrt_enclosure(sq)
  penetration=any(all(min(aa[i+3],b[i+3])>max(aa[i],b[i]) for i in range(3)) for b in ob)
  motion=L*(h-l)/2;lower=lo-motion
  status='FAIL' if penetration else 'PASS' if lower>required else 'UNKNOWN'
  if status=='UNKNOWN' and depth<max_depth:visit(l,m,depth+1);visit(m,h,depth+1);return
  rows.append({'lo':str(l),'hi':str(h),'mid':str(m),'distance_squared':str(sq),'distance_lower':str(lo),'distance_upper':str(hi),'distance_absolute_error':str(hi-lo),'midpoint_estimate':str(hi),'motion_upper':str(motion),'clearance_lower':str(lower),'status':status,'contact':'PENETRATION' if penetration else 'CONTACT' if sq==0 else 'SEPARATE','witness_scope':'exact analytical model'})
 visit(start,end,0)
 return {'contract_sha256':expected_digest,'parts':c['parts'],'range':c['range'],'unit':'mm','guarantees':{'shape_correspondence':{'status':'UNKNOWN','scope':'imported CAD BRep','reason':'nominal parameter/source correspondence and sampled observations do not prove set equality or a Hausdorff enclosure'},'distance_error':{'status':'PASS','scope':'exact analytical AABB union only','method':'integer square root dyadic outward enclosure; upper estimate error <= upper-lower','unit':'mm','rounding':'exact rationals, floor lower/ceil upper'},'motion_upper':{'status':'PASS','scope':'constant-velocity analytical translation only','L':str(L),'unit':'mm per mm travel','method':'relative velocity L1 upper bound on Euclidean displacement; both bodies included','rounding':'exact rational'}},'intervals':rows,'cad_application':{'status':'UNKNOWN','guarantees':{'shape_correspondence':'UNKNOWN','distance_absolute_error':'UNKNOWN','motion_upper_bound':'UNKNOWN'},'intervals':[{'lo':r['lo'],'hi':r['hi'],'status':'UNKNOWN'} for r in rows]},'physical_safety':'NOT_TESTED'}
