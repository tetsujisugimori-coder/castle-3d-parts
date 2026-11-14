"""Fixed rational 1D geometry controls, not FreeCAD evidence."""
import json,sys
from fractions import Fraction as F
from pathlib import Path
from intervals import classify,validate_cover
cases=[]
for center in [F(1,2),F(1,4),F(3,4)]:
 def sample(x):
  signed=abs(x-center)-F(1,100)
  return dict(distance=str(max(F(0),signed)),absolute_error=0,certified=True,penetration_proven=signed<0,contact='PENETRATION' if signed<0 else 'CLEAR')
 old=all(F(sample(x)['distance'])>0 for x in [F(0),F(1)])
 rows=classify(0,1,sample,1,max_depth=6);validate_cover(rows,0,1)
 assert old and any(r['status']=='FAIL' for r in rows)
 cases.append({'fixture':'point swept through open obstacle (center +/- 1/100)','center':str(center),'legacy_endpoints_only':'FALSE_ACCEPT','new':'FAIL','intervals':rows})
for distance,expected in [(F(2),'PASS'),(F(0),'UNKNOWN')]:
 rows=classify(0,1,lambda x:dict(distance=str(distance),absolute_error=0,certified=True,contact='TOUCHING' if distance==0 else 'CLEAR'),0,max_depth=0)
 assert rows[0]['status']==expected
 cases.append({'fixture':'constant stationary gap','distance':str(distance),'new':expected,'intervals':rows})
Path(sys.argv[1]).write_text(json.dumps({'kind':'EXACT_RATIONAL_SYNTHETIC_NOT_CAD','cases':cases},indent=2))
