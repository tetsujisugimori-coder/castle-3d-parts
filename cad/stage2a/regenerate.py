"""FreeCAD worker: a copied FCStd is the only editable CAD input."""
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prototype', ROOT / 'cad/prototype-v1/build.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
out = Path(sys.argv[1])
p = json.loads((out / 'validated-application.json').read_text())['parameters']
m.validate(p)
d = m.App.openDocument(str(out / 'input.FCStd'))
# Omit baseline-only drawing annotations from the changed working copy.
for name in ('FrontView', 'Drawing', 'Template'):
    if d.getObject(name): d.removeObject(name)
d.recompute()
for name, key in [('Height','height'), ('Spacing','spacing'), ('Width','width')]:
    setattr(d.Parameters, name, p[key] * 1000)
for name, key in [('Count','count'), ('Rails','rails')]:
    setattr(d.Parameters, name, p[key])
d, objects = m.regenerate(d)
r = {'software': m.App.Version(), 'mode': 'headless module; GUI NOT_TESTED', 'techdraw':'OMITTED: baseline drawing is not valid for changed dimensions', 'generated': m.audit(d, objects, p)}
d.saveAs(str(out / 'palisade.FCStd'))
m.App.closeDocument(d.Name)
d = m.App.openDocument(str(out / 'palisade.FCStd'))
objects = [o for o in d.Objects if o.Name.startswith(('Post_', 'Rail_'))]
r['fcstd_reopened'] = m.audit(d, objects, p)
m.Part.export(objects, str(out / 'palisade.step'))
s = m.Part.Shape()
s.read(str(out / 'palisade.step'))
assert s.isValid() and len(s.Solids) == p['count'] + p['rails']
assert abs(s.Volume-r['generated']['volume_mm3']) < .01
bb = s.BoundBox
r['step_reopened'] = {'valid':s.isValid(), 'solids':len(s.Solids), 'dimensions_m':[bb.XLength/1000,bb.YLength/1000,bb.ZLength/1000], 'volume_mm3':s.Volume}
assert all(abs(a-b)<1e-8 for a,b in zip(r['step_reopened']['dimensions_m'],r['generated']['dimensions_m']))
# Match each reopened STEP solid to its CAD component by bounds, not by export order.
remaining = list(objects)
meshes = []
for solid in s.Solids:
    bounds = lambda shape: [getattr(shape.BoundBox, k) for k in ('XMin','YMin','ZMin','XMax','YMax','ZMax')]
    candidates = [o for o in remaining if all(abs(a-b)<1e-6 for a,b in zip(bounds(o.Shape),bounds(solid)))]
    assert len(candidates) == 1, 'STEP_COMPONENT_MATCH'
    obj = candidates[0]
    remaining.remove(obj)
    vertices, faces = solid.tessellate(.1)
    meshes.append({'name':obj.Name, 'vertices_m':[[v.x/1000,v.y/1000,v.z/1000] for v in vertices], 'faces':[list(f) for f in faces]})
assert not remaining
meshes.sort(key=lambda item:item['name'])
(out / 'mesh-transfer.json').write_text(json.dumps({'unit':'m','up':'Z','derived_from':'reopened palisade.step','objects':meshes},indent=2)+'\n')
m.App.closeDocument(d.Name)
(out / 'freecad-audit.json').write_text(json.dumps(r,indent=2)+'\n')
