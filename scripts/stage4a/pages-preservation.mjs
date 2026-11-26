import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

const evidence='evidence/stage4a/pages-migration/';
const migration=JSON.parse(readFileSync(new URL('../../'+evidence+'manifest.json',import.meta.url),'utf8'));
const leaf=JSON.parse(readFileSync(new URL('../../evidence/stage4b/pages-integration/manifest.json',import.meta.url),'utf8')).files;
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

/** Return the original digest for an explicitly recorded migration with both versions present. */
export function preservedPagesHash(path,expected,read){
 let actual=sha(read(path));
 if(path==='scripts/build-stage2d-site.mjs'&&Object.hasOwn(leaf,path)&&actual===leaf[path].after_sha256){
  const prior=leaf[path];
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
