import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('../../../',import.meta.url));
const here=fileURLToPath(new URL('./',import.meta.url));
const current=await import(pathToFileURL(join(root,'scripts/observation-register.mjs')).href);
let oldText=readFileSync(join(here,'old-observation-register.mjs'),'utf8');
oldText=oldText.replace("'./source-register.mjs'",JSON.stringify(pathToFileURL(join(root,'scripts/source-register.mjs')).href));
oldText=oldText.replace("'./observation-schema.mjs'",JSON.stringify(pathToFileURL(join(here,'old-observation-schema.mjs')).href));
oldText=oldText.replace("fileURLToPath(new URL('../',import.meta.url))",JSON.stringify(root));
oldText=oldText.replace("join(root,'observations/schema/observation.schema.json')",JSON.stringify(join(here,'old-observation.schema.json')));
// Only disable the snapshot CLI entry guard for data-URL import; validation code is unchanged.
oldText=oldText.replace("if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))run();",'');
const old=await import('data:text/javascript;base64,'+Buffer.from(oldText).toString('base64'));
const positive=JSON.parse(readFileSync(join(here,'positive-original.json'),'utf8'));
const currentPositive=current.loadObservations();
const result=fn=>{try{fn();return {accepted:true,error:null}}catch(e){return {accepted:false,error:e.message}}};
assert.equal(result(()=>old.validateObservations(positive)).accepted,true);
assert.equal(result(()=>current.validateObservations(currentPositive)).accepted,true);
const mutations={unit_masquerade:r=>{let m=r.measurements[1];m.unit='m';m.original_unit='m'},quantity_from_depth:r=>{let m=r.measurements[0];m.value=12;m.original_value=12;m.original_text='12'},reported_spacing_to_depth:r=>{let m=r.measurements[1];m.lower=4.9;m.upper=27.7;m.original_lower=4.9;m.original_upper=27.7;m.original_text='4.9〜27.7cm'},fake_id_number:r=>{r.scope='individual';r.original_ids=[{value:'19',reference_ids:['R01']}];r.measurements=[]},fake_id_noun:r=>{r.scope='individual';r.original_ids=[{value:'柱穴',reference_ids:['R01']}];r.measurements=[]}};
const cases=[];
for(const [name,mutate] of Object.entries(mutations)){
 const saved=JSON.parse(readFileSync(join(here,name+'.json'),'utf8'));
 const exactOld=result(()=>old.validateObservations(saved)),exactNew=result(()=>current.validateObservations(saved));
 const upgraded=structuredClone(currentPositive);mutate(upgraded[5].record);
 const upgradedNew=result(()=>current.validateObservations(upgraded));
 assert.equal(exactOld.accepted,true,name+' old RED');assert.equal(exactNew.accepted,false,name+' saved input');assert.equal(upgradedNew.accepted,false,name+' current-schema GREEN');
 cases.push({name,exactOld,exactNew,upgradedNew});
}
// Expectations transcribed independently from p125 and figure 65, not calculated from product extraction code.
assert.deepEqual(current.extractionContract.measurements.map(x=>[x.statistic,x.unit,x.value,x.lower,x.upper]),[['single','count',19,null,null],['range','cm',null,50,70],['mean','cm',58.6,null,null],['range','cm',null,4.9,27.7],['mean','cm',12,null,null]]);
assert.deepEqual(current.extractionContract.identifiers[0].values,Array.from({length:19},(_,i)=>'P'+(i+1)));
const additional=[];
const check=(name,mutate,accept=false)=>{const e=structuredClone(currentPositive);mutate(e);const out=result(()=>current.validateObservations(e));assert.equal(out.accepted,accept,name);additional.push({name,...out})};
check('cm-to-m preserves source values',e=>{const m=e[5].record.measurements[1];m.unit='m';m.lower=.5;m.upper=.7},true);
check('cm-to-mm preserves source values',e=>{const m=e[5].record.measurements[1];m.unit='mm';m.lower=500;m.upper=700},true);
check('basis cannot bypass contract',e=>{const m=e[5].record.measurements[1];m.basis='measured';m.method='claimed measurement';m.assertion_id=null});
check('wrong assertion ID',e=>e[5].record.measurements[1].assertion_id='SRC-0008/L01/M04');
check('original ID needs checked figure',e=>e[5].record.references[1].figure_status='not_checked');
check('borrowed value cannot gain source identity',e=>{const r=e[0].record;r.original_ids=[{value:'P1',reference_ids:['R01']}];r.scope='individual'});
check('unknowns false filter can have a match',e=>{e[0].record.unknowns=[]},true);
const out={executed_at:new Date().toISOString(),classification:'independent new execution',positiveOld:true,positiveCurrent:true,cases,additional,independentContractExpectations:'PASS',sourceSha256:createHash('sha256').update(readFileSync(join(root,'scripts/observation-register.mjs'))).digest('hex')};
if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify(out,null,2));
