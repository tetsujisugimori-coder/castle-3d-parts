import sys,pathlib,importlib.util,json,copy
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from history_test import Document,valid,move
spec=importlib.util.spec_from_file_location('under_review',sys.argv[2]);module=importlib.util.module_from_spec(spec);sys.modules['under_review']=module;spec.loader.exec_module(module)
rows=[]
with patch.multiple(module,validate_document=valid,transition=move):
 for direction in ['undo','redo']:
  d=Document();values=d.past if direction=='undo' else d.future;names=d.past_names if direction=='undo' else d.future_names;values.append((45,.14));names.append('external invalid target');before=copy.deepcopy(d.__dict__)
  try:getattr(module,direction)(d)
  except ValueError as error: rejected=str(error)
  else:rejected=None
  rows.append({'operation':direction,'same_injected_target':[45,.14],'rejected':rejected,'before_pose':list(before['pose']),'after_pose':list(d.pose),'state_and_native_stacks_unchanged':d.__dict__==before})
print(json.dumps(rows,indent=2))
assert all(r['rejected'] and r['state_and_native_stacks_unchanged'] for r in rows),'Illegal Undo/Redo target mutated original state/history'
