import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const base=JSON.parse(readFileSync('evidence/stage3b/baseline.json'));
function verify(reader=p=>readFileSync(p)){
 assert.equal(base.repository,'tetsujisugimori-coder/castle-3d-parts');
 assert.equal(base.commit,'b0713ecc0f18772fc119ba4b51359855d383e086');
 assert.equal(Object.keys(base.files).length,1072);
 for(const [p,v] of Object.entries(base.files))assert.equal(createHash('sha256').update(reader(p)).digest('hex'),v.sha256,p);
}
test('Stage3B preserves all 1072 baseline paths',()=>verify());
test('old CAD byte corruption is rejected',()=>assert.throws(()=>verify(p=>p.endsWith('.FCStd')?Buffer.from('corrupt'):readFileSync(p))));
test('old source deletion is rejected',()=>assert.throws(()=>verify(p=>{if(p==='AGENTS.md')throw Error('missing');return readFileSync(p)})));
test('mechanism prototype does not promote historical evidence',()=>{
 const r=JSON.parse(readFileSync('docs/stage3b/research-boundary.json'));
 assert.equal(r.basis,'D');assert.equal(r.historical_existence.status,'UNKNOWN');
 assert.equal(r.mechanism_hypothesis.basis,'C');assert.equal(r.mechanism_hypothesis.status,'UNCONFIRMED');
 assert.equal(r.dimensions.archaeological_measurement,false);assert.equal(r.comparison_sources.status,'NOT_CONFIRMED');
 for(const ref of r.references)assert.ok(readFileSync(ref.path).length);
});
