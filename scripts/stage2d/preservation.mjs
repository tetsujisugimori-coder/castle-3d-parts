/** Explicit code migration only. Historical manifests and all data remain immutable. */
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
export const REPLACEMENTS = ['.github/workflows/pages.yml','scripts/research-cad.mjs','scripts/stage2b.mjs','tests/hypothesis-preservation.test.mjs','scripts/cad-prototype.mjs','scripts/design-register.mjs','scripts/verification-register.mjs','scripts/hypothesis-evidence.mjs','cad/stage2c/check.py'];
const digest=(b,kind)=>kind==='git-blob'?createHash('sha1').update(`blob ${b.length}\0`).update(b).digest('hex'):createHash('sha256').update(b).digest('hex');
export function originalBytes(root,path,expected,kind='sha256'){
 const current=readFileSync(resolve(root,path));
 if(digest(current,kind)===expected)return current;
 if(!REPLACEMENTS.includes(path))throw Error('ORIGINAL_CHANGED '+path);
 const changes=JSON.parse(readFileSync(resolve(root,'design/stage2d/code-migrations.json')));
 if(Object.keys(changes.files).sort().join('|')!==[...REPLACEMENTS].sort().join('|'))throw Error('MIGRATION_SET');
 const entry=changes.files[path],old=readFileSync(resolve(root,entry.archive));
 if(entry.archive!=='design/stage2d/originals/'+path+'.txt'||digest(old,kind)!==expected||digest(old,'sha256')!==entry.before_sha256||digest(current,'sha256')!==entry.after_sha256)throw Error('MIGRATION_HASH '+path);
 return old;
}
