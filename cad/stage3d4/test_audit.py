"""Synthetic ZIP auditor controls, NOT native/CI execution evidence."""
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from audit import audit
class Archive(unittest.TestCase):
    def check(self,mode):
        data={};src=b'synthetic control only\n';name='.github/workflows/stage3d4.yml'
        meta={'bytes':len(src),'sha256':hashlib.sha256(src).hexdigest(),'git_blob_sha':hashlib.sha1(b'blob '+str(len(src)).encode()+b'\0'+src).hexdigest()}
        for step in ['portable','archive-controls','native-command','d1-regression','d2-regression','d3-regression','analytical']:
            data[step+'/execution.json']=json.dumps({'sources':{name:meta},'status':'PASS','exit_code':0}).encode()
            data[step+'/source/'+name]=src
            for log in ['stdout.log','stderr.log']:data[step+'/'+log]=b''
        counts={'PASS':0,'FAIL':0,'UNKNOWN':128}
        rows=[{'case':c,'assessment':{'cad_intervals':counts}} for c in ['original','bolt_enlarged','hole_shrunk','placement_shift','orientation_reversed','missing_face_open_shell','unsupported_curved','extra_solid']]
        data['x/native/native.json']=json.dumps({'sources_before':{},'sources_after':{},'rows':rows}).encode()
        data['x/analytical.json']=json.dumps({'analytical_counts':{'PASS':128,'FAIL':0,'UNKNOWN':0},'cad_counts':counts}).encode()
        if mode=='hidden':data.pop('portable/source/'+name)
        if mode=='changed':data['portable/source/'+name]=b'changed'
        if mode=='failed':
            r=json.loads(data['portable/execution.json']);r['exit_code']=1;data['portable/execution.json']=json.dumps(r).encode()
        if mode=='log':data.pop('portable/stderr.log')
        if mode=='missing':data.pop('x/native/native.json')
        if mode=='promoted':
            r=json.loads(data['x/native/native.json']);r['rows'][0]['assessment']['cad_intervals']={'PASS':128,'FAIL':0,'UNKNOWN':0};data['x/native/native.json']=json.dumps(r).encode()
        if mode=='extra':data['extra/execution.json']=data['portable/execution.json'];data['extra/source/'+name]=src
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.zip'
            with zipfile.ZipFile(p,'w') as z:
                for n,b in data.items():z.writestr(n,b)
            return audit(p)
    def test_normal(self):self.assertEqual(self.check('normal')['d4_command_count'],7)
    def test_faults(self):
        for mode in ['hidden','changed','failed','log','missing','promoted','extra']:
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(mode)
if __name__=='__main__':unittest.main()
