import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {root, schema, validateSchema, loadRecords, validateRegister, renderIndex} from '../scripts/source-register.mjs';
const original=loadRecords();
const copy=()=>structuredClone(original);
const reject=(name,mutation,code)=>test(name,()=>{const e=copy();mutation(e);assert.throws(()=>validateRegister(e),new RegExp(code));});
test('ten distinct records for nine candidates, with independent editions',()=>{
 const records=validateRegister(original);assert.equal(records.length,10);
 assert.deepEqual(records.map(r=>r.id),Array.from({length:10},(_,i)=>`SRC-${String(i+1).padStart(4,'0')}`));
 assert.equal(records[5].verification.acquisition,'unavailable');
 assert.equal(records[5].access.pdf_url,null);
 assert.equal(records[9].bibliography.publication_year,2004);
 assert.equal(records[9].bibliography.edition,'第2版（一部改訂）');
 assert.equal(records[9].verification.text,'not_checked');
});
test('same set-level catalogue ID is valid for two separate volumes',()=>{validateRegister(original);assert.deepEqual(original[2].record.bibliography.identifiers[0],original[3].record.bibliography.identifiers[0]);});
test('generated index matches records byte for byte',()=>assert.equal(renderIndex(validateRegister(original)),readFileSync(join(root,'sources/index.md'),'utf8')));
test('repeated generation is stable and does not mutate source records',()=>{const before=JSON.stringify(original);assert.equal(renderIndex(validateRegister(original)),renderIndex(validateRegister(original)));assert.equal(JSON.stringify(original),before)});
test('empty register is rejected',()=>assert.throws(()=>validateRegister([]),/EMPTY_REGISTER/));
reject('missing required field',e=>delete e[0].record.title,'MISSING:title');
reject('unknown record property',e=>e[0].record.confidence=90,'EXTRA:confidence');
reject('unknown nested property',e=>e[0].record.verification.reliability=90,'EXTRA:reliability');
reject('invalid status',e=>e[0].record.verification.text='verified','ENUM');
reject('null and string are distinct types',e=>e[0].record.access.pdf_pages='170','TYPE');
reject('duplicate source ID',e=>e.push(structuredClone(e[0])),'DUPLICATE_ID');
reject('filename and ID mismatch',e=>e[0].name='SRC-9999.json','FILENAME');
reject('dangling related source',e=>e[0].record.research.related_source_ids.push('SRC-9999'),'RELATED_ID');
reject('self reference',e=>e[0].record.research.related_source_ids.push('SRC-0001'),'RELATED_ID');
reject('duplicate bibliography with new ID',e=>{const r=structuredClone(e[0]);r.name='SRC-0011.json';r.record.id='SRC-0011';e.push(r)},'DUPLICATE_BIBLIOGRAPHY');
reject('renamed duplicate identifier',e=>{const r=structuredClone(e[0]);r.name='SRC-0011.json';r.record.id='SRC-0011';r.record.title='別名';e.push(r)},'DUPLICATE_IDENTIFIER');
reject('duplicate passage ID',e=>e[0].record.research.locations.push(structuredClone(e[0].record.research.locations[0])),'DUPLICATE_LOCATOR');
reject('unsafe URL protocol',e=>e[0].record.access.official_url='javascript:alert(1)','PATTERN');
reject('invalid URL',e=>e[0].record.access.official_url='https://','URL');
reject('URL credentials prohibited',e=>e[0].record.access.official_url='https://user:password@example.com','URL');
reject('impossible access date',e=>e[0].record.access.last_checked='2026-02-30','DATE');
reject('invalid hash',e=>e[0].record.access.acquired_sha256='not a hash','PATTERN');
reject('acquisition without hash',e=>e[0].record.access.acquired_sha256=null,'ACQUISITION_EVIDENCE');
reject('acquisition without download record',e=>e[0].record.access.checks=e[0].record.access.checks.filter(x=>x.outcome!=='downloaded'),'ACQUISITION_EVIDENCE');
reject('catalogue-only cannot count as text checked',e=>e[2].record.verification.text='partial_checked','VERIFICATION_CONTRADICTION');
reject('catalogue cannot have acquired hash',e=>e[2].record.access.acquired_sha256='a'.repeat(64),'ACQUISITION_CONTRADICTION');
reject('text checked without passage evidence',e=>e[9].record.verification.text='partial_checked','TEXT_EVIDENCE');
reject('figures checked without figure locator',e=>e[0].record.verification.figures='partial_checked','FIGURE_EVIDENCE');
reject('unchecked text conflicts with verified passage',e=>e[0].record.verification.text='not_checked','TEXT_CONTRADICTION');
reject('unchecked figures conflicts with verified figure',e=>e[7].record.verification.figures='not_checked','FIGURE_CONTRADICTION');
reject('unchecked quotation rejected',e=>{e[2].record.research.locations.push({id:'L01',kind:'quote',locator:'unknown',text:'not read',evidence_url:'https://example.com',text_checked:false,figure_checked:false})},'UNCHECKED_PASSAGE');
test('malformed JSON fails before validation',()=>{const dir=mkdtempSync(join(tmpdir(),'source-register-'));try{writeFileSync(join(dir,'SRC-0001.json'),'{broken');assert.throws(()=>loadRecords(dir),SyntaxError)}finally{rmSync(dir,{recursive:true})}});
test('schema keyword expansion cannot be silently ignored',()=>assert.throws(()=>validateSchema(original[0].record,{...schema,unknownKeyword:true}),/SCHEMA_UNSUPPORTED/));
test('Markdown escapes separator and newline',()=>{const e=copy();e[0].record.title='a|b\nc';assert.match(renderIndex(validateRegister(e)),/a\\\|b c/)});
test('legacy 3D source bytes preserved at fixed main',()=>{
 const manifest=JSON.parse(readFileSync(join(root,'tests/fixtures/source-register-legacy-hashes.json'),'utf8'));
 for(const [path,hash] of Object.entries(manifest.files)) assert.equal(createHash('sha256').update(readFileSync(join(root,path))).digest('hex'),hash,path);
});

import {runControls} from '../scripts/source-register-controls.mjs';
test('independent thirteen counterexamples RED to GREEN, positive stays accepted',async()=>{
 const result=await runControls();assert.equal(result.status,'PASS');assert.equal(result.counterexamples,13);
});
reject('impossible publication date',e=>e[0].record.bibliography.publication_date='2023-02-30','PUBLICATION_DATE');
reject('publication year contradiction',e=>e[0].record.bibliography.publication_date='2022-03-10','PUBLICATION_DATE');
reject('invalid DOI format',e=>e[6].record.bibliography.identifiers.find(x=>x.scheme==='DOI').value='not-a-doi','IDENTIFIER_FORMAT');
test('schema-valued additionalProperties fails closed',()=>{
 const s=structuredClone(schema);s.additionalProperties={type:'integer'};
 assert.throws(()=>validateSchema({...original[0].record,newProperty:'not integer'},s),/SCHEMA_VALUE additionalProperties/);
});
test('duplicate objects are compared independent of key order',()=>{
 const r=structuredClone(original[0].record);r.bibliography.identifiers.push({value:'BD02874939',scheme:'NCID'});
 assert.throws(()=>validateSchema(r),/DUPLICATE_ITEM/);
});

test('falsey unsupported schema type and dialect values fail closed',()=>{
 for(const value of [null,'',false,0]) {
  const s=structuredClone(schema);s.properties.access.properties.pdf_pages.type=value;
  const r=structuredClone(original[0].record);r.access.pdf_pages='not a page count';
  assert.throws(()=>validateSchema(r,s),/SCHEMA_TYPE/);
  const d=structuredClone(schema);d.$schema=value;
  assert.throws(()=>validateSchema(original[0].record,d),/SCHEMA_DIALECT/);
 }
});
