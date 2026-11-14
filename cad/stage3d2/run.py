"""Emit analytical certificates, binding inputs and semantic controls."""
import json,hashlib,sys
from pathlib import Path
from proof import verify,digest,squared,box,translated,number
ROOT=Path(__file__).resolve().parents[2]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
c=json.loads(Path(__file__).with_name('contract.json').read_text());sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in c['sources']}
EXPECTED_CONTRACT='9e8bb54754f2ce8ff0623bc5a2676788f22ec2154f4da98c66939eaae0b287a2'
r=verify(c,EXPECTED_CONTRACT,sources);(out/'proof.json').write_text(json.dumps(r,indent=2))
from test_proof import fixture
s=fixture([0,0,0,'1/100',1,1],['1/2',0,0,'51/100',1,1],v=(1,0,0));a=box(s['moving_box']);b=box(s['obstacle_boxes'][0]);v=list(map(number,s['moving_velocity']))
old=[str(squared(translated(a,v,number(t)),b)) for t in ('0','1')];new=verify(s,digest(s),s['sources'],0)
assert all(number(x)>0 for x in old) and new['intervals'][0]['status']=='FAIL'
(out/'midpoint-red-green.json').write_text(json.dumps({'input':s,'input_sha256':digest(s),'old_endpoint_squared_distances':old,'old_comparator':'FALSE_ACCEPT (synthetic endpoint-only comparator, not historical CAD product)','new':new},indent=2))
(out/'contract.json').write_text(json.dumps(c,indent=2));print(json.dumps({'analytical_counts':{s:sum(x['status']==s for x in r['intervals']) for s in ('PASS','FAIL','UNKNOWN')},'actual_CAD':'UNKNOWN'}))
