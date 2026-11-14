"""Same-BBox negative controls: former bounds check vs full triangle check.

This portable mutation test is not a claim of real Blender execution. Separate
native CI applies compare_mesh to actual blend/GLB imports at all six poses.
"""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('mesh_controls',root/'tests/stage3c-mesh-integrity.test.py')
tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
real=tests.module.compare_mesh
def bounds_only(expected_vertices,expected_faces,actual_vertices,actual_faces,tolerance=1e-5):
    assert all(abs(a-b)<tolerance for a,b in zip(tests.box(expected_vertices),tests.box(actual_vertices)))
    return {'triangles':len(actual_faces),'unique_vertices':len(set(map(tuple,actual_vertices)))}

rows=[]
for label,compare,expected in [('RED',bounds_only,False),('GREEN',real,True)]:
    tests.module.compare_mesh=compare
    log=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.MeshIntegrity)
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (out/(label+'.log')).write_text(log.getvalue(),encoding='utf-8')
    rows.append({'phase':label,'tests':result.testsRun,'success':result.wasSuccessful(),
                 'failures':len(result.failures),'errors':len(result.errors)})
    assert result.wasSuccessful()==expected,(label,log.getvalue())
(out/'red-green.json').write_text(json.dumps({'status':'PASS','scope':'portable validator mutation; real Blender is separate','rows':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,indent=2))
