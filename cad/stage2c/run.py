"""Regenerate into a new directory. No old CAD/evidence/research files are written."""
import sys,os,json,hashlib,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main(dest):
 out=Path(dest).resolve()
 if out.exists():raise SystemExit('OUTPUT_EXISTS')
 subprocess.run(['node',str(ROOT/'scripts/stage2b.mjs'),'preflight'],cwd=ROOT,check=True)
 subprocess.run(['/usr/bin/python3',str(ROOT/'cad/stage2b/build.py'),str(out)],check=True)
 for r in ['B0','B1','B2']:
  d=out/r;env=os.environ|{'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':tempfile.mkdtemp(prefix='s2c-qt-cache-')}
  subprocess.run(['/usr/bin/python3',str(ROOT/'cad/stage2c/native.py'),str(d),r],env=env,check=True)
  subprocess.run(['blender','-b','-t','1','--python',str(ROOT/'blender/stage2b/build.py'),'--',str(d)],check=True)
  subprocess.run(['/usr/bin/python3',str(ROOT/'cad/stage2c/link.py'),str(d),r],check=True)
 print('PASS: B0/B1/B2 real CAD, native dimensions, STEP, Blender, GLB, SVG')
if __name__=='__main__':main(sys.argv[1])
