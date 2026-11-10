import sys,tempfile,json,shutil,hashlib
from pathlib import Path
sys.path.append('/usr/lib/freecad/lib')
from PySide2 import QtWidgets
q=QtWidgets.QApplication([])
import FreeCAD as A,FreeCADGui as G
G.showMainWindow()
import TechDrawGui
root=Path.cwd();out=root/'evidence/stage3c/independent';folder=Path(tempfile.mkdtemp(dir=out/'tmp'));source=root/'cad/stage3c/generated/assembly.FCStd';shutil.copyfile(source,folder/'alone.FCStd')
def load(path):
 d=A.newDocument('IndependentPortability');d.TransientDir=tempfile.mkdtemp(dir=folder)+'/';d.FileName=str(path);d.restore();d.recompute();return d
x=load(folder/'alone.FCStd');templates=[o for o in x.Objects if o.TypeId=='TechDraw::DrawSVGTemplate'];assert len(templates)==6
print('TEMPLATES',x.TransientDir,[(o.Template,o.PageResult if 'PageResult' in o.PropertiesList else '') for o in templates],flush=True)
assert all((Path(x.TransientDir)/Path(o.Template).name).exists() for o in templates)
x.LockMechanism.BoltPosition=70;x.recompute();x.saveAs(str(folder/'resaved.FCStd'));A.closeDocument(x.Name)
x=load(folder/'resaved.FCStd');assert x.LockMechanism.BoltPosition.Value==70;assert abs(x.GATE_Bolt.Shape.BoundBox.XMin+330)<1e-6
(out/'portable-review.json').write_text(json.dumps({'result':'PASS','templates':6,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'copy FCStd alone; newDocument + fresh TransientDir + FileName + restore; embedded SVG extraction; change bolt70mm, saveAs, close, restore, assert dimension and geometry','ordinary_openDocument':'FAILED in this runtime, empty TransientDir','manual_GUI':'NOT_TESTED'},indent=2))
A.closeDocument(x.Name)
