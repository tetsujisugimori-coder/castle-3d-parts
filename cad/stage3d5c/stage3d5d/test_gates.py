import copy,hashlib,json,os,tempfile,unittest,zipfile
from pathlib import Path
from stage3d5d.gates import *
from stage3d5d.evidence_contract import audit_archive,compare_reference

def fixture():
    return ({k:{'kind':'topology_observation','status':'UNKNOWN'} for k in REQUIRED},
            {k:{'kind':'occt_flag','upper_m':None,'status':'UNKNOWN'} for k in ERRORS})

class Gates(unittest.TestCase):
    def test_normal_observation_not_native_proof(self):
        p,e=fixture();r=assess(p,e);self.assertEqual(r['input_status'],'PASS');self.assertEqual(r['representative'],'NOT_TESTED')
    def test_true_flags_and_zero_samples_not_proof(self):
        p,e=fixture()
        for r in p.values():r.update(kind='occt_flag',value=True,status='PASS')
        for r in e.values():r.update(kind='sample_maximum',upper_m='0',status='PASS')
        r=assess(p,e,'PASS');self.assertEqual(r['native_bound_sum_m'],None);self.assertEqual(r['actual_intervals_evaluated'],0)
    def test_forged_theorem_and_hash(self):
        p,e=fixture()
        for r in p.values():r.update(kind='claimed_native_theorem',status='PASS',sha256='a'*64)
        self.assertEqual(assess(p,e,'PASS')['representative'],'NOT_TESTED')
    def test_independent_material_void(self):
        p,e=fixture();p['material_outer']={'kind':'represented_identity','status':'PASS'}
        r=assess(p,e);self.assertEqual(r['propositions']['void_inner']['status'],'UNKNOWN')
    def test_all8_unknown_never_zero(self):
        p,e=fixture()
        for k in ERRORS:
            x=copy.deepcopy(e);x[k]['upper_m']=None;self.assertIsNone(assess(p,x)['errors'][k]['upper_m'])
    def test_bad_inventory(self):
        p,e=fixture();p.pop('void_inner');self.assertEqual(assess(p,e)['input_status'],'FAIL')
    def test_negative_boolean_float_bounds(self):
        for v in ['-1',True,0.0,'1/0']:
            p,e=fixture();e['unit']['upper_m']=v;self.assertEqual(assess(p,e)['input_status'],'FAIL')
    def test_nonpositive_not_collision(self):
        r=conditional_clearance('29/64000',dict.fromkeys(ERRORS,'1'))
        self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['native_safety'],'NOT_TESTED')
    def test_sampling_not_continuous(self):
        for n in [23,2300]:self.assertIsNone(sampling_record('0',n)['continuous_upper'])
    def test_static_poses_not_motion(self):
        p,e=fixture();p['all_state_motion']={'kind':'static_pose_comparison','poses':[0,70,140],'status':'PASS'}
        self.assertEqual(assess(p,e)['propositions']['all_state_motion']['status'],'UNKNOWN')
    def test_full_observation_changes(self):
        normal={'stored':None,'trim':[1,2],'orientation':'F','void_extra':False,'closed':True,'transform_count':1}
        for k,v in [('stored',True),('trim',[1]),('orientation','R'),('void_extra',True),('closed',False),('transform_count',2)]:
            c=copy.deepcopy(normal);c[k]=v;self.assertEqual(compare_reference(c,normal)['status'],'FAIL')
        self.assertEqual(compare_reference(normal,normal)['status'],'PASS')
    def test_archive_hidden_and_source_required(self):
        payload={'source/.github/workflows/test.yml':b'fixed','source/runner.py':b'runner'}
        expected={k:{'size':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in payload.items()}
        base=Path(os.environ.get('TMPDIR',str(Path.cwd()/'.work5d')));base.mkdir(parents=True,exist_ok=True)
        t=tempfile.mkdtemp(prefix='archive-controls-',dir=base)
        for n,items,want in [('normal',payload,'PASS'),('hidden-missing',{'source/runner.py':b'runner'},'FAIL'),('source-free',{},'FAIL'),('wrong-bytes',{k:b'x' for k in payload},'FAIL')]:
            p=Path(t)/(n+'.zip')
            with zipfile.ZipFile(p,'w') as z:
                for k,v in items.items():z.writestr(k,v)
            self.assertEqual(audit_archive(p,expected)['status'],want)
