"""Synthetic adapter controls. These are NOT native CAD executions."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from planar_native import assess, proposal, rational
from test_planar_contract import block, guide


def observation(boundary):
    t = {'vertices':[], 'edges':[], 'wires':[], 'faces':[],
         'all_edges_used':True,'all_vertices_used':True}
    points, edges = {}, {}
    for f in boundary['faces']:
        axis, sign = f['axis'], f['normal_sign']; ids=[]
        for w in f['wires']:
            vi=[]
            for p in w['vertices']:
                p=tuple(str(F(x)*1000) for x in p)
                if p not in points:
                    points[p]=len(t['vertices']);t['vertices'].append({'point_mm_ieee':list(p)})
                vi.append(points[p])
            ei=[]
            for i,a in enumerate(vi):
                pair=frozenset((a,vi[(i+1)%len(vi)]))
                if pair not in edges:
                    edges[pair]=len(t['edges']);t['edges'].append({'vertex_ids':sorted(pair),'curve_type':'Line','degenerated_observed':False})
                ei.append(edges[pair])
            ids.append(len(t['wires']));t['wires'].append({'closed_observed':True,'ordered_vertex_ids':vi,'ordered_edge_ids':ei})
        normal=['0']*3;normal[axis]=str(sign)
        pos=['0']*3;pos[axis]=str(F(f['coordinate'])*1000)
        t['faces'].append({'surface_type':'Plane','normal_ieee':normal,'position_mm_ieee':pos,
                           'wire_ids':ids,'wire_roles':[w['role'] for w in f['wires']],
                           'edge_ids':sorted({e for i in ids for e in t['wires'][i]['ordered_edge_ids']}),
                           'vertex_ids':sorted({v for i in ids for v in t['wires'][i]['ordered_vertex_ids']})})
    return t


class NativeProposalControls(unittest.TestCase):
    def test_whole_block(self):
        r=assess(observation(block()),[['0','0','0','4','4','4']])
        self.assertEqual(r['boundary_math']['status'],'PASS')
        self.assertEqual(r['D4_material_comparison']['status'],'PASS')
        self.assertEqual(r['real_material_inclusion'],'UNKNOWN')

    def test_whole_guide(self):
        r=assess(observation(guide()),[['0','0','0','2','4','4']])
        self.assertEqual(r['boundary_math']['atomic_material_cell_count'],8)
        self.assertEqual(r['real_void_inclusion'],'UNKNOWN')

    def test_missing_face(self):
        t=observation(block());t['faces'].pop()
        self.assertEqual(assess(t,[['0','0','0','4','4','4']])['candidate_status'],'FAIL')

    def test_reversed_normal(self):
        t=observation(block());t['faces'][0]['normal_ieee'][0]='1'
        self.assertEqual(assess(t,[['0','0','0','4','4','4']])['boundary_math']['status'],'FAIL')

    def test_missing_edge(self):
        t=observation(block());t['wires'][0]['ordered_edge_ids'].pop()
        self.assertEqual(assess(t,[])['candidate_status'],'FAIL')

    def test_unused_inventory_cannot_be_excluded(self):
        for kind, extra in [('vertices',{'point_mm_ieee':['9','9','9']}),
                            ('edges',{'vertex_ids':[0,1],'curve_type':'Line','degenerated_observed':False}),
                            ('wires',{'closed_observed':True,'ordered_vertex_ids':[0,1,2,3],'ordered_edge_ids':[0,1,2,3]})]:
            t=observation(block());t[kind].append(extra)
            self.assertEqual(assess(t,[])['candidate_status'],'FAIL')

    def test_unsupported_geometry(self):
        t=observation(block());t['edges'][0]['curve_type']='Circle'
        self.assertEqual(assess(t,[])['candidate_status'],'UNKNOWN')

    def test_near_axis_is_not_snapped(self):
        t=observation(block());t['faces'][0]['normal_ieee'][1]='1/1000000000000000'
        self.assertEqual(assess(t,[])['candidate_status'],'UNKNOWN')

    def test_exact_ieee_lift(self):
        self.assertEqual(F(rational(0.1)),F(*0.1.as_integer_ratio()))
        self.assertNotEqual(F(rational(0.1)),F(1,10))
        with self.assertRaises(ValueError):rational(True)
        with self.assertRaises(ValueError):rational(float('nan'))


if __name__=='__main__':unittest.main()
