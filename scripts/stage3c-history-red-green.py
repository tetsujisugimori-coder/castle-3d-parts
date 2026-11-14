"""Replay identical negative controls against preserved before/final code."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=False)
rows=[]
def run(name, argv, expected):
    p=subprocess.run(argv,cwd=root,capture_output=True)
    (out/(name+'.stdout.log')).write_bytes(p.stdout)
    (out/(name+'.stderr.log')).write_bytes(p.stderr)
    rows.append({'name':name,'exit_code':p.returncode,'expected_exit':expected,
                 'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),
                 'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()})
    assert p.returncode==expected,(name,p.returncode,p.stderr.decode(errors='replace'))

cad=str(root/'cad/stage3c')
for label, counterexample, before in [
    ('illegal-target','stage3c-history-target-counterexample.py','stage3c-history-draft.py'),
    ('native-names','stage3c-history-names-counterexample.py','stage3c-history-before-native-names.py')]:
    for phase,source,expected in [('RED',root/'tests/fixtures'/before,1),('GREEN',root/'cad/stage3c/history.py',0)]:
        run(label+'-'+phase,[sys.executable,'-B',str(root/'scripts'/counterexample),cad,str(source)],expected)

# The submitted starting HEAD had no Web history module at all. Preserve the
# real acceptance test and execute it against that missing-module boundary.
missing=out/'before-web';(missing/'tests').mkdir(parents=True)
shutil.copyfile(root/'tests/stage3c-history.test.mjs',missing/'tests/stage3c-history.test.mjs')
run('web-history-RED',['node','--test',str(missing/'tests/stage3c-history.test.mjs')],1)
assert b'ERR_MODULE_NOT_FOUND' in (out/'web-history-RED.stderr.log').read_bytes()+(out/'web-history-RED.stdout.log').read_bytes()
run('web-history-GREEN',['node','--test','tests/stage3c-history.test.mjs'],0)
summary={'status':'PASS','rows':rows,'red_target_scope':'CAD before-code fixtures are unsubmitted drafts; starting HEAD has no history API',
         'native_execution':'NOT_TESTED; transaction double only'}
(out/'red-green.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
