import copy
import json
from pathlib import Path
import unittest
from circular_contract import ROLES,IDENTITY,validate,disk_subset,outward


def control():
    s={'valid':True,'closed':True,'solids':1,'faces':dict(ROLES),
       'box_m':['-1','-1','0','1','1','1'],
       'hole':{'kind':'circular-through-Z','center_xy_m':['0','0'],
               'radius_m':'1/5','wall_role':'bore','openings':['zmin','zmax']},
       'placement':{'rotation':list(IDENTITY),'translation_m':['0','0','0']}}
    return {'kind':'synthetic-box-through-cylinder-v1','unit':'m','source':s,
            'model':copy.deepcopy(s),'face_mapping':{k:k for k in ROLES},
            'errors_m':{k:'0' for k in ['approximation','transform','distance_rounding','representation','pose','motion']},
            'rounding':{'exact_upper_m':'1/3','quantum_m':'1/1000','reported_upper_m':'167/500'}}


def cases():
    rows=[]
    def add(name,reason,mutate):
        d=control();mutate(d);rows.append((name,reason,d))
    add('radius-enlarged','hole-radius-correspondence',lambda d:d['model']['hole'].update(radius_m='21/100'))
    add('radius-shrunk','hole-radius-correspondence',lambda d:d['model']['hole'].update(radius_m='19/100'))
    add('hole-orientation-reversed','face-inventory-or-orientation',lambda d:d['model']['faces'].update(bore='away-from-axis'))
    add('hole-outer-swapped','hole-outer-boundary-correspondence',lambda d:d['model']['hole'].update(wall_role='xmin'))
    add('missing-face','face-inventory-or-orientation',lambda d:d['model']['faces'].pop('zmin'))
    add('translation-shift','placement-mismatch',lambda d:d['model']['placement']['translation_m'].__setitem__(0,'1/1000'))
    add('rotation-mismatch','placement-mismatch',lambda d:d['model']['placement'].update(rotation=['0','-1','0','1','0','0','0','0','1']))
    add('unit-mismatch','unit-mismatch',lambda d:d.update(unit='mm'))
    add('invalid-solid','invalid-or-open-solid',lambda d:d['model'].update(valid=False))
    add('open-solid','invalid-or-open-solid',lambda d:d['model'].update(closed=False))
    add('unsafe-rounding','unsafe-rounding',lambda d:d['rounding'].update(reported_upper_m='333/1000'))
    return rows


class Tests(unittest.TestCase):
    def test_control(self): self.assertEqual(validate(control())['status'],'PASS')

    def test_faults(self):
        for name,reason,data in cases():
            with self.subTest(name=name):
                self.assertEqual(validate(data),{'status':'FAIL','reason':reason})

    def test_primitive_theorem(self):
        self.assertTrue(disk_subset(['0','0'],'1/5',['0','0'],'1/4'))
        self.assertFalse(disk_subset(['0','0'],'1/4',['0','0'],'1/5'))
        self.assertTrue(disk_subset(['3/10','4/10'],'1/2',['0','0'],'1'))
        self.assertFalse(disk_subset(['3/10','4/10'],'1/2',['0','0'],'999/1000'))
        self.assertEqual(str(outward('1/3','1/1000')),'167/500')

    def test_unproved_and_real(self):
        d=control();d['kind']='occt-extracted';self.assertEqual(validate(d)['status'],'UNKNOWN')
        d=control();d['errors_m']['pose']='1/1000';self.assertEqual(validate(d)['status'],'UNKNOWN')
        d=control();d['source']['placement']['rotation']=['0']*9
        self.assertEqual(validate(d)['status'],'FAIL')

    def test_schema_types(self):
        for bad in (True,1.0,'1'):
            d=control();d['source']['solids']=bad
            self.assertEqual(validate(d)['status'],'FAIL')
        d=control();d['source']['placement']['rotation']='100010001'
        self.assertEqual(validate(d)['status'],'FAIL')
        d=control();d['source']['hole']['center_xy_m']='00'
        self.assertEqual(validate(d)['status'],'FAIL')


if __name__=='__main__':
    unittest.main(verbosity=2)
