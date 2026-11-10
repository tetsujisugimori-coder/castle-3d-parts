import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const b=JSON.parse(readFileSync('evidence/stage3c/baseline.json'));
const allowed=new Set(['site/stage3b/app.mjs','scripts/build-stage3b-site.mjs']);
function verify(read=p=>readFileSync(p)) {assert.equal(b.repository,'tetsujisugimori-coder/castle-3d-parts');assert.equal(b.head,'34956e1978794aa3d4858c564c51da37d84bfa27');assert(Object.keys(b.files).length>1100);for(const[p,h]of Object.entries(b.files))if(!allowed.has(p))assert.equal(createHash('sha256').update(read(p)).digest('hex'),h,p);}
test('Stage3C preserves baseline outside explicit shared-viewer integration',()=>verify());
test('original CAD corruption fails',()=>assert.throws(()=>verify(p=>p.endsWith('.FCStd')?Buffer.from('bad'):readFileSync(p))));
test('historical certainty does not rise with mechanism success',()=>{const r=JSON.parse(readFileSync('docs/stage3c/research-boundary.json'));assert.equal(r.basis,'D');assert.equal(r.historical_existence.status,'UNKNOWN');assert.equal(r.decision.archaeological_measurement,false);assert.equal(r.hypothesis.status,'UNCONFIRMED');assert.equal(r.verification.physical_load_strength,'UNKNOWN');for(const p of r.previous_references)assert(readFileSync(p).length);for(const s of r.sources){assert(s.id.startsWith('SRC-'));assert(s.observation_id.startsWith('OBS-'));assert(s.url.startsWith('https://'));assert(s.unverified.length)}});
