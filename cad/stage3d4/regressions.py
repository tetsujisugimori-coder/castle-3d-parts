"""Read-only portable regression aggregator; every subcommand exit is retained."""
import json,os,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
commands=[['python3','-B',p] for p in ['cad/stage3d1/test_intervals.py','cad/stage3d2/test_proof.py','cad/stage3d3/test_correspondence.py','cad/stage3d3/test_archive.py','cad/stage3c/check.py','cad/stage3c/check_test.py','cad/stage3c/history_test.py','cad/stage3c/history_parity_test.py','cad/stage3b/check_test.py']]+[['node','--test']]
rows=[]
for i,cmd in enumerate(commands):
    with (out/f'{i}.stdout.log').open('wb') as so,(out/f'{i}.stderr.log').open('wb') as se:
        r=subprocess.run(cmd,stdout=so,stderr=se)
    rows.append({'command':cmd,'exit_code':r.returncode})
(out/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows));sys.exit(int(any(r['exit_code'] for r in rows)))
