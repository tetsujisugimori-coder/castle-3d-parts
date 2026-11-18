"""Synthetic exact boundary tests; none are a native CAD inclusion proof."""
from copy import deepcopy
from fractions import Fraction
import unittest

from planar_contract import classify_point, compare_cells, compare_material, certify_void_box, verify_boundary


def rectangle(fid, axis, coordinate, sign, u0, u1, v0, v1, role='outer'):
    uv=((axis+1)%3,(axis+2)%3)
    points=[]
    for u,v in ((u0,v0),(u1,v0),(u1,v1),(u0,v1)):
        p=[None]*3;p[axis]=coordinate;p[uv[0]]=u;p[uv[1]]=v
        points.append(list(map(str,p)))
    if sign*(1 if role=='outer' else -1)<0:points.reverse()
    return {'id':fid,'surface':'Plane','axis':axis,'coordinate':str(coordinate),'normal_sign':sign,
            'wires':[{'id':fid+'-'+role,'role':role,'curve_type':'Line','vertices':points}]}


def block():
    return {'schema':'rectilinear-boundary-v1','unit':'m','faces':[
        rectangle(str(a)+'-'+str(s),a,0 if s<0 else 4,s,0,4,0,4)
        for a in range(3) for s in (-1,1)]}


def guide(hole_min=1,hole_max=3):
    faces=[]
    for x,s in ((0,-1),(2,1)):
        f=rectangle('x'+str(x),0,x,s,0,4,0,4)
        f['wires']+=rectangle('x'+str(x),0,x,s,hole_min,hole_max,hole_min,hole_max,'inner')['wires']
        faces.append(f)
    # cyclic projection y=> (z,x), z=> (x,y)
    for y,s in ((0,-1),(4,1)):
        faces.append(rectangle('y'+str(y),1,y,s,0,4,0,2))
    for z,s in ((0,-1),(4,1)):
        faces.append(rectangle('z'+str(z),2,z,s,0,2,0,4))
    for y,s in ((hole_min,1),(hole_max,-1)):
        faces.append(rectangle('inner-y'+str(y),1,y,s,hole_min,hole_max,0,2))
    for z,s in ((hole_min,1),(hole_max,-1)):
        faces.append(rectangle('inner-z'+str(z),2,z,s,0,2,hole_min,hole_max))
    return {'schema':'rectilinear-boundary-v1','unit':'m','faces':faces}


class PlanarContractTests(unittest.TestCase):
    def test_complete_block(self):
        result=verify_boundary(block())
        self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['exact_material_cells_m'],[['0','0','0','4','4','4']])
        self.assertEqual(result['real_brep'],'UNKNOWN')

    def test_complete_rectangular_through_opening(self):
        result=verify_boundary(guide())
        self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['face_count'],10)
        self.assertEqual(result['atomic_material_cell_count'],8)
        # Passes beyond both x end planes: exact empty corridor, not just bbox.
        self.assertEqual(certify_void_box(guide(),['-1','3/2','3/2','3','5/2','5/2'])['status'],'PASS')

    def test_missing_face_rejected(self):
        d=guide();d['faces'].pop()
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_missing_inner_trim_rejected(self):
        d=guide();d['faces'][0]['wires'].pop()
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_reverse_normal_rejected(self):
        d=guide();d['faces'][0]['normal_sign']*= -1
        self.assertEqual(verify_boundary(d)['reason'],'wire-role-or-orientation')

    def test_reverse_normal_and_loop_rejected(self):
        d=guide();f=d['faces'][0];f['normal_sign']*= -1
        for w in f['wires']:w['vertices'].reverse()
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_inner_material_role_inversion_rejected(self):
        d=guide();d['faces'][0]['wires'][1]['role']='outer'
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_globally_inverted_material_rejected(self):
        d=guide()
        for f in d['faces']:
            f['normal_sign']*= -1
            for w in f['wires']:w['vertices'].reverse()
        self.assertEqual(verify_boundary(d)['reason'],'negative-or-multiple-material-winding')

    def test_opening_dimension_inconsistent_rejected(self):
        d=guide();d['faces'][0]['wires'][1]['vertices'][0][1]='1/2'
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_consistent_opening_enlargement_not_covering_material(self):
        larger=guide(Fraction(1,2),Fraction(7,2))
        self.assertEqual(verify_boundary(larger)['status'],'PASS')
        self.assertEqual(compare_material(guide(),larger)['reason'],'mathematical-material-not-covered')

    def test_smaller_void_is_conservative_material_only(self):
        smaller=guide(Fraction(3,2),Fraction(5,2))
        self.assertEqual(compare_material(guide(),smaller)['status'],'PASS')
        self.assertEqual(certify_void_box(smaller,['1/2','5/4','5/4','3/2','11/4','11/4'])['status'],'FAIL')

    def test_coherent_opening_shift_not_material_equivalent(self):
        d=guide();offset=Fraction(1,4)
        for f in d['faces']:
            inner_face=f['id'].startswith('inner-')
            if inner_face and f['axis']==1:
                f['coordinate']=str(Fraction(f['coordinate'])+offset)
            for w in f['wires']:
                if w['role']=='inner' or inner_face:
                    for v in w['vertices']:v[1]=str(Fraction(v[1])+offset)
        self.assertEqual(verify_boundary(d)['status'],'PASS')
        self.assertEqual(compare_material(guide(),d)['status'],'FAIL')

    def test_point_boundary_belongs_to_material(self):
        for p,expected in ((['1','1','2'],'MATERIAL'),(['1','2','2'],'VOID'),(['0','1','2'],'MATERIAL'),(['0','2','2'],'VOID')):
            with self.subTest(point=p):self.assertEqual(classify_point(guide(),p)['classification'],expected)

    def test_disconnected_internal_cavity_boundary_outside_class(self):
        d=block()
        for a in range(3):
            for s in (-1,1):
                d['faces'].append(rectangle('cavity'+str(a)+str(s),a,1 if s>0 else 3,s,1,3,1,3))
        self.assertEqual(verify_boundary(d)['reason'],'disconnected-boundary-components-unsupported')

    def test_touch_separation_intrusion(self):
        eps=Fraction(1,10**12)
        for offset,expected in ((0,'FAIL'),(eps,'PASS'),(-eps,'FAIL')):
            with self.subTest(offset=str(offset)):
                query=['1/2',str(1+offset),str(1+offset),'3/2',str(3-offset),str(3-offset)]
                self.assertEqual(certify_void_box(guide(),query)['status'],expected)

    def test_duplicate_face_rejected(self):
        d=block();f=deepcopy(d['faces'][0]);f['id']='duplicate';f['wires'][0]['id']='duplicate-wire';d['faces'].append(f)
        self.assertEqual(verify_boundary(d)['reason'],'duplicate-or-overlapping-face-patch')

    def test_curve_and_surface_rejected(self):
        for kind in ('curve','surface'):
            d=guide()
            if kind=='curve':d['faces'][0]['wires'][0]['curve_type']='BSplineCurve'
            else:d['faces'][0]['surface']='BSplineSurface'
            self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_floats_and_wrong_units_rejected(self):
        for kind in ('float','unit'):
            d=guide()
            if kind=='float':d['faces'][0]['coordinate']=0.0
            else:d['unit']='mm'
            self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_self_intersecting_trim_rejected(self):
        d=block();w=d['faces'][0]['wires'][0]
        w['vertices']=[['0','0','0'],['0','0','4'],['0','2','4'],['0','2','-1'],['0','4','-1'],['0','4','2'],['0','-1','2'],['0','-1','0']]
        self.assertEqual(verify_boundary(d)['status'],'FAIL')

    def test_box_envelope_conservative_but_not_void_evidence(self):
        result=compare_cells(guide(),[['0','0','0','2','4','4']])
        self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['real_brep'],'UNKNOWN')
        envelope=block()
        self.assertEqual(certify_void_box(envelope,['1/2','3/2','3/2','3/2','5/2','5/2'])['status'],'FAIL')

    def test_real_self_attestation_cannot_promote(self):
        d=guide();d['real_brep_proven']=True;d['extraction_error']='0'
        self.assertEqual(verify_boundary(d)['real_brep'],'UNKNOWN')


if __name__=='__main__':unittest.main()
