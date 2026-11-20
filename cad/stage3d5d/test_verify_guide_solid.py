"""Synthetic invalid-orientation, missing boundary, and native sample faults."""
import copy
import unittest
from verify_guide_solid import guide_census, validate_classification, assess, expected_samples
from test_one_slice import fixture


def sample_fixture():
    rows=expected_samples(fixture())
    native={'schema':1,'occt':'7.8.1','solid_count':1,'valid_observed':True,
            'sample_count':len(rows),'native_material_outer':'UNKNOWN','native_void_inner':'UNKNOWN',
            'samples':[{'id':r['id'],'point_mm':[int(x) for x in r['point_mm_exact']],
                        'state':r['expected']} for r in rows]}
    return rows,native


def boundary_fixture():
    faces=[];stored=[];edge=0
    for fi in range(10):
        wires=[]
        for wi in range(2 if fi in (0,1) else 1):
            role='inner' if wi==1 else 'outer'
            uses=[]
            for ui in range(4):
                uses.append({'edge':edge,'use':ui})
                stored.append({'face':fi,'wire':wi,'edge':edge,'formula_use_order':ui,'status':'PASS'})
                edge+=1
            wires.append({'role':role,'wire':wi,'uses':uses})
        faces.append({'status':'PASS','face':fi,'represented_material_side':{'status':'PASS'},
                      'wires':wires})
    return {'status':'PASS','edge_use_count':48,'faces':faces},stored


class GuideSolidContractTests(unittest.TestCase):
    def test_expected_region_names_are_separate(self):
        rows,native=sample_fixture()
        self.assertEqual(len(rows),16)
        self.assertTrue(any(r['id'].startswith('through_end_') and r['expected']=='OUT' for r in rows))
        self.assertTrue(any(r['role']=='closed_material' and r['expected']=='IN' for r in rows))
        self.assertEqual(validate_classification(rows,native)['status'],'PASS')

    def test_mismatched_point_and_material_side_are_rejected(self):
        rows,native=sample_fixture()
        for field,val in [('state','IN'),('point_mm',[-189,-105,1020])]:
            changed=copy.deepcopy(native)
            item=next(s for s in changed['samples'] if s['id']=='void_center')
            item[field]=val
            self.assertEqual(validate_classification(rows,changed)['status'],'FAIL')

    def test_duplicate_missing_and_invalid_native_results(self):
        rows,native=sample_fixture()
        for defect in ('missing','duplicate','invalid','closed-hole'):
            d=copy.deepcopy(native)
            if defect=='missing':d['samples'].pop()
            elif defect=='duplicate':d['samples'].append(d['samples'][0])
            elif defect=='invalid':d['valid_observed']=False
            else:next(x for x in d['samples'] if x['id']=='end_plane_positive_x')['state']='ON'
            self.assertEqual(validate_classification(rows,d)['status'],'FAIL')

    def test_boundary_use_and_hole_census(self):
        t,stored=boundary_fixture()
        self.assertEqual(guide_census(t,stored)['status'],'PASS')
        for defect in ('no-inner','missing-use','missing-stored','false-store','wrong-order','face-side'):
            a,b=copy.deepcopy(t),copy.deepcopy(stored)
            if defect=='no-inner':a['faces'][0]['wires'][1]['role']='outer'
            elif defect=='missing-use':a['faces'][0]['wires'][0]['uses'].pop()
            elif defect=='missing-stored':b.pop()
            elif defect=='false-store':b[0]['status']='FAIL'
            elif defect=='wrong-order':b[0]['formula_use_order']=1
            else:a['faces'][0]['represented_material_side']['status']='FAIL'
            self.assertEqual(guide_census(a,b)['status'],'FAIL')

    def test_finite_observation_never_promotes_real_inclusion(self):
        rows,native=sample_fixture()
        a,b=boundary_fixture()
        census=guide_census(a,b)
        samples=validate_classification(rows,native)
        candidate={'status':'PASS','represented_set_equality':'PASS',
                   'candidate_void_to_query':{'status':'PASS'}}
        result=assess(census,samples,candidate,b)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['native_material_outer'],'UNKNOWN')
        self.assertEqual(result['native_void_inner'],'UNKNOWN')
        self.assertEqual(result['native_representative_interval'],'NOT_TESTED')
        broken=copy.deepcopy(candidate)
        broken['candidate_void_to_query']['status']='FAIL'
        self.assertEqual(assess(census,samples,broken,b)['status'],'FAIL')


if __name__=='__main__':
    unittest.main()
