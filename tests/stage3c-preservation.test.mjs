import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preservedPagesHash} from '../scripts/stage4a/pages-preservation.mjs';
import {createHash} from 'node:crypto';
const b=JSON.parse(readFileSync('evidence/stage3c/baseline.json'));
const allowed=new Set(['site/stage3b/app.mjs','scripts/build-stage3b-site.mjs']);
const exceptions=JSON.parse(readFileSync('evidence/stage3c/shared-viewer-exceptions.json'));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function verify(read=p=>readFileSync(p)) {
 assert.equal(b.repository,'tetsujisugimori-coder/castle-3d-parts');
 assert.equal(b.head,'34956e1978794aa3d4858c564c51da37d84bfa27');
 assert.equal(Object.keys(b.files).length,1133);
 assert.equal(exceptions.baseline_head,b.head);
 assert.deepEqual(Object.keys(exceptions.files).sort(),[...allowed].sort());
 for(const[p,h]of Object.entries(b.files)) {
  let expected=h;
  if(allowed.has(p)) {
   const e=exceptions.files[p];assert.equal(e.before_sha256,h,p+' baseline');
   assert.equal(hash(read(e.permitted_patch)),e.patch_sha256,p+' permitted diff');
   assert(e.reason.length>20);expected=e.after_sha256;
  }
  const actual=allowed.has(p)?hash(read(p)):preservedPagesHash(p,expected,read);
  assert.equal(actual,expected,p);
 }
 assert.equal(hash(read('site/shared/gate-viewer.mjs')),exceptions.shared_viewer_sha256,'shared dependency');
}
test('Stage3C preserves baseline outside explicit shared-viewer integration',()=>verify());
test('original CAD corruption fails',()=>assert.throws(()=>verify(p=>p.endsWith('.FCStd')?Buffer.from('bad'):readFileSync(p))));
for(const changed of [...allowed,'site/shared/gate-viewer.mjs'])test('shared-viewer exception rejects corrupted bytes: '+changed,()=>assert.throws(()=>verify(p=>p===changed?Buffer.concat([readFileSync(p),Buffer.from(' ') ]):readFileSync(p))));
test('historical certainty does not rise with mechanism success',()=>{const r=JSON.parse(readFileSync('docs/stage3c/research-boundary.json'));assert.equal(r.basis,'D');assert.equal(r.historical_existence.status,'UNKNOWN');assert.equal(r.decision.archaeological_measurement,false);assert.equal(r.hypothesis.status,'UNCONFIRMED');assert.equal(r.verification.physical_load_strength,'UNKNOWN');for(const p of r.previous_references)assert(readFileSync(p).length);for(const s of r.sources){assert(s.id.startsWith('SRC-'));assert(s.observation_id.startsWith('OBS-'));assert(s.url.startsWith('https://'));assert(s.unverified.length)}});
