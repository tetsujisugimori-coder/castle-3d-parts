"""Synthetic ZIP auditor controls, NOT native/CI execution evidence."""
import copy,hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import audit as auditor
from bridge import PARTS,assess,sources,ROOT
from run import build_report
from test_bridge import fixture

def package():
    data={};name='.github/workflows/stage3d4.yml';src=(ROOT/name).read_bytes()
    meta={'bytes':len(src),'sha256':hashlib.sha256(src).hexdigest(),'git_blob_sha':hashlib.sha1(b'blob '+str(len(src)).encode()+b'\0'+src).hexdigest()}
    for step in ['portable','archive-controls','native-command','d1-regression','d2-regression','d3-regression','analytical']:
        data[step+'/execution.json']=json.dumps({'sources':{name:meta},'status':'PASS','exit_code':0}).encode()
        data[step+'/source/'+name]=src
        for log in ['stdout.log','stderr.log']:data[step+'/'+log]=b''
    original=fixture()
    for name,p in original['parts'].items():
        raw=('synthetic BRep placeholder '+name).encode();data['x/native/'+name+'.brep']=raw;p['brep_sha256']=hashlib.sha256(raw).hexdigest()
        p.update(solid_orientations=['Forward'],shell_orientations=['Forward'],bounds_observed=[0,0,0,1,1,1],tolerance_observed=1e-7)
        for f in p['faces']:
            f.update(normal_observed=[1,0,0],area_observed=1)
            for w in f['wires']:
                w['orientation']='Forward'
                for e in w['edges']:e.update(length_observed=1,tolerance_observed=1e-7)
    rows=[{'case':'original','input':original,'assessment':assess(original)}]
    for case in ['bolt_enlarged','hole_shrunk','placement_shift','orientation_reversed','missing_face_open_shell','unsupported_curved','extra_solid']:
        x=copy.deepcopy(original);raw=('synthetic mutation '+case).encode();data['x/native/'+case+'.brep']=raw;x['parts'][PARTS[0]]['brep_sha256']=hashlib.sha256(raw).hexdigest()
        for part in PARTS:data['x/native/'+case+'/'+part+'.brep']=raw if part==PARTS[0] else data['x/native/'+part+'.brep']
        rows.append({'case':case,'input':x,'assessment':assess(x),'BRep_changed':True,'fixed_observation_match':'REJECTED_BREP_CHANGED'})
    data['x/native/native.json']=json.dumps({'sources_before':sources(),'sources_after':sources(),'rows':rows}).encode()
    data['x/analytical.json']=json.dumps(build_report()).encode()
    return data

class Archive(unittest.TestCase):
    def check(self,mode):
        data=package();name='.github/workflows/stage3d4.yml'
        if mode=='hidden':data.pop('portable/source/'+name)
        if mode=='changed':data['portable/source/'+name]=b'changed'
        if mode=='failed':
            r=json.loads(data['portable/execution.json']);r['exit_code']=1;data['portable/execution.json']=json.dumps(r).encode()
        if mode=='log':data.pop('portable/stderr.log')
        if mode=='missing':data.pop('x/native/native.json')
        if mode in ['promoted','faces','source']:
            r=json.loads(data['x/native/native.json'])
            if mode=='promoted':r['rows'][0]['assessment']['cad_intervals']={'PASS':128,'FAIL':0,'UNKNOWN':0}
            if mode=='faces':r['rows'][0]['input']['parts'][PARTS[0]]['faces']=[]
            if mode=='source':r['sources_before']={}
            data['x/native/native.json']=json.dumps(r).encode()
        if mode in ['intervals','boundary']:
            r=json.loads(data['x/analytical.json'])
            if mode=='intervals':r['analytical']['intervals']=[]
            else:r['boundaries']['bolt']['faces']=[]
            data['x/analytical.json']=json.dumps(r).encode()
        if mode=='brep':data['x/native/'+PARTS[0]+'.brep']=b'wrong'
        if mode=='extra':data['extra/execution.json']=data['portable/execution.json'];data['extra/source/'+name]=data['portable/source/'+name]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.zip'
            with zipfile.ZipFile(p,'w') as z:
                for n,b in data.items():z.writestr(n,b)
            # This test scopes source inventory to one file; production audit does not.
            with patch.object(auditor,'source_paths',return_value=[ROOT/name]):return auditor.audit(p)
    def test_normal(self):self.assertEqual(self.check('normal')['d4_command_count'],7)
    def test_faults(self):
        for mode in ['hidden','changed','failed','log','missing','promoted','extra','faces','source','intervals','boundary','brep']:
            with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):self.check(mode)
    def test_full_source_set_required(self):
        data=package()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.zip'
            with zipfile.ZipFile(p,'w') as z:
                for n,b in data.items():z.writestr(n,b)
            with self.assertRaisesRegex(ValueError,'FIXED_SOURCE_SET_MISMATCH'):auditor.audit(p)
if __name__=='__main__':unittest.main()
