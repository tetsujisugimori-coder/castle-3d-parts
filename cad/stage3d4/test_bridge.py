import copy,unittest
from bridge import PARTS,assess,sources

def fixture():
    edge={'curve':'Line','orientation':'Forward','vertices':[[0,0,0],[1,0,0]]}
    face={'surface':'Plane','orientation':'Forward','wires':[{'closed':True,'edges':[edge]}]}
    part={'brep_sha256':'synthetic only','placement':'synthetic','valid':True,'closed':True,'solids':1,'shells':1,'faces':[face]}
    return {'sources':sources(),'unit':'mm','frame':'FreeCAD world','door_degrees':0,'travel_mm':[0,140], 'parts':{n:copy.deepcopy(part) for n in PARTS}}
class Bridge(unittest.TestCase):
    def test_incomplete_evidence_never_proves_cad(self):
        self.assertEqual(assess(fixture())['cad_intervals'],{'PASS':0,'FAIL':0,'UNKNOWN':128})
    def test_forged_claims_never_prove_cad(self):
        x=fixture();x.update(proof='PASS',error=0,material_outer_containment=True,hole_inner_containment=True)
        self.assertTrue(all(v['status']=='UNKNOWN' for k,v in assess(x)['guarantees'].items() if k!='input_identity'))
    def test_reject_controls(self):
        mutations=[lambda x:x.update(unit='m'),lambda x:x.update(sources={}),lambda x:x.update(parts={}),
            lambda x:x['parts'][PARTS[0]].update(faces=[]),lambda x:x['parts'][PARTS[0]].update(solids=2),
            lambda x:x['parts'][PARTS[0]].update(closed=False),lambda x:x['parts'][PARTS[0]]['faces'][0].update(surface='Cylinder'),
            lambda x:x['parts'][PARTS[0]]['faces'][0].update(wires=[]),lambda x:x['parts'][PARTS[0]]['faces'][0].update(orientation='Internal'),
            lambda x:x['parts'][PARTS[0]]['faces'][0]['wires'][0].update(closed=False),lambda x:x.update(travel_mm=[0,141])]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                x=fixture();mutate(x);self.assertEqual(assess(x)['eligibility'],'REJECTED')
                self.assertEqual(assess(x)['cad_intervals']['PASS'],0)
if __name__=='__main__':unittest.main()
