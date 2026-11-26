import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';

const root='evidence/stage4b/policy-migration/';
const records={'AGENTS.md':'AGENTS.md.txt','scripts/stage2d/preservation.mjs':'stage2d-preservation.mjs.txt'};
const h=b=>createHash('sha256').update(b).digest('hex');

/** Preserve exactly the prior two code/policy files, never an arbitrary alternative. */
export function priorPolicyBytes(path,current,read){
 if(!Object.hasOwn(records,path))return null;
 let raw;
 try{raw=read(root+'manifest.json')}
 catch(e){if(e.code==='ENOENT')return null;throw e;}
 const {files}=JSON.parse(raw);
 assert.deepEqual(Object.keys(files),Object.keys(records));
 const e=files[path];
 assert.equal(e.previous,root+records[path]);
 if(h(current)!==e.after_sha256)return null;
 const prior=read(e.previous);
 assert.equal(h(prior),e.before_sha256);
 return prior;
}
