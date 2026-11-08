import * as m from '../../../scripts/research-cad.mjs';import{readFileSync,writeFileSync,cpSync,mkdtempSync,rmSync}from'node:fs';import{resolve}from'node:path';import{tmpdir}from'node:os';import{execFileSync}from'node:child_process';
const source=resolve('../castle-stage2a-shallow'),dir=mkdtempSync(resolve(tmpdir(),'independent-shallow-')),rows=[];
function check(name,fn,reject=false){try{fn();rows.push({name,status:reject?'FAIL':'PASS',result:'ACCEPTED'});}catch(e){rows.push({name,status:reject?'PASS':'FAIL',result:e.message});}}
try{cpSync(source,dir,{recursive:true,filter:p=>!p.includes('/dist')&&(!p.includes('/evidence/')||p.includes('/evidence/stage2a/demo')||p.endsWith('/evidence/stage2a'))});
check('actually shallow with BASE absent',()=>{if(execFileSync('git',['-C',dir,'rev-parse','--is-shallow-repository'],{encoding:'utf8'}).trim()!=='true')throw Error('NOT_SHALLOW');try{execFileSync('git',['-C',dir,'cat-file','-e',m.BASE],{stdio:'pipe'});throw Error('BASE_EXISTS');}catch(e){if(e.message==='BASE_EXISTS')throw e;}});
check('BASE bundle equals full Git snapshot',()=>{if(m.canonical(m.snapshot(dir,m.BASE))!==m.canonical(m.snapshot(m.ROOT,m.BASE)))throw Error('SNAPSHOT_DIFF');});
check('fixed original artifacts equal full Git',()=>{if(m.canonical(m.part(dir))!==m.canonical(m.part()))throw Error('PART_DIFF');});
check('HEAD DEC historical pins resolve correctly',()=>m.snapshot(dir,'HEAD'));
check('arbitrary absent ref denied',()=>m.snapshot(dir,'0'.repeat(40)),true);
for(const [name,path,fn]of [['bundle tamper','evidence/stage2a/demo/snapshot.json',()=>m.snapshot(dir,m.BASE)],['baseline tamper','cad/revisions/baseline.json',()=>m.part(dir)],['current CAD tamper','cad/prototype-v1/generated/palisade.FCStd',()=>m.part(dir)],['current catalog tamper','catalog/wooden-palisade-v0.json',()=>m.part(dir)]]){const p=resolve(dir,path),b=readFileSync(p);writeFileSync(p,Buffer.concat([b,Buffer.from(' ')]));check(name,fn,true);writeFileSync(p,b);}
const a=JSON.parse(readFileSync(resolve(dir,'evidence/stage2a/demo/application.json')));check('approved application valid in shallow',()=>m.validateApplication(a,dir));const p=resolve(dir,'sources/records/SRC-9999.json');writeFileSync(p,'{}');check('added source still invalidates approval',()=>m.validateApplication(a,dir),true);rmSync(p);
// Removing shallow marker makes history intentionally incomplete but no longer eligible for fallback.
rmSync(resolve(dir,'.git/shallow'));check('nonshallow absent BASE never uses bundle',()=>m.snapshot(dir,m.BASE),true);
}finally{rmSync(dir,{recursive:true,force:true});}
console.log(JSON.stringify({engine_sha256:m.hash(readFileSync(resolve(m.ROOT,'scripts/research-cad.mjs'))),results:rows},null,2));if(rows.some(r=>r.status!=='PASS'))process.exitCode=1;
