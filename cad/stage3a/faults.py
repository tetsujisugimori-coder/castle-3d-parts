"""Real native faults; failures retained as positive detector evidence."""
import sys,json,copy,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import build as b
out=Path(sys.argv[1]);rows=[]
for key,value in [('door_width',-1),('post_height',float('nan')),('axis_radius',.1)]:
 s=copy.deepcopy(b.SPEC);s['parameters'][key]=value
 try:b.check_spec(s)
 except AssertionError:rows.append({'case':key,'input':str(value),'actual':'REJECT'})
 else:raise AssertionError('FAULT_ACCEPTED')
d=b.A.openDocument(str(out/'B0/assembly.FCStd'));b.ready(d);d.removeObject('GATE_Door');b.rec(d)
try:b.audit(d)
except AssertionError:rows.append({'case':'missing-door','actual':'REJECT'})
else:raise AssertionError('FAULT_ACCEPTED')
b.A.closeDocument(d.Name)
# Preserve the actual rejected 40 mm pivot counterexample and repeat same 90-degree pose.
b.SPEC['parameters']['axis_inset']=.04
try:b.build({'id':'B2','angle_degrees':90},Path(tempfile.mkdtemp(prefix='gate-red-'))/'B2')
except AssertionError as e:
 assert 'INTERFERENCE' in str(e),str(e);rows.append({'case':'axis-inset-40mm-B2','actual':'REJECT','reason':str(e),'corrected_input_m':.06,'corrected_evidence':'B2/cad-audit.json'})
else:raise AssertionError('FAULT_ACCEPTED')
(out/'fault-audit.json').write_text(json.dumps({'status':'PASS','cases':rows},indent=2))
