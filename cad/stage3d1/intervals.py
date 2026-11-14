"""Conservative interval classifier. No finite samples alone can certify clearance."""
from fractions import Fraction as F

def rational(x):
    if isinstance(x, bool): raise ValueError('BOOLEAN')
    return F(str(x))

def classify(lo, hi, sample, speed, clearance=0, max_depth=6, depth=0):
    lo,hi,speed,clearance=map(rational,(lo,hi,speed,clearance))
    if lo>=hi or speed<0 or clearance<0 or not isinstance(max_depth,int) or not 0<=max_depth<=12:
        raise ValueError('INVALID_CONTRACT')
    mid=(lo+hi)/2
    obs=sample(mid)
    d=rational(obs['distance']); error=obs.get('absolute_error')
    if d<0: raise ValueError('NEGATIVE_DISTANCE')
    certified=obs.get('certified') is True and error is not None
    if error is not None and rational(error)<0: raise ValueError('NEGATIVE_ERROR')
    lower=None if not certified else d-rational(error)-speed*(hi-lo)/2
    status='FAIL' if obs.get('penetration_proven') is True else 'PASS' if lower is not None and lower>clearance else 'UNKNOWN'
    row={'lo':str(lo),'hi':str(hi),'mid':str(mid),'distance':str(d),'motion_bound':str(speed*(hi-lo)/2),'lower_bound':None if lower is None else str(lower),'status':status,'contact':obs.get('contact','UNKNOWN'),'observation':obs}
    if status=='UNKNOWN' and depth<max_depth:
        return classify(lo,mid,sample,speed,clearance,max_depth,depth+1)+classify(mid,hi,sample,speed,clearance,max_depth,depth+1)
    return [row]

def validate_cover(rows,lo,hi):
    cursor=rational(lo)
    for row in rows:
        if rational(row['lo'])!=cursor or rational(row['hi'])<=cursor: raise ValueError('GAP_OVERLAP_ORDER')
        cursor=rational(row['hi'])
    if cursor!=rational(hi): raise ValueError('INCOMPLETE_COVER')
    return True
