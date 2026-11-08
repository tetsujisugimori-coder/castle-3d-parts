import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {readFileSync,writeFileSync,cpSync,mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
const root=process.cwd(), m=await import(pathToFileURL(resolve(root,'scripts/research-cad.mjs')));
const rows=[];function reject(name,fn){try{fn();rows.push({name,status:'RED',actual:'ACCEPTED'});}catch(e){rows.push({name,status:'PASS',actual:e.message});}}
const s=m.snapshot(root,m.BASE),p=m.propose(s,s,[{parameter:'post_height',proposed_value:2.2,unit:'m'}],'independent D test only');
const meta={id:'DEC-WORK-INDEPENDENT',actor:'independent review counterexample',at:'2026-11-08T21:20:00Z',reason:'D test not historical approval'},a=m.decide(p,'approved',meta);
reject('applied without real manifest',()=>m.decide(a,'applied',{...meta,manifest_sha256:'a'.repeat(64)}));
reject('unapproved apply',()=>m.application(p));
for(const state of ['deferred','rejected'])reject(state+' apply',()=>m.application(m.decide(p,state,meta)));
reject('cycle',()=>m.validateGraph([{id:'a'},{id:'b'}],[{from:'a',to:'b'},{from:'b',to:'a'}]));
reject('missing reference',()=>m.validateGraph([{id:'a'}],[{from:'a',to:'missing'}]));
for(const [field,value] of [['part_id','forged-part'],['basis','A'],['decision_ids',['DEC-9999']]]){const c=structuredClone(p);c[field]=value;const {id,sha256,status,events,approval,...payload}=c;c.sha256=m.digest(payload);c.id='CADREV-'+c.sha256.slice(0,16);reject('rehashed '+field,()=>m.validateCandidate(c));}
const c=structuredClone(a);c.parameter_changes[0].proposed_value=2.4;const {id,sha256,status,events,approval,...payload}=c;c.sha256=m.digest(payload);c.id='CADREV-'+c.sha256.slice(0,16);reject('rehashed approved numerical edit',()=>m.application(c));
const f=structuredClone(p);f.after_snapshot.records[0].data.title='forged';const {sha256:sh,...sp}=f.after_snapshot;f.after_snapshot.sha256=m.digest(sp);reject('rehashed forged evidence',()=>m.validateCandidate(f));
reject('unit mismatch',()=>m.propose(s,s,[{parameter:'post_height',proposed_value:2200,unit:'mm'}],'wrong unit test'));
const dir=mkdtempSync(resolve(tmpdir(),'independent-stage2a-'));try{cpSync(root,dir,{recursive:true,filter:path=>!path.includes('/evidence/stage2a')&&!path.includes('/dist')});const app=m.application(a);const src=resolve(dir,'sources/records/SRC-9999.json');writeFileSync(src,'{}');reject('added source stale',()=>m.validateApplication(app,dir));rmSync(src);const path=resolve(dir,'research/hypotheses/HYP-0001.json'),bytes=readFileSync(path);writeFileSync(path,Buffer.concat([bytes,Buffer.from(' ')]));reject('changed research stale',()=>m.validateApplication(app,dir));rmSync(path);reject('deleted research stale',()=>m.validateApplication(app,dir));writeFileSync(path,bytes);writeFileSync(resolve(dir,'site/cad/palisade.glb'),'forged');reject('binary original forged',()=>m.validateApplication(app,dir));}finally{rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({source_sha256:m.hash(readFileSync(resolve(root,'scripts/research-cad.mjs'))),original_files_preserved:m.preserve(),results:rows},null,2));
