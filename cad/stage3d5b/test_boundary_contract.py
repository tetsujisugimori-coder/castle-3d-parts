import copy
import hashlib
import unittest
from test_circular_contract import control as circular_control
from circular_contract import validate as old_validate
from boundary_contract import validate_observation,round_grid,void_rectangle,aggregate_intervals


def fixture():
    h=lambda s:hashlib.sha256(s.encode()).hexdigest()
    record={'object_id':'GATE_BoltGuide_Left','shape_sha256':h('synthetic primitive definition'),
            'fcstd_sha256':h('no actual FCStd: synthetic fixture'),
            'axis_local':['0','0','1'],'raw_unit':'mm','geometry_unit':'m','scale_to_m':'1/1000',
            'placement_applications':1,'transform_order':['scale','rotate','translate'],
            'primitive_frame':'local','brep_tolerance_m':'0','tolerance_budget_m':'0'}
    d={'schema':'synthetic-observation-v1','manifest_sha256':h('synthetic manifest'),
       'evidence':{k:'synthetic-definition:'+k for k in ['input','topology','geometry','placement','tolerance']},
       'records':{'source':copy.deepcopy(record),'model':copy.deepcopy(record)},'geometry':circular_control()}
    a={'manifest_sha256':d['manifest_sha256'],
       **{k:{n:v for n,v in record.items() if n in ['object_id','shape_sha256','fcstd_sha256']} for k in ['source','model']}}
    return d,a


def fault_cases():
    cases=[]
    def add(name,reason,f):
        d,a=fixture();f(d);cases.append((name,reason,d,a))
    add('E1-radius-enlarged','hole-radius-correspondence',lambda d:d['geometry']['model']['hole'].update(radius_m='21/100'))
    add('E2-radius-shrunk','hole-radius-correspondence',lambda d:d['geometry']['model']['hole'].update(radius_m='19/100'))
    add('E3-center-shift','hole-center-correspondence',lambda d:d['geometry']['model']['hole'].update(center_xy_m=['1/100','0']))
    add('E4-axis-reversed','directed-hole-frame',lambda d:d['records']['model'].update(axis_local=['0','0','-1']))
    add('E5-normal-reversed','face-inventory-or-orientation',lambda d:d['geometry']['model']['faces'].update(bore='away-from-axis'))
    add('E6-face-missing','face-inventory-or-orientation',lambda d:d['geometry']['model']['faces'].pop('xmin'))
    add('E7-open-solid','invalid-or-open-solid',lambda d:d['geometry']['model'].update(closed=False))
    add('E8-placement-missing',"'placement'",lambda d:d['geometry']['model'].pop('placement'))
    add('E9-double-placement','placement-application-count',lambda d:d['records']['model'].update(placement_applications=2))
    add('E10-unit-conversion','unit-conversion',lambda d:d['records']['model'].update(scale_to_m='1'))
    add('E11-rounding-direction','unsafe-rounding',lambda d:d['geometry']['rounding'].update(reported_upper_m='333/1000'))
    add('E12-tolerance-excess','tolerance-exceeds-declared-budget',lambda d:d['records']['model'].update(brep_tolerance_m='1/1000'))
    add('E13-shape-swap','shape-anchor-mismatch',lambda d:d['records']['model'].update(object_id='GATE_Bolt'))
    add('E14-evidence-missing','mandatory-evidence',lambda d:d['evidence'].pop('geometry'))
    add('E14-manifest-missing',"'manifest_sha256'",lambda d:d.pop('manifest_sha256'))
    return cases


class ContractTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(validate_observation(*fixture())['status'],'PASS')

    def test_faults(self):
        for name,reason,d,a in fault_cases():
            with self.subTest(name=name): self.assertEqual(validate_observation(d,a),{'status':'FAIL','reason':reason})

    def test_old_extension_gap(self):
        # This new obligation was outside D5A's declared interface, not a
        # retroactive claim that D5A certified these observation fields.
        d,a=fixture();d['records']['model']['placement_applications']=2
        self.assertEqual(old_validate(d['geometry'])['status'],'PASS')
        self.assertEqual(validate_observation(d,a)['status'],'FAIL')

    def test_real_and_tolerance_gate(self):
        d,a=fixture();d['schema']='brep-observation-v1'
        self.assertEqual(validate_observation(d,a)['status'],'UNKNOWN')
        d,a=fixture()
        for s in d['records'].values(): s.update(brep_tolerance_m='1/1000',tolerance_budget_m='1/1000')
        self.assertEqual(validate_observation(d,a)['status'],'UNKNOWN')
        d,a=fixture();d['records']['model']['placement_applications']=True
        self.assertEqual(validate_observation(d,a)['status'],'FAIL')

    def test_real_missing_and_open(self):
        d,a=fixture();d['schema']='brep-observation-v1';d.pop('geometry')
        self.assertEqual(validate_observation(d,a),{'status':'FAIL','reason':"'geometry'"})
        d,a=fixture();d['schema']='brep-observation-v1';d['geometry']['source']['closed']=False
        self.assertEqual(validate_observation(d,a),{'status':'FAIL','reason':'invalid-or-open-solid'})
        d,a=fixture();d['schema']='brep-observation-v1';d['geometry']['source']['placement']['rotation']=['0']*9
        self.assertEqual(validate_observation(d,a),{'status':'FAIL','reason':'non-rigid rotation'})

    def test_rounding(self):
        self.assertEqual(str(round_grid('-1/3','1/1000','lower')),'-167/500')
        self.assertEqual(str(round_grid('-1/3','1/1000','upper')),'-333/1000')
        self.assertEqual(str(round_grid('1/3','1/1000','lower')),'333/1000')

    def test_inner_void_boundary(self):
        f=lambda x,y:void_rectangle('1','0','0','0',x,y,'1/1000')
        self.assertEqual(f('3/5','4/5')['status'],'FAIL')
        self.assertEqual(f('599/1000','4/5')['status'],'PASS')
        self.assertEqual(f('601/1000','4/5')['status'],'FAIL')
        self.assertEqual(void_rectangle('1','1','0','0','1/10','1/10','1/1000')['status'],'UNKNOWN')
        self.assertEqual(void_rectangle('1','1/10','1/10','1/10','2/5','2/5','1/1000')['inner_radius_m'],'7/10')

    def test_interval_snapshots(self):
        old=aggregate_intervals(['UNKNOWN']*128);new=aggregate_intervals(['NOT_TESTED']*128)
        self.assertEqual(old['UNKNOWN'],128);self.assertEqual(new['NOT_TESTED'],128)
        for bad in [['PASS']*127,['PASS']*256,['BLOCKED']*128]:
            with self.assertRaises(ValueError):aggregate_intervals(bad)


if __name__=='__main__': unittest.main(verbosity=2)
