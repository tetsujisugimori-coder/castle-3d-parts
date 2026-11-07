// Historical, deliberately vulnerable validator runs only against synthetic record mutations.
import {mkdtempSync, mkdirSync, cpSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {root, schema, loadRecords, validateRegister, validateSchema} from './source-register.mjs';
export const mutations = [
 ['all-web-requests-failed',e=>e[1].record.access.checks.forEach(x=>x.outcome='failed'),'WEB_ACCESS_EVIDENCE'],
 ['all-bibliography-requests-failed',e=>e[2].record.access.checks.forEach(x=>x.outcome='failed'),'BIBLIOGRAPHY_EVIDENCE'],
 ['partial-text-promoted-to-complete',e=>{e[0].record.research.locations=e[0].record.research.locations.slice(0,1);e[0].record.verification.text='fully_collated'},'ENUM'],
 ['one-figure-promoted-to-complete',e=>e[7].record.verification.figures='fully_collated','ENUM'],
 ['download-receipt-for-different-file',e=>e[0].record.access.checks.find(x=>x.outcome==='downloaded').url='https://example.com/unrelated.pdf','ACQUISITION_EVIDENCE'],
 ['unread-passage-url',e=>e[0].record.research.locations[0].evidence_url='https://example.com/unread.pdf','PASSAGE_ACCESS_EVIDENCE'],
 ['duplicate-doi-different-volume',e=>{const r=structuredClone(e[6]);r.name='SRC-0011.json';r.record.id='SRC-0011';r.record.bibliography.volume='22';r.record.research.related_source_ids=[];e.push(r)},'DUPLICATE_IDENTIFIER'],
];
export const schemaMutations = [
 ['empty-array-unsupported-schema-keyword',s=>s.properties.research.properties.locations.items.unsupportedKeyword=true,'SCHEMA_UNSUPPORTED'],
 ['null-value-unsupported-schema-format',s=>s.properties.access.properties.pdf_url.format='unsupported','SCHEMA_FORMAT'],
 ['unsupported-schema-dialect',s=>s.$schema='https://example.com/unknown-dialect','SCHEMA_DIALECT'],
 ['schema-valued-additional-properties',s=>s.additionalProperties={type:'integer'},'SCHEMA_VALUE',r=>r.uncheckedExtra='not an integer'],
 ['null-schema-type',s=>s.properties.access.properties.pdf_pages.type=null,'SCHEMA_TYPE',r=>r.access.pdf_pages='not a page count'],
 ['empty-schema-dialect',s=>s.$schema='','SCHEMA_DIALECT']
];
const outcome=fn=>{try{fn();return {accepted:true,reason:null}}catch(e){return {accepted:false,reason:e.message}}};
export async function runControls() {
 const temp=mkdtempSync(join(tmpdir(),'castle-source-controls-'));
 try {
  mkdirSync(join(temp,'scripts'));mkdirSync(join(temp,'sources/schema'),{recursive:true});
  cpSync(join(root,'evidence/source-register/red/source-register.mjs.txt'),join(temp,'scripts/source-register.mjs'));
  cpSync(join(root,'evidence/source-register/red/source.schema.json'),join(temp,'sources/schema/source.schema.json'));
  const old=await import(pathToFileURL(join(temp,'scripts/source-register.mjs')));
  const input=loadRecords();const results=[];
  const positive={old:outcome(()=>old.validateRegister(structuredClone(input))),new:outcome(()=>validateRegister(structuredClone(input)))};
  for(const [name,mutate,code] of mutations) {
   const e=structuredClone(input);mutate(e);
   results.push({name,expected_reason:code,red:outcome(()=>old.validateRegister(e)),green:outcome(()=>validateRegister(e))});
  }
  for(const [name,mutate,code,mutateRecord] of schemaMutations) {
   const before=structuredClone(old.schema),after=structuredClone(schema);mutate(before);mutate(after);
   const record=structuredClone(input[2].record);if(mutateRecord)mutateRecord(record);
   results.push({name,expected_reason:code,red:outcome(()=>old.validateSchema(record,before)),green:outcome(()=>validateSchema(record,after))});
  }
  const pass=positive.old.accepted && positive.new.accepted && results.every(x=>x.red.accepted && !x.green.accepted && x.green.reason.startsWith(x.expected_reason));
  return {status:pass?'PASS':'FAIL',positive,counterexamples:results.length,results};
 } finally {rmSync(temp,{recursive:true,force:true})}
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
 const result=await runControls();console.log(JSON.stringify(result,null,2));if(result.status!=='PASS')process.exitCode=1;
}
