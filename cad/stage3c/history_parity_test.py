"""Compare actual Python and JavaScript state authorities; no CAD runtime claim."""
import json
from pathlib import Path
import subprocess
import unittest
from state import validate_state


class CrossRuntimeContract(unittest.TestCase):
    def test_state_domain_matches_web(self):
        root = Path(__file__).resolve().parents[2]
        cases = [[a, b] for a in [-1, 0, .001, 45, 90, 91, True, None]
                 for b in [-.001, 0, .001, .07, .14, .140001, True, None]]
        script = """
import {readFileSync} from 'node:fs';
import {transition} from './site/stage3c/contract.mjs';
const model=JSON.parse(readFileSync('cad/stage3c/generated/manifest.json'));
const cases=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(cases.map(([angle,bolt])=>{try{transition(model,{angle,bolt},{type:'angle',value:angle});return true}catch{return false}})));
"""
        native = []
        for a, b in cases:
            try:
                validate_state(a, b)
                native.append(True)
            except ValueError:
                native.append(False)
        result = subprocess.run(['node', '--input-type=module', '-e', script],
                                cwd=root, input=json.dumps(cases), text=True,
                                capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), native)
        self.assertEqual(len(cases), 64)


if __name__ == '__main__':
    unittest.main()
