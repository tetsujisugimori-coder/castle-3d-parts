"""Closed cell must be disjoint from material, including material boundary."""
from fractions import Fraction as F
import unittest
from boundary_contract import void_rectangle


class ContactSpecification(unittest.TestCase):
    def test_contact_separation_penetration(self):
        # Grid is finer than the explicitly chosen synthetic perturbation.
        # These are exact fixture values, not an asserted BRep epsilon.
        for dy,expected in [(F(0),'FAIL'),(-F(1,10**12),'PASS'),(F(1,10**12),'FAIL')]:
            with self.subTest(dy=str(dy)):
                result=void_rectangle('1','0','0','0','3/5',str(F(4,5)+dy),'1/1000000000000000')
                self.assertEqual(result['status'],expected)


if __name__=='__main__':unittest.main(verbosity=2)
