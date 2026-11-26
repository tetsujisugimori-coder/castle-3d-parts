import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {priorPolicyBytes} from '../scripts/stage4b/policy-preservation.mjs';

test('policy exception accepts only the exact predecessor and exact approved replacement',()=>{
 const read=p=>readFileSync(p),h=b=>createHash('sha256').update(b).digest('hex');
 const old={'AGENTS.md':'214c11b29e29c95284150648314ec7c9faaa41c42e89ab7c365af796f5ab09de','scripts/stage2d/preservation.mjs':'efe2cc3fc367162c0f104f0d41756456f0a611378c5c207a24aef78b3cb4b37b'};
 for(const [p,dig] of Object.entries(old)){
  assert.equal(h(priorPolicyBytes(p,read(p),read)),dig,p);
  assert.equal(priorPolicyBytes(p,Buffer.concat([read(p),Buffer.from(' ')]),read),null,p);
  assert.throws(()=>priorPolicyBytes(p,read(p),f=>f.endsWith('.txt')?Buffer.from('corrupt'):read(f)));
 }
 assert.equal(priorPolicyBytes('site/index.html',Buffer.from('other'),read),null);
});

test('coordinated AGENTS + receipt hash edits and changes to the historical prefix are rejected',()=>{
 const read=p=>readFileSync(p),h=b=>createHash('sha256').update(b).digest('hex');
 const path='AGENTS.md', receipt='evidence/stage4b/policy-migration/manifest.json';
 for(const bad of [Buffer.from('# replacement\n'),Buffer.concat([read(path),Buffer.from('unexpected suffix\n')]),read(path).subarray(1)]){
  const content=JSON.parse(read(receipt));
  content.files[path].after_sha256=h(bad);
  assert.throws(()=>priorPolicyBytes(path,bad,p=>p===receipt?Buffer.from(JSON.stringify(content)):read(p)),/unexpected approved replacement fingerprint/);
 }
});
