import sys,importlib.util,json
from unittest.mock import patch
sys.path.insert(0,sys.argv[1]);from history_test import Document,valid,move
spec=importlib.util.spec_from_file_location('under_review',sys.argv[2]);m=importlib.util.module_from_spec(spec);sys.modules['under_review']=m;spec.loader.exec_module(m)
rows=[]
with patch.multiple(m,validate_document=valid,transition=move):
 for direction in ['undo','redo']:
  d=Document();m.apply_state(d,45,0)
  if direction=='redo':m.undo(d)
  before=d.pose;native=getattr(d,direction)
  def substituted():
   native();names=d.future_names if direction=='undo' else d.past_names;names[-1]='unowned replacement with unchanged counts'
  with patch.object(d,direction,substituted):
   try:getattr(m,direction)(d)
   except Exception as error: rejected=str(error)
   else: rejected=None
  rows.append({'direction':direction,'same_fault':'native transaction name replaced after travel; correct pose/count delta','rejected':rejected,'pose_restored':d.pose==before,'session_blocked':m._sessions[id(d)].poisoned})
print(json.dumps(rows,indent=2));assert all(r['rejected'] and r['pose_restored'] and r['session_blocked'] for r in rows),'Same-count native name substitution was accepted'
