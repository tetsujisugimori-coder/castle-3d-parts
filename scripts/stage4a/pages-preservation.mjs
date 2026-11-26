import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {priorPolicyBytes} from '../stage4b/policy-preservation.mjs';

const evidence='evidence/stage4a/pages-migration/';
const migration=JSON.parse(readFileSync(new URL('../../'+evidence+'manifest.json',import.meta.url),'utf8'));
const currentLeafBuilderSha='8da1bd7f138ff110fdb5286cda73727e2fa56fc298991977dceaa4b50f4dff00';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

/** Return the original digest for an explicitly recorded migration with both versions present. */
export function preservedPagesHash(path,expected,read){
 const historical=priorPolicyBytes(path,read(path),read);
 if(historical&&sha(historical)===expected)return expected;
 let actual=sha(read(path));
 if(path==='scripts/build-stage2d-site.mjs'){
  const {files}=JSON.parse(read('evidence/stage4b/pages-integration/manifest.json'));
  assert.deepEqual(Object.keys(files),[path]);
  const prior=files[path];
  assert.equal(prior.after_sha256,currentLeafBuilderSha,'unexpected approved Pages builder fingerprint');
  if(actual!==currentLeafBuilderSha)return actual;
  assert.equal(prior.previous,'evidence/stage4b/pages-integration/build-stage2d-site.mjs.txt');
  assert.equal(prior.before_sha256,migration.files[path].after_sha256);
  assert.equal(sha(read(prior.previous)),prior.before_sha256,path+' Stage 4-A archived version');
  actual=prior.before_sha256;
 }
 if(actual===expected||!Object.hasOwn(migration.files,path))return actual;
 const change=migration.files[path];
 if(change.before_sha256!==expected||change.after_sha256!==actual)return actual;
 assert.equal(sha(read(evidence+'originals/'+path+'.txt')),expected,path+' archived original');
 return expected;
}
