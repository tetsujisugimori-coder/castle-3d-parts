"""Offline analytic fixtures only: box minus open vertical through-cylinder.

No FCStd reader and no admission path for real BRep. Decimal/rational strings
are interpreted exactly in metres. Synthetic validity is by definition, not
an OCCT observation. The interface must not be connected to CAD until a
separate extraction and correspondence proof exists.
"""
from fractions import Fraction
import re

IDENTITY = ['1','0','0','0','1','0','0','0','1']
ROLES = {'xmin':'-X','xmax':'+X','ymin':'-Y','ymax':'+Y',
         'zmin':'-Z','zmax':'+Z','bore':'toward-axis'}


def q(v):
    if not isinstance(v,str) or not re.fullmatch(r'-?\d+(?:\.\d+|/\d+)?',v):
        raise ValueError('exact rational string required')
    return Fraction(v)


def outward(value, quantum):
    x,h=q(value),q(quantum)
    if x<0 or h<=0: raise ValueError('rounding domain')
    z=x/h
    return ((z.numerator+z.denominator-1)//z.denominator)*h


def disk_subset(inner_center, inner_radius, outer_center, outer_radius):
    """Exact test of a closed disk contained in a closed disk, no sqrt."""
    if not isinstance(inner_center,list) or not isinstance(outer_center,list) or len(inner_center)!=2 or len(outer_center)!=2:
        raise ValueError('2D centers')
    a,b=list(map(q,inner_center)),list(map(q,outer_center))
    r,R=q(inner_radius),q(outer_radius)
    if min(r,R)<=0: raise ValueError('positive radius required')
    return R>=r and sum((a[i]-b[i])**2 for i in range(2)) <= (R-r)**2


def rigid(p):
    if set(p)!={'rotation','translation_m'} or not isinstance(p['rotation'],list) or not isinstance(p['translation_m'],list) or len(p['rotation'])!=9 or len(p['translation_m'])!=3:
        raise ValueError('placement schema')
    r=list(map(q,p['rotation']));list(map(q,p['translation_m']))
    if any(sum(r[3*k+i]*r[3*k+j] for k in range(3)) != int(i==j)
           for i in range(3) for j in range(3)):
        raise ValueError('non-rigid rotation')
    det=r[0]*(r[4]*r[8]-r[5]*r[7])-r[1]*(r[3]*r[8]-r[5]*r[6])+r[2]*(r[3]*r[7]-r[4]*r[6])
    if det!=1: raise ValueError('rotation must preserve orientation')


def body(s):
    if s['valid'] is not True or s['closed'] is not True or type(s['solids']) is not int or s['solids']!=1:
        raise ValueError('invalid-or-open-solid')
    if s['faces']!=ROLES: raise ValueError('face-inventory-or-orientation')
    if not isinstance(s['box_m'],list): raise ValueError('box-schema')
    b=list(map(q,s['box_m']))
    if len(b)!=6 or any(b[i]>=b[i+3] for i in range(3)):
        raise ValueError('box-domain')
    hole=s['hole']
    if hole['kind']!='circular-through-Z' or hole['wall_role']!='bore' or hole['openings']!=['zmin','zmax']:
        raise ValueError('hole-outer-boundary-correspondence')
    if not isinstance(hole['center_xy_m'],list): raise ValueError('hole-schema')
    c=list(map(q,hole['center_xy_m']));r=q(hole['radius_m'])
    if len(c)!=2 or r<=0 or any(not (b[i]<c[i]-r and c[i]+r<b[i+3]) for i in range(2)):
        raise ValueError('hole-domain')
    rigid(s['placement'])
    return b,c,r


def validate(d):
    try:
        if d['kind']!='synthetic-box-through-cylinder-v1':
            return {'status':'UNKNOWN','reason':'real-BRep-correspondence-unproved'}
        if d['unit']!='m': raise ValueError('unit-mismatch')
        a,b=d['source'],d['model'];ab,ac,ar=body(a);bb,bc,br=body(b)
        if a['placement']!=b['placement']: raise ValueError('placement-mismatch')
        if d['face_mapping']!={k:k for k in ROLES}: raise ValueError('face-correspondence')
        # This correspondence contract intentionally requires identical bores.
        # A smaller model hole can be conservative, but is not this identity
        # certificate; use a different separately proved contract for that.
        if ar!=br: raise ValueError('hole-radius-correspondence')
        if ac!=bc: raise ValueError('hole-center-correspondence')
        if any(ab[i]<bb[i] or ab[i+3]>bb[i+3] for i in range(3)):
            raise ValueError('stock-containment')
        # Model empty cylinder is contained in source empty cylinder. Hence a
        # source material point cannot lie in the model void. Together with
        # stock containment this proves containment of complete synthetic sets.
        if not disk_subset(b['hole']['center_xy_m'],b['hole']['radius_m'],
                           a['hole']['center_xy_m'],a['hole']['radius_m']):
            return {'status':'UNKNOWN','reason':'void-inclusion-unproved'}
        if set(d['errors_m'])!={'approximation','transform','distance_rounding','representation','pose','motion'}:
            raise ValueError('error-inventory')
        if any(q(v)!=0 for v in d['errors_m'].values()):
            return {'status':'UNKNOWN','reason':'nonzero-error-premises-unproved'}
        rd=d['rounding'];exact=q(rd['exact_upper_m'])
        safe=outward(rd['exact_upper_m'],rd['quantum_m'])
        if q(rd['reported_upper_m'])<safe or exact<0: raise ValueError('unsafe-rounding')
        return {'status':'PASS','scope':'synthetic static set inclusion only',
                'epsilon_m':'0','real_brep':'UNKNOWN','continuous_motion':'NOT_TESTED',
                'safe_rounded_upper_m':str(safe)}
    except (ValueError,KeyError,TypeError,IndexError,AttributeError,ZeroDivisionError) as e:
        return {'status':'FAIL','reason':str(e)}
