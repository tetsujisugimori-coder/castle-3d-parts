"""Fast negative controls; no CAD software necessary for rejection tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
TRACKED=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT)
spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/cad-regenerate.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
class NegativeControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.directory=Path(self.temp.name)
        self.app=self.directory/'application.json'
        self.app.write_text('{}')
    def tearDown(self):self.temp.cleanup()
    def test_existing_output(self):
        with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):r.run(self.app,self.directory)
    def test_original_tree(self):
        for tree in ('cad/prototype-v1','blender/prototype-v1','site','research'):
            with self.assertRaisesRegex(ValueError,'PROTECTED_OUTPUT'):r.run(self.app,ROOT/tree/'new')
    def test_symlink_application_and_parent(self):
        link=self.directory/'link'
        link.symlink_to(self.app)
        with self.assertRaisesRegex(ValueError,'SYMLINK_FORBIDDEN'):r.run(link,self.directory/'new')
        link.unlink()
        link.symlink_to(self.directory,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'SYMLINK_FORBIDDEN'):r.run(self.app,link/'new')
    def test_missing_parent(self):
        with self.assertRaisesRegex(ValueError,'OUTPUT_PARENT_MISSING'):r.run(self.app,self.directory/'absent'/'new')
    def test_forged_application_engine_rejection(self):
        if not (ROOT/'scripts/research-cad.mjs').exists():self.skipTest('engine not yet installed')
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION_REJECTED'):r.run(self.app,self.directory/'new')
        self.assertFalse((self.directory/'new').exists())
    def test_approval_revoked_before_software(self):
        source=ROOT/'cad/prototype-v1/generated/palisade.FCStd'
        auth={'part_id':'wooden-palisade-late-sengoku-v0','basis':'D','scope':'working_copy_only','source_cad':{'path':str(source.relative_to(ROOT)),'sha256':r.digest(source)},'parameters':dict(height=2.2,spacing=1.2,width=.15,count=5,rails=2)}
        valid=subprocess.CompletedProcess([],0,json.dumps(auth),'')
        revoked=subprocess.CompletedProcess([],1,'','APPROVAL_REVOKED')
        with patch.object(r.subprocess,'check_output',return_value=TRACKED), patch.object(r.subprocess,'run',side_effect=[valid,revoked]) as mocked:
            with self.assertRaisesRegex(ValueError,'AUTHORIZATION_CHANGED'):r.run(self.app,self.directory/'new')
            self.assertEqual(mocked.call_count,2)
        manifest=json.loads((self.directory/'new/manifest.json').read_text())
        self.assertEqual(manifest['status'],'FAIL')
        self.assertTrue(manifest['original_tracked_files_unchanged'])
        self.assertFalse((self.directory/'new/palisade.FCStd').exists())
    def test_wrong_source_hash(self):
        auth={'part_id':'wooden-palisade-late-sengoku-v0','basis':'D','scope':'working_copy_only','source_cad':{'path':'cad/prototype-v1/generated/palisade.FCStd','sha256':'0'*64},'parameters':dict(height=2.2,spacing=1.2,width=.15,count=5,rails=2)}
        with patch.object(r.subprocess,'check_output',return_value=TRACKED), patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(auth),'')):
            with self.assertRaisesRegex(ValueError,'SOURCE_HASH'):r.run(self.app,self.directory/'new')
        self.assertFalse((self.directory/'new').exists())
    def test_bad_parameters(self):
        p=dict(height=2.2,spacing=1.2,width=.15,count=5,rails=2)
        r.parameters(p)
        for k,v in [('height',0),('height',float('inf')),('width',float('nan')),('width',True),('spacing',.1),('count',True),('count',5.5),('count',31),('rails',-1),('rails',7)]:
            with self.subTest(field=k,value=v),self.assertRaises(ValueError):r.parameters({**p,k:v})
        with self.assertRaises(ValueError):r.parameters({**p,'extra':1})
if __name__=='__main__':unittest.main()
