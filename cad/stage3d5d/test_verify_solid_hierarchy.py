"""Adversarial synthetic topology-only controls; not a native OCCT run."""
from copy import deepcopy
from collections import defaultdict
import unittest

from verify_solid_hierarchy import check_structure

FACE_WIRES=((0,1),(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),(10,11))
WIRE_EDGES=((0,1,3,2),(4,5,6,7),(8,9,10,0),(1,10,12,11),
            (2,13,14,8),(13,3,11,15),(16,4,18,17),
            (16,19,20,5),(20,21,22,6),(18,7,22,23),
            (9,14,15,12),(17,23,21,19))
EDGE_VERTICES=((0,1),(2,0),(3,1),(2,3),(4,5),(4,6),(6,7),(5,7),
               (8,1),(9,8),(9,0),(10,2),(10,9),(11,3),(11,8),
               (10,11),(4,12),(12,13),(5,13),(12,14),(6,14),
               (14,15),(7,15),(13,15))
ORIENTATIONS=('Reversed','Reversed','Forward','Reversed','Forward',
              'Forward','Reversed','Reversed','Forward','Forward')

def example():
    edges=defaultdict(list)
    for fi,wire_ids in enumerate(FACE_WIRES):
        for wi in wire_ids:
            for ei in WIRE_EDGES[wi]:
                edges[ei].append(fi)
    degrees=[0]*16
    for a,b in EDGE_VERTICES:
        degrees[a]+=1;degrees[b]+=1
    assert len(edges)==24 and all(len(fs)==2 for fs in edges.values())
    assert degrees==[3]*16
    return {'schema':1,'occt':'7.8.1','solid_count':1,
            'direct_shell_count':1,'shell_count':1,
            'direct_shell_face_count':10,
            'all_root_faces_identical_to_shell_faces':True,
            'shell_closed':True,'brepcheck_valid':True,
            'wire_count':12,'edge_count':24,'vertex_count':16,
            'native_shell_membership_exhaustive':'PASS',
            'native_solid_material_set_equality':'UNKNOWN',
            'native_full_q_void_inclusion':'UNKNOWN',
            'native_face_hierarchy':[
                {'face':fi,'orientation':ORIENTATIONS[fi],'direct_wires':list(ws)}
                for fi,ws in enumerate(FACE_WIRES)],
            'wires':[{'wire':wi,'edge_ordinals':list(es),
                      'orientations':['Forward']*4}
                     for wi,es in enumerate(WIRE_EDGES)],
            'edges':[{'edge':ei,'face_pair':edges[ei],
                      'vertex_pair':list(vs)}
                     for ei,vs in enumerate(EDGE_VERTICES)],
            'vertices':[{'vertex':i,'point_mm':[i,0,0],'edge_degree':d}
                        for i,d in enumerate(degrees)]}

class NativeHierarchyContractTests(unittest.TestCase):
    def test_synthetic_genus_one_structure(self):
        r=check_structure(example())
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['unique_edge_uses'],48)
        self.assertEqual(r['native_vertex_edge_graph_components'],2)
        self.assertTrue(r['connected_native_face_graph'])
        self.assertEqual(r['annular_faces_bridge_both_wire_components'],[0,9])
        self.assertEqual(r['represented_surface_euler_characteristic'],0)

    def test_missing_extra_or_misparented_face(self):
        for kind in ('count','duplicate','missing_wire','extra_wire','unknown_orientation'):
            n=example()
            if kind=='count':n['direct_shell_face_count']=9
            if kind=='duplicate':n['native_face_hierarchy'][9]['face']=0
            if kind=='missing_wire':n['native_face_hierarchy'][0]['direct_wires'].pop()
            if kind=='extra_wire':n['native_face_hierarchy'][3]['direct_wires'].append(1)
            if kind=='unknown_orientation':n['native_face_hierarchy'][3]['orientation']='Internal'
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                check_structure(n)

    def test_invalid_edge_ancestry_and_vertex_links(self):
        for kind in ('orphan_edge','wrong_pair','duplicate_wire_edge','null_vertex',
                     'edge_valence','vertex_degree','duplicate_vertex'):
            n=example()
            if kind=='orphan_edge':n['wires'][0]['edge_ordinals'][0]=22
            if kind=='wrong_pair':n['edges'][0]['face_pair']=[0,2]
            if kind=='duplicate_wire_edge':n['wires'][0]['edge_ordinals'][0]=1
            if kind=='null_vertex':n['edges'][0]['vertex_pair']=[0,0]
            if kind=='edge_valence':n['edges'][0]['vertex_pair']=[0,3]
            if kind=='vertex_degree':n['vertices'][0]['edge_degree']=2
            if kind=='duplicate_vertex':n['vertices'][0]['point_mm']=[1,0,0]
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                check_structure(n)

    def test_never_auto_promote_real_solid_equality(self):
        n=example()
        n['native_solid_material_set_equality']='PASS'
        with self.assertRaises(ValueError):
            check_structure(n)
        n=example();n['native_full_q_void_inclusion']='PASS'
        with self.assertRaises(ValueError):
            check_structure(n)

if __name__=='__main__':
    unittest.main()
