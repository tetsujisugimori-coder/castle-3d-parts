import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

const evidence='evidence/stage4a/pages-migration/';
const migration=JSON.parse(readFileSync(new URL('../../'+evidence+'manifest.json',import.meta.url),'utf8'));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

/** Return the original digest for an explicitly recorded migration with both versions present. */
export function preservedPagesHash(path,expected,read){
 const actual=sha(read(path));
 if(actual===expected||!Object.hasOwn(migration.files,path))return actual;
 const change=migration.files[path];
 if(change.before_sha256!==expected||change.after_sha256!==actual)return actual;
 assert.equal(sha(read(evidence+'originals/'+path+'.txt')),expected,path+' archived original');
 return expected;
}
