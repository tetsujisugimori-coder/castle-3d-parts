import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL(p,root));
const sha=b=>createHash('sha256').update(b).digest('hex');
const base=JSON.parse(read('evidence/stage3a/baseline.json'));
function verify(files,reader=read){
 assert.equal(base.repository,'tetsujisugimori-coder/castle-3d-parts');
 assert.equal(base.commit,'1cc50d1a6d1af8164cada51124cb02279dbe316c');
 assert.equal(Object.keys(files).length,974);
 for(const [p,h] of Object.entries(files)) assert.equal(sha(reader(p)),h,p);
}
test('Stage3A preserves all 974 prior paths byte-for-byte',()=>verify(base.files));
test('preservation rejects changed old CAD bytes',()=>assert.throws(()=>verify(base.files,p=>p.endsWith('.FCStd')?Buffer.from('bad'):read(p))));
test('preservation rejects missing old source',()=>assert.throws(()=>verify(base.files,p=>{if(p==='AGENTS.md')throw Error('missing');return read(p)})));
test('gate research boundary never elevates prototype or existing source',()=>{
 const r=JSON.parse(read('docs/stage3a/research-boundary.json'));
 assert.equal(r.basis,'D');assert.equal(r.cad_eligibility,'prototype_only');
 assert.equal(r.historical_existence.status,'UNKNOWN');assert.equal(r.dimensions.status,'PROTOTYPE');
 assert.equal(r.form_and_structure.status,'ASSUMPTION');assert.equal(r.comparative_examples.status,'NOT_CONFIRMED');
 for(const ref of r.reference_only)assert.ok(read(ref.path).length);
 assert.ok(r.unresolved.length>=5);
});
