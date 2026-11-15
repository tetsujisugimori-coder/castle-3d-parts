import os,tempfile,unittest
from pathlib import Path
from stage3d5d.record_controls import record
class FullControlEvidence(unittest.TestCase):
    def test_complete_control_record(self):
        base=Path(os.environ.get('TMPDIR',str(Path.cwd()/'.work5d')))/'5d-proof-controls';base.mkdir(parents=True,exist_ok=True)
        out=Path(tempfile.mkdtemp(prefix='retained-',dir=base))/'evidence'
        rows=record(out);self.assertEqual(len(rows),13)
