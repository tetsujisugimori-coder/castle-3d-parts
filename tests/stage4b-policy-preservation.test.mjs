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
