import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {preservedPagesHash} from '../scripts/stage4a/pages-preservation.mjs';

const evidence='evidence/stage4a/pages-migration/';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const files=JSON.parse(readFileSync(evidence+'manifest.json')).files;
const leaf=JSON.parse(readFileSync('evidence/stage4b/pages-integration/manifest.json')).files;
const expectedPaths=[
 'scripts/build-stage2d-site.mjs',
 'tests/stage3a-preservation.test.mjs',
 'tests/stage3b-preservation.test.mjs',
];
test('Pages preservation migration is limited to the builder and two prior verifiers',()=>{
 assert.deepEqual(Object.keys(files),expectedPaths);
 for(const path of expectedPaths){
  const {before_sha256,after_sha256}=files[path];
  const archive=evidence+'originals/'+path+'.txt';
  assert.notEqual(after_sha256,before_sha256,path);
  if(Object.hasOwn(leaf,path)){
   assert.equal(leaf[path].before_sha256,after_sha256,path);
   assert.equal(sha(readFileSync(leaf[path].previous)),after_sha256,path);
   assert.equal(sha(readFileSync(path)),leaf[path].after_sha256,path);
  }else assert.equal(sha(readFileSync(path)),after_sha256,path);
  assert.equal(preservedPagesHash(path,before_sha256,readFileSync),before_sha256,path);
  const corrupt=Buffer.from('unexpected bytes');
  assert.notEqual(preservedPagesHash(path,before_sha256,p=>p===path?corrupt:readFileSync(p)),before_sha256,path);
  assert.throws(()=>preservedPagesHash(path,before_sha256,p=>p===archive?corrupt:readFileSync(p)),/archived original/);
 }
});

test('coordinated Stage 4-B builder and change receipt tamper fails',()=>{
 const path='scripts/build-stage2d-site.mjs';
 const receipt='evidence/stage4b/pages-integration/manifest.json';
 const modified=Buffer.concat([readFileSync(path),Buffer.from('\n// unapproved extra bytes\n')]);
 const forged=JSON.parse(readFileSync(receipt));
 forged.files[path].after_sha256=sha(modified);
 assert.throws(()=>preservedPagesHash(path,files[path].before_sha256,
  p=>p===receipt?Buffer.from(JSON.stringify(forged)):p===path?modified:readFileSync(p)),
 /unexpected approved Pages builder fingerprint/);
});
