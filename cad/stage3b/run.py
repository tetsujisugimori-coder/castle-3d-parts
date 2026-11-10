"""Regenerate native outputs to a new destination; never overwrite original evidence."""
import os,sys,tempfile,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]).resolve();assert not out.exists()
cache=tempfile.mkdtemp(prefix='gate3b-cache-');env=os.environ|{'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':cache}
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3b/build.py'),str(out)],env=env,check=True)
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3b/collision.py'),str(out)],check=True,env=env)
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3b/drawings.py'),str(out)],check=True,env=env)
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3b/native_test.py'),str(out)],check=True,env=env)
subprocess.run(['/usr/bin/python3',str(root/'cad/stage3b/limits.py'),str(out)],check=True,env=env)
subprocess.run(['blender','-b','-t','1','--python-exit-code','1','--python',str(root/'cad/stage3b/blender.py'),'--',str(out)],check=True,env=env)
