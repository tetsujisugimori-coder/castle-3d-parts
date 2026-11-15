"""Synthetic archive controls; not historical artifacts or native CAD tests."""
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from audit_zip import audit

class Archive(unittest.TestCase):
    def run_case(self,mode):
        raw=b'fixed workflow bytes\n';path='.github/workflows/stage3d3.yml'
        m={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
           'git_blob_sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'case.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('native/execution.json',json.dumps({'sources':{path:m}}))
                if mode!='missing':z.writestr('native/source/'+path,raw if mode!='changed' else raw+b'x')
                if mode=='extra':z.writestr('native/source/extra.py',b'x')
            return audit(p)
    def test_normal(self):self.assertEqual(self.run_case('normal')['source_instances'],1)
    def test_hidden_missing(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_SET_MISMATCH'):self.run_case('missing')
    def test_changed(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_BYTES_MISMATCH'):self.run_case('changed')
    def test_extra(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_SET_MISMATCH'):self.run_case('extra')
if __name__=='__main__':unittest.main()
