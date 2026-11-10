"""Generate into new directory; preserves old originals."""
import sys,os,tempfile,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]).resolve()
assert not out.exists(),'OUTPUT_EXISTS'
env=os.environ|{'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':tempfile.mkdtemp(prefix='gate-cache-')}
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3a/build.py'),str(out)],env=env,check=True)
for pose in ['B0','B1','B2']:
 subprocess.run(['blender','-b','--python-exit-code','1','-t','1','--python',str(root/'blender/stage3a/build.py'),'--',str(out/pose)],check=True)
 subprocess.run(['/usr/bin/python3',str(root/'cad/stage3a/link.py'),str(out/pose),pose],check=True)

subprocess.run(['/usr/bin/python3',str(root/'cad/stage3a/connection.py'),str(out)],env=env,check=True)
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3a/faults.py'),str(out)],env=env,check=True)
