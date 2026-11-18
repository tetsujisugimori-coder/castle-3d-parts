"""Direct observer contracts, with absent OCP explicitly BLOCKED, not native PASS."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('d5d_direct',Path(__file__).with_name('direct_capture.py'))
mod=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(mod)


def fresh(label, synthetic_environment_mock=False):
    base=Path(os.environ.get('TMPDIR',str(mod.ROOT/'.work-d5d-tests')))/'5d-native'
    base.mkdir(parents=True,exist_ok=True)
    case=Path(tempfile.mkdtemp(prefix=label+'-',dir=base))
    (case/'test-context.json').write_text(json.dumps({'case':label,'synthetic_environment_mock':synthetic_environment_mock,'scope':'test environment/contract, not automatic native evidence PASS'})+'\n')
    return case/'output'


class DirectCaptureContract(unittest.TestCase):
    def test_missing_ocp_is_blocked(self):
        out=fresh('missing-ocp',True)
        with patch.object(mod,'environment',side_effect=ImportError('synthetic missing OCP')):
            self.assertEqual(mod.main(out),2)
        self.assertEqual(json.loads((out/'results.json').read_text())['capture'],'BLOCKED')

    def test_unknown_kernel_stops_before_cad_read(self):
        out=fresh('unknown-version',True)
        with patch.object(mod,'environment',return_value={'loaded_occt_version_identification':'UNKNOWN'}):
            self.assertEqual(mod.main(out),2)
        self.assertFalse((out/'isolated').exists())

    def test_output_refuses_overwrite(self):
        out=fresh('overwrite-protection');out.mkdir();(out/'keep').write_text('unchanged')
        with self.assertRaises(FileExistsError):mod.main(out)
        self.assertEqual((out/'keep').read_text(),'unchanged')

    def test_exact_representation_no_epsilon(self):
        self.assertEqual(mod.q(.5),'1/2')
        self.assertNotEqual(mod.q(.1),'1/10')

    def test_native_observer_if_available(self):
        out=fresh('real-environment-probe');rc=mod.main(out)
        result=json.loads((out/'results.json').read_text())
        if rc==2:
            self.assertEqual(result['capture'],'BLOCKED')
            # A passing conditional contract is not native execution success.
            return
        self.assertEqual(rc,0)
        data=json.loads((out/'direct-capture.json').read_text())
        self.assertEqual(data['native_material'],'UNKNOWN')
        self.assertEqual(data['finite_real_error'],'UNKNOWN')
        self.assertEqual(data['representative_native'],'NOT_TESTED')
        self.assertEqual(data['source_unchanged'],'PASS')
        self.assertEqual(sum(len(x['pcurve_uses']) for x in data['parts'].values()),72)
        for part in data['parts'].values():
            self.assertTrue(all(x['status']=='PASS' for x in part['coverage'].values()))
            self.assertTrue(all(isinstance(e['same_parameter_flag'],bool) for e in part['inventory']['edge']))
            self.assertTrue(all(u['native_trim_correspondence']=='UNKNOWN' for u in part['pcurve_uses']))


if __name__=='__main__':unittest.main()
