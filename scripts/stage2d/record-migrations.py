"""Maintenance command. Only after review of an intended code change; never run in CI."""
import subprocess,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
paths=['.github/workflows/pages.yml','scripts/research-cad.mjs','scripts/stage2b.mjs','tests/hypothesis-preservation.test.mjs','scripts/cad-prototype.mjs','scripts/design-register.mjs','scripts/verification-register.mjs','cad/stage2c/check.py']
h=lambda b:hashlib.sha256(b).hexdigest()
rows={}
for p in paths:
 old=subprocess.check_output(['git','show','dec85b596f6b82bfd69129e4b1edbc75d182318c:'+p],cwd=root)
 dest='design/stage2d/originals/'+p+'.txt';(root/dest).parent.mkdir(parents=True,exist_ok=True);(root/dest).write_bytes(old)
 rows[p]={'archive':dest,'before_sha256':h(old),'after_sha256':h((root/p).read_bytes()),'reason':'Official Pages build connection' if p.endswith('pages.yml') else 'Exact-hash preservation contract migration; source/CAD/research remains byte protected'}
(root/'design/stage2d/code-migrations.json').write_text(json.dumps({'baseline':'dec85b596f6b82bfd69129e4b1edbc75d182318c','files':rows},indent=2)+'\n')
