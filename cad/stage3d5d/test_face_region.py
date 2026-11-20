"""Synthetic region and adversarial evidence controls, no FreeCAD dependency."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
import face_region as f


BOXES=[['-200','-130','990','-180','-116','1050'],
       ['-200','-94','990','-180','0','1050'],
       ['-200','-116','990','-180','-94','999'],
       ['-200','-116','1041','-180','-94','1050']]


def fixture():
    plane=[['-200','-130','990'],['0','0','1'],['0','-1','0']]
    o,u,v=(f.vec(row,3) for row in plane)
    polygons=[[(0,0),(60,0),(60,-130),(0,-130)],
              [(9,-14),(9,-36),(51,-36),(51,-14)]]
    wires=[];stored=[]
    for wi,p in enumerate(polygons):
        uses=[]
        for ui, start in enumerate(p):
            stop=p[(ui+1)%4]
            reverse=(wi==1 and ui==0)
            origin=stop if reverse else start
            delta=tuple((start[i]-stop[i] if reverse else stop[i]-start[i]) for i in (0,1))
            # pcurve points in the underlying edge parameter order; the wire
            # occurrence may be reversed independently of its storage order.
            co=f.surface_point((o,u,v),origin)
            cd=f.plus(f.scaled(delta[0],u),f.scaled(delta[1],v))
            edge=4*wi+ui
            uses.append({'edge':edge,'use':ui,'orientation':'Reversed' if reverse else 'Forward',
                         'pcurve_type':'Line2d','curve_type':'Line',
                         'pcurve':[[str(t) for t in origin],[str(t) for t in delta]],
                         'curve':[[str(t) for t in co],[str(t) for t in cd]],
                         'pcurve_range':['0','1'],'curve_range':['0','1'],
                         'directed_uv':[[str(t) for t in start],[str(t) for t in stop]],
                         'directed_3d':[[str(t) for t in f.surface_point((o,u,v),q)] for q in (start,stop)],
                         'represented_affine_link':'PASS'})
            stored.append({'face':0,'wire':wi,'edge':edge,'formula_use_order':ui,'status':'PASS'})
        signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))
        wires.append({'wire':wi,'role':'outer' if wi==0 else 'inner',
                      'uses':uses,'directed_loop':[[str(x) for x in row] for row in p],
                      'signed_area2_mm2':str(signed)})
    face={'face':0,'orientation':'Reversed','plane':plane,'normal':['-1','0','0'],
          'uv_bounds':['0','60','-130','0'],'wires':wires,'status':'PASS',
          'represented_trim_polygon':'PASS','represented_material_side':{'status':'PASS'}}
    faces=[face, {'face':1,'wires':[{},{}],'plane':[['-180','0','0']]}]
    faces += [{'face':i,'wires':[{}]} for i in range(2,10)]
    stored += [{'face':i,'wire':0,'edge':100+j,'formula_use_order':j,'status':'PASS'}
               for i in range(1,10) for j in range(4)]
    stored += [{'face':1,'wire':1,'edge':200+j,'formula_use_order':j,'status':'PASS'} for j in range(4)]
    assert len(stored)==48
    trim={'source_fcstd_sha256':f.FCSTD_SHA,'source_d2_sha256':f.D2_SHA,
          'parts':{f.GUIDE:{'status':'PASS','edge_use_count':48,'faces':faces}}}
    source={'formula_sha256':f.TRIM_SHA,'expansion_permitted':True,'parts':{f.GUIDE:stored}}
    contract={'obstacle_boxes':deepcopy(BOXES)}
    return trim,source,contract


class FaceRegionProofTests(unittest.TestCase):
    def test_normal_one_face_entire_domain(self):
        result=f.proof(*fixture())
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['represented_ring_area_mm2'],'6876')
        self.assertEqual(result['D2_end_face']['status'],'PASS')
        self.assertEqual(result['native_geometric_face_semantics'],'UNKNOWN')
        self.assertEqual(result['native_void_subset'],'UNKNOWN')

    def test_inner_wire_boundary_is_face_but_hole_center_not(self):
        face=fixture()[0]['parts'][f.GUIDE]['faces'][0]
        _,outer,inner=f.verify_uses(face,fixture()[1]['parts'][f.GUIDE][:8])
        for p,inside in [((9,-20),True),((20,-14),True),((20,-20),False),
                         ((0,0),True),((0,-100),True),((-1,-100),False)]:
            self.assertEqual(f.exact_face_membership(outer,inner,p),inside)

    def test_reject_missing_wire_or_missing_use(self):
        for which in ('wire','use'):
            t,s,c=fixture()
            if which=='wire':t['parts'][f.GUIDE]['faces'][0]['wires'].pop()
            else:t['parts'][f.GUIDE]['faces'][0]['wires'][1]['uses'].pop()
            with self.subTest(which=which),self.assertRaises(ValueError):f.proof(t,s,c)

    def test_reject_reverse_edge_orientation(self):
        t,s,c=fixture()
        t['parts'][f.GUIDE]['faces'][0]['wires'][0]['uses'][0]['orientation']='Reversed'
        with self.assertRaisesRegex(ValueError,'DIRECTED_PCURVE_ENDPOINT_MISMATCH'):
            f.proof(t,s,c)

    def test_reject_stored_witness_fault_or_omission(self):
        for which in ('false','duplicate','missing'):
            t,s,c=fixture()
            arr=s['parts'][f.GUIDE]
            if which=='false':arr[0]['status']='UNKNOWN'
            elif which=='duplicate':arr[1]['edge']=arr[0]['edge'];arr[1]['formula_use_order']=arr[0]['formula_use_order']
            else:arr.pop(0)
            with self.subTest(which=which),self.assertRaises(ValueError):f.proof(t,s,c)

    def test_reject_wrong_parameter_and_location(self):
        for which in ('range','location','slope'):
            t,s,c=fixture()
            face=t['parts'][f.GUIDE]['faces'][0]
            use=face['wires'][0]['uses'][0]
            if which=='range':use['pcurve_range']=['0','2']
            elif which=='location':face['plane'][0][0]='-201'
            else:use['pcurve'][1][0]='2'
            with self.subTest(which=which),self.assertRaises(ValueError):f.proof(t,s,c)

    def test_reject_shifted_or_blocked_d2_hole(self):
        for which in ('shift','block'):
            t,s,c=fixture()
            if which=='shift':c['obstacle_boxes'][0][4]='-115'
            else:c['obstacle_boxes'].append(['-200','-116','999','-180','-94','1041'])
            with self.subTest(which=which),self.assertRaises(ValueError):f.proof(t,s,c)

    def test_reject_wrong_face_side_and_hash_contract(self):
        t,s,c=fixture();t['parts'][f.GUIDE]['faces'][0]['represented_material_side']['status']='FAIL'
        with self.assertRaises(ValueError):f.proof(t,s,c)
        t,s,c=fixture();s['formula_sha256']='bad'
        with self.assertRaises(ValueError):f.proof(t,s,c)

    def test_reject_skewed_plane_or_touching_hole(self):
        t,s,c=fixture()
        t['parts'][f.GUIDE]['faces'][0]['plane'][1][0]='1/2'
        with self.assertRaises(ValueError):f.proof(t,s,c)
        outer=f.rectangle([(0,0),(60,0),(60,-130),(0,-130)])
        touching=f.rectangle([(0,-14),(9,-14),(9,-36),(0,-36)])
        self.assertFalse(f.strict_nested(outer,touching))


if __name__=='__main__':unittest.main()
