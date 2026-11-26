"""Verify the exact exception without altering archived or current files."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cad/stage2c'))
from check import validate_policy_append

class PolicyCADContract(unittest.TestCase):
    def test_exact_prefix_and_suffix_only(self):
        old=(ROOT/'evidence/stage4b/policy-migration/AGENTS.md.txt').read_bytes()
        current=(ROOT/'AGENTS.md').read_bytes()
        sha='214c11b29e29c95284150648314ec7c9faaa41c42e89ab7c365af796f5ab09de'
        validate_policy_append(old,current,sha)
        for prior,candidate in ((old,current[1:]),(old,current+b'\n'),(old+b'\n',current)):
            with self.assertRaises(AssertionError):
                validate_policy_append(prior,candidate,sha)
if __name__=='__main__':
    unittest.main()
