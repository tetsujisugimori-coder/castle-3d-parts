"""Rebuild into a NEW destination; never overwrite earlier outputs."""
import sys,json,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
subprocess.run(['node',str(ROOT/'scripts/stage2b.mjs'),'preflight'],cwd=ROOT,check=True)
out=Path(sys.argv[1]).resolve()
if out.exists():raise SystemExit('OUTPUT_EXISTS: use a new destination')
subprocess.run(['/usr/bin/python3',str(ROOT/'cad/stage2b/build.py'),str(out)],check=True)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for rev in json.loads((ROOT/'cad/stage2b/spec.json').read_text())['revisions']:
 d=out/rev['id'];subprocess.run(['blender','-b','-t','1','--python',str(ROOT/'blender/stage2b/build.py'),'--',str(d)],check=True)
 m={'schema_version':1,'revision':rev['id'],'basis':'D','cad_eligibility':'reference_only','spec_sha256':h(ROOT/'cad/stage2b/spec.json'),'source_scripts':{p:h(ROOT/p) for p in ['cad/stage2b/build.py','blender/stage2b/build.py','cad/stage2b/run.py','cad/stage2b/drawing.py']},'outputs':{p.name:h(p) for p in sorted(d.iterdir()) if p.is_file()}}
 (d/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
