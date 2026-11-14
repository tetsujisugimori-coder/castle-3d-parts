"""Regenerate into a NEW destination. Originals and previous evidence are never overwritten."""
import os,sys,tempfile,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]).resolve()
if out.exists():raise SystemExit('Refusing existing output destination')
cache=Path(tempfile.mkdtemp(prefix='gate3c-cache-'));env=os.environ|{'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':str(cache)}
for script in ['build.py','native_test.py','legacy.py','collision.py']:
 subprocess.run(['/usr/bin/python3',str(Path(__file__).parent/script),str(out)],check=True,env=env)
subprocess.run(['blender','-b','-t','1','--python-exit-code','1','--python',str(Path(__file__).parent/'blender.py'),'--',str(out)],check=True,env=env)
subprocess.run(['/usr/bin/python3',str(Path(__file__).parent/'finalize.py'),str(out)],check=True,env=env)
