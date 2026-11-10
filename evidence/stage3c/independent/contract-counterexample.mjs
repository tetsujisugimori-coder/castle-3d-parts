import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const root=resolve('.');
const historical=readFileSync('evidence/stage3c/independent/before-collision-validator.mjs.txt','utf8').replaceAll("'../stage3b/contract.mjs'",JSON.stringify(pathToFileURL(root+'/site/stage3b/contract.mjs').href));
const before=await import('data:text/javascript;base64,'+Buffer.from(historical).toString('base64'));
const current=await import(pathToFileURL(root+'/site/stage3c/contract.mjs'));
const m=JSON.parse(readFileSync('cad/stage3c/generated/manifest.json'));
const c=JSON.parse(readFileSync('cad/stage3c/generated/collision.json'));
const rows=[];
for(const [name,mutate] of Object.entries({delete_pair:d=>d.samples[0].pairs.pop(),remove_interior_bolt:d=>d.bolt_samples.splice(1,1),wrong_positive_volume:d=>{d.samples[0].pairs[0].overlap_mm3=1;d.samples[0].pairs[0].contact='CLEAR';}})){
 const data=structuredClone(c);mutate(data);
 const row={fault:name};for(const[label,api]of[['before',before],['after',current]]){try{api.validateCollision(structuredClone(m),data);row[label]='ACCEPTED'}catch(e){row[label]='REJECTED';row[label+'_reason']=e.message}}rows.push(row);
}
writeFileSync('evidence/stage3c/independent/contract-counterexample.json',JSON.stringify(rows,null,2)+'\n');console.log(rows);if(rows.some(r=>r.after!=='REJECTED'))process.exitCode=1;
