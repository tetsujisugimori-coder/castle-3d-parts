import sys,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'cad/stage2c'))
import native
try:
 d=native.open_ready(ROOT/'cad/stage2c/generated/B0/assembly.FCStd')
 before=native.validate(d);v=d.getObject('FrontView');original=len(v.Source);v.Source=[d.getObject('U01_Post_001')];native.recompute(d)
 try:after=native.validate(d);result={'case':'front-view-only-one-part','original_sources':original,'modified_sources':len(v.Source),'accepted':True,'dimensions':len(after)}
 except Exception as e:result={'case':'front-view-only-one-part','accepted':False,'error':str(e)}
 print('INDEPENDENT_RESULT',json.dumps(result));native.A.closeDocument(d.Name)
except BaseException:
 import traceback;traceback.print_exc();sys.stderr.flush();os._exit(1)
