import copy, unittest
from fractions import Fraction as Q
from proof_contract import *

def fixture():
    return {'curve_type':'Line','pcurve_type':'Line2d','surface_type':'Plane',
       'c0':['1','2','3'],'c1':['1','0','0'],'p0':['1','2'],'p1':['1','0'],
       'origin':['0','0','3'],'u_axis':['1','0','0'],'v_axis':['0','1','0'],'range':['0','10']}

class Contract(unittest.TestCase):
    def test_full_parameter_identity(self):
        self.assertEqual(line_plane_identity(fixture())['status'],'PASS')
    def test_curve_pcurve_surface_faults(self):
        for field,index in [('c0',0),('c1',0),('p0',1),('p1',0),('origin',2),('u_axis',2),('v_axis',2)]:
            f=fixture();f[field][index]=str(q(f[field][index])+1)
            self.assertEqual(line_plane_identity(f)['status'],'FAIL')
    def test_unsupported_not_false_collision(self):
        f=fixture();f['pcurve_type']='BSpline';self.assertEqual(line_plane_identity(f)['status'],'UNKNOWN')
    def test_degenerate_plane(self):
        f=fixture();f['v_axis']=['0','0','0'];f['c0']=['1','0','3'];f['p0']=['1','0']
        self.assertEqual(line_plane_identity(f)['reason'],'DEGENERATE_PLANE_AXES')
    def test_bad_range_and_type(self):
        for v in [['1','0'],['0','0'],[False,1],[0,float('nan')]]:
            f=fixture();f['range']=v
            with self.assertRaises(ValueError):line_plane_identity(f)
    def test_missing_bound_unknown(self):
        for k in ERROR_DOMAINS:
            b=dict.fromkeys(ERROR_DOMAINS,'1/10000');b[k]=None
            self.assertEqual(error_sum(b)['status'],'UNKNOWN')
    def test_underreport(self):
        b=dict.fromkeys(ERROR_DOMAINS,'1/10000')
        self.assertEqual(error_sum(b,'7/10000')['status'],'FAIL')
        self.assertEqual(error_sum(b,'8/10000')['status'],'PASS')
    def test_native_claims_never_certify(self):
        r=representative({'clearance_lower':'1'},dict.fromkeys(ERROR_DOMAINS,'0'),dict.fromkeys(NATIVE_OBLIGATIONS,'PASS'))
        self.assertEqual(r['status'],'NOT_TESTED');self.assertEqual(r['conditional_arithmetic']['status'],'PASS')
    def test_nonpositive_not_collision(self):
        r=representative({'clearance_lower':'1'},dict.fromkeys(ERROR_DOMAINS,'1'))
        self.assertEqual(r['conditional_arithmetic']['status'],'UNKNOWN');self.assertEqual(r['status'],'NOT_TESTED')
    def test_path(self):
        e,ids=fixed_path_controls();r=chain(e,ids,'local','m-world')
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['matrix'][3],['1/100','1/100']);self.assertEqual(r['matrix'][7],['1/50','1/50'])
        for bad in [e[:1]+e[2:],e[:1]+e,e[::-1]]:self.assertEqual(chain(bad,ids,'local','m-world')['status'],'FAIL')
        b=copy.deepcopy(e);b[-1]['matrix']=IDENTITY
        self.assertEqual(chain(b,ids,'local','m-world')['status'],'FAIL')
    def test_nonidentity_not_silently_normalized(self):
        e,ids=fixed_path_controls();e[0]['matrix'][0]=2
        r=chain(e,ids,'local','m-world');self.assertEqual(r['matrix'][0],['1/500','1/500'])
        self.assertNotEqual(r['matrix'][0],['1/1000','1/1000'])

if __name__=='__main__':unittest.main()
