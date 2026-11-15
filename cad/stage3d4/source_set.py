"""Complete bounded execution source/input set; excludes old evidence archives."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def source_paths(root=ROOT):
    paths=[p for p in (root/'cad/stage3d4').glob('*.py')]+list((root/'docs/stage3d4').glob('*.md'))
    paths += [root/p for p in json.loads((root/'cad/stage3d2/contract.json').read_text())['sources']]
    paths += list((root/'cad/stage3d1').glob('*.py')) + list((root/'cad/stage3d2').glob('*.py')) + list((root/'cad/stage3d3').glob('*.py'))
    paths += [root/'cad/stage3d2/contract.json',root/'.github/workflows/stage3d4.yml',root/'scripts/stage3c-hash-evidence.py']
    # Regression commands consume these additional source/input trees. Preserve raw bytes,
    # not only hashes. No old bulky evidence archives are copied.
    for folder in ['cad/stage3c','cad/stage3b','tests','scripts','site','catalog','research','observations','sources','design']:
        paths += [p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.mjs','.js','.json','.html','.css') and 'evidence' not in p.parts and 'generated' not in p.parts]
    paths=sorted(set(paths))
    return paths
